from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Exists, OuterRef, Prefetch
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
import random
import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from .models import Worker, Departament, Test, TestMember, UploadedFile, \
    Question, AnswerOpen, AnswerPair, AnswerVariant, Result, UserAnswer, AttemptQuestion


def get_role(user):
    worker = Worker.objects.get(user=user)
    if worker.role == 'admin':
        return 'admin'
    if worker.role == 'curator':
        return 'curator'
    if worker.role == 'worker':
        return 'worker'


def get_question_type(question):
    if question.question_type == 'choose_one':
        return 'variants'
    if question.question_type == 'pairs':
        return 'pairs'
    if question.question_type == 'open_answer':
        return 'open'


@login_required(login_url='login')
def form_protocol_file(request, test_id, result_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)
    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    result = Result.objects.get(id=result_id)
    attempt_questions = AttemptQuestion.objects.filter(result=result).values_list('question', flat=True)
    test_questions = Question.objects.filter(id__in=attempt_questions, test__id=test_id)
    if not test_questions.exists():  # old tests compatibility
        test_questions = Question.objects.filter(test=test)
    variants = AnswerVariant.objects.filter(question__test=test, is_correct=True)
    pairs = AnswerPair.objects.filter(question__test=test)
    open_answer = AnswerOpen.objects.filter(question__test=test)
    test_questions = test_questions.prefetch_related(
        Prefetch('answervariant_set', queryset=variants, to_attr='variants')
    )
    test_questions = test_questions.prefetch_related(
        Prefetch('answerpair_set', queryset=pairs, to_attr='pairs')
    )
    test_questions = test_questions.prefetch_related(
        Prefetch('answeropen_set', queryset=open_answer, to_attr='open_answer')
    )
    user_answers = UserAnswer.objects.filter(question__test=test, result=result)
    max_score = len(test_questions)

    buffer = io.BytesIO()
    time_spent = result.finish_date - result.start_date
    result_score = int(result.result) if round(result.result, 5) == int(result.result) \
        else round(result.result, 5)
    header = f'''Тестируемый: {user_answers[0].result.worker.full_name}
Подразделение: {user_answers[0].result.worker.departament}
Тест: {test_questions[0].test.test_name}
Набрано баллов: {result_score}
Максимум баллов: {max_score}
Дата прохождения: {result.finish_date.day}.{result.finish_date.month}.{result.finish_date.year}
Тест пройден: {'Да' if result.is_passed else 'Нет'}
Затраченное время: {time_spent.seconds//3600}:{time_spent.seconds//60%60}:{time_spent.seconds%60}'''

    table = [[header], ['№', 'Текст вопроса', 'Ответ пользователя', 'Правильный ответ', 'Верно']]
    font_path = settings.BASE_DIR / 'static/fonts/DejaVuSerif.ttf'
    pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path))
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'DejaVuSerif'
    styles['Normal'].fontSize = 8
    for i, question in enumerate(test_questions):
        question_type = get_question_type(question)
        row = list()
        row.append(i+1)

        user_answer_cell = ''
        correct_answer_cell = ''
        if question_type == 'pairs':
            pairs = AnswerPair.objects.filter(question=question)
            for pair in pairs.order_by('left_part'):
                correct_answer_cell += f'{pair.left_part} - {pair.right_part};\n'
            for answer in user_answers.filter(question=question).order_by('left_part'):
                user_answer_cell += f'{answer.left_part} - {answer.right_part};\n'
        elif question_type == 'variants':
            correct_answer = AnswerVariant.objects.filter(question=question, is_correct=True)
            correct_answer_cell += correct_answer[0].answer_text
            user_answer_obj = user_answers.filter(question=question)
            if user_answer_obj:
                user_answer_cell += f'{user_answer_obj[0].simple_answer}'
            else:
                user_answer_cell += '-'
        elif question_type == 'open':
            open_answer = AnswerOpen.objects.filter(question=question)
            correct_answer_cell += open_answer[0].correct_answer
            user_answer_obj = user_answers.filter(question=question)
            if user_answer_obj:
                user_answer_cell += f'{user_answer_obj[0].simple_answer}'
            else:
                user_answer_cell += '-'

        row.append(Paragraph(question.question_text, styles['Normal']))
        row.append(Paragraph(user_answer_cell, styles['Normal']))
        row.append(Paragraph(correct_answer_cell, styles['Normal']))
        row.append('Да' if user_answer_cell.lower() == correct_answer_cell.lower() else 'Нет')
        table.append(tuple(row))

    pdf_file = SimpleDocTemplate(buffer, pagesize=A4,
                                 rightMargin=40, leftMargin=40, topMargin=20, bottomMargin=40)
    table = Table(table, colWidths=[30, 150, 160, 160, 40])
    style = TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (1, 1), (-1, -1), 8),
    ])
    table.setStyle(style)
    elements = [table]
    pdf_file.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = \
        f'attachment; filename="protocol_{result.test.id}_{result.worker.id}.pdf"'
    return response


def index(request):
    return render(request, 'index.html')


@login_required(login_url='login')
def tests_view(request):
    worker = Worker.objects.get(user=request.user)
    role = get_role(request.user)
    if role == 'admin':
        tests = Test.objects.all().order_by('test_name')
    else:
        test_members = TestMember.objects.filter(test=OuterRef('pk'), worker=worker)
        tests = Test.objects.annotate(user_is_participating=Exists(test_members))
        tests = tests.filter(user_is_participating=True)
        tests = tests.order_by('test_name')
        if role == 'curator':
            tests = list(set(list(tests) + list(Test.objects.filter(curator=worker))))
    return render(request, 'testing.html', {
        'tests': tests,
    })


@login_required(login_url='login')
def test_detailed(request, test_id):
    worker = Worker.objects.get(user=request.user)
    test_members = TestMember.objects.filter(test__id=test_id)
    test_members = [i.worker for i in test_members]
    test = Test.objects.get(id=test_id)
    results = Result.objects.filter(test=test, worker=worker)
    role = get_role(request.user)
    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    elif worker in test_members:
        pass
    else:
        return render(request, '403.html', {
            'messages': ['Вы не участвуете в данном тестировании']
        })
    questions = Question.objects.filter(test=test)
    return render(request, 'test_detailed.html', {
        'test': test,
        'questions': questions,
        'results': results,
    })


@login_required(login_url='login')
def protocols_view(request):
    worker = Worker.objects.get(user=request.user)
    role = get_role(request.user)
    if role in ['admin']:
        tests = Test.objects.all()
    elif role in ['curator']:
        tests = Test.objects.filter(curator=worker)
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    if not tests:
        return render(request, 'protocols.html', {
            'tests': tests,
            'messages': ['Вы не являетесь куратором ни одного теста'],
        })
    tests = tests.order_by('test_name')
    return render(request, 'protocols.html', {
        'tests': tests,
    })


@login_required(login_url='login')
def test_protocols_view(request, test_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    protocols = Result.objects.filter(test__id=test_id)
    protocols = protocols.order_by('worker__full_name')
    for protocol in protocols:
        protocol.result = int(protocol.result) if round(protocol.result, 5) ==\
                                                  int(protocol.result) else round(protocol.result, 5)
    return render(request, 'test_protocols.html', {
        'protocols': protocols,
    })


@login_required(login_url='login')
def test_attempts(request, test_id):
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)
    results = Result.objects.filter(test=test, worker=worker, finish_date__isnull=False)
    if not results.exists():
        return render(request, '403.html', {'messages': ['Вы не участвуете в данном тестировании']})

    results = results.order_by('test__test_name')
    for result in results:
        result.result = int(result.result) if round(result.result, 5) ==\
                                                  int(result.result) else round(result.result, 5)
    return render(request, 'test_attempts.html', {
        'results': results,
    })


@login_required(login_url='login')
def worker_protocol(request, test_id, result_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    result = Result.objects.get(id=result_id)
    attempt_questions = AttemptQuestion.objects.filter(result=result).values_list('question', flat=True)
    test_questions = Question.objects.filter(id__in=attempt_questions, test__id=test_id)
    if not test_questions.exists():  # old tests compatibility
        test_questions = Question.objects.filter(test__id=test_id)
    variants = AnswerVariant.objects.filter(question__test__id=test_id, is_correct=True)
    pairs = AnswerPair.objects.filter(question__test__id=test_id).order_by('left_part')
    open_answer = AnswerOpen.objects.filter(question__test__id=test_id)
    test_questions = test_questions.prefetch_related(
        Prefetch('answervariant_set', queryset=variants, to_attr='variants')
    )
    test_questions = test_questions.prefetch_related(
        Prefetch('answerpair_set', queryset=pairs, to_attr='pairs')
    )
    test_questions = test_questions.prefetch_related(
        Prefetch('answeropen_set', queryset=open_answer, to_attr='open_answer')
    )
    user_answers = UserAnswer.objects.filter(question__test=test, result=result)
    user_answers = user_answers.order_by('left_part')

    time_spent = result.finish_date - result.start_date
    return render(request, 'worker_protocol.html', {
        'test': test,
        'result': result,
        'time_spent': f'{time_spent.seconds // 3600}:'
                      f'{time_spent.seconds // 60 % 60}:{time_spent.seconds % 60}',
        'score': int(result.result) if round(result.result, 5) == int(result.result)
        else round(result.result, 5),
        'max_score': len(test_questions),
        'questions': test_questions,
        'user_answers': user_answers,
    })


@login_required(login_url='login')
def start_test(request, test_id):
    worker = Worker.objects.get(user=request.user)
    user_is_participating = TestMember.objects.filter(test__id=test_id, worker=worker).exists()
    if not user_is_participating:
        return render(request, '403.html', {
            'messages': ['Вы не участвуете в данном тестировании']
        })

    result = Result.objects.filter(worker=worker, test__id=test_id)
    test = Test.objects.get(id=test_id)
    test_questions = list(Question.objects.filter(test=test))
    random.shuffle(test_questions)
    test_questions = test_questions[:test.questions_per_attempt]

    current_time = datetime.datetime.now(datetime.timezone.utc)
    if result.exists():
        if result.last().finish_date:
            if len(result) >= test.max_tries:
                return redirect('test_attempts', test_id=test_id)
            else:
                new_result_obj = Result(test=test, worker=worker, start_date=current_time)
                new_result_obj.save()
                for test_question in test_questions:
                    attempt_question = AttemptQuestion(result=new_result_obj, question=test_question)
                    attempt_question.save()
        else:  # redirect to last answered question
            attempt_questions = AttemptQuestion.objects.filter(result=result.last())
            user_answers = UserAnswer.objects.filter(
                result=result.last()
            ).values_list('question')  # get questions ids for the test
            last_question = attempt_questions[len(set(user_answers))]
            return redirect('question', test_id=test_id, question_id=last_question.question.id)

    if not result.exists():
        new_result_obj = Result(test=test, worker=worker, start_date=current_time)
        new_result_obj.save()
        for test_question in test_questions:
            attempt_question = AttemptQuestion(result=new_result_obj, question=test_question)
            attempt_question.save()
    return redirect('question', test_id=test_id, question_id=test_questions[0].id)


@login_required(login_url='login')
def practice_start(request, test_id):
    worker = Worker.objects.get(user=request.user)
    role = get_role(request.user)
    user_is_participating = TestMember.objects.filter(test__id=test_id, worker=worker).exists()
    if role in ['admin']:
        pass
    elif not user_is_participating:
        return render(request, '403.html', {
            'messages': ['Вы не участвуете в данном тестировании']
        })
    test = Test.objects.get(id=test_id)
    first_question = Question.objects.filter(test=test).first()
    return redirect('practice_question', test_id=test_id, question_id=first_question.id)


@login_required(login_url='login')
def question_view(request, test_id, question_id):
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)
    results = Result.objects.filter(worker=worker, test=test)
    current_result = results.last()

    if not results.exists():
        return render(request, '403.html', {
            'messages': ['Вы не участвуете в данном тестировании']
        })

    if results.exists():
        if current_result.finish_date:
            return render(request, '403.html', {
                'messages': ['Вы уже прошли данный тест']
            })

    def fill_answer(q, a=None, left=None, right=None):
        if a:
            user_answer_obj, created = UserAnswer.objects.get_or_create(
                result=current_result,
                question=q,
                left_part=None,
                right_part=None
            )
            user_answer_obj.simple_answer = a
            user_answer_obj.save()
        elif left:
            user_answer_obj, created = UserAnswer.objects.get_or_create(
                result=current_result,
                question=q,
                simple_answer=None,
                left_part=left
            )
            user_answer_obj.right_part = right
            user_answer_obj.save()

    try:
        question = AttemptQuestion.objects.get(question__id=question_id, result=current_result).question
    except:
        return render(request, '403.html', {
            'messages': ['Такой объект не существует']
        })
    media_files = UploadedFile.objects.filter(question=question)
    start_time = current_result.start_date
    start_time = start_time
    test_time_limit = datetime.timedelta(minutes=test.time_limit)
    end_before = start_time + test_time_limit
    end_before_unix = int(end_before.timestamp() * 1000)

    time_now = datetime.datetime.now(datetime.timezone.utc)

    if time_now > end_before:
        user_result = Result.objects.get(worker=worker, test=test)
        user_result.finish_date = time_now
        user_result.save()
        return redirect('test_result', test_id=test_id)

    variants = AnswerVariant.objects.filter(question=question)
    pairs = AnswerPair.objects.filter(question=question)
    open_answer = AnswerOpen.objects.filter(question=question)

    right_parts = list(set([i.right_part for i in pairs])) if pairs else None
    answers = list(variants) + list(pairs) + list(open_answer)
    random.shuffle(right_parts) if right_parts else None
    random.shuffle(answers)

    if request.method == 'POST':
        question_type = get_question_type(question)
        if question_type == 'variants':
            answer_value = int(request.POST['user-answer'])
            answers_ids = [i.id for i in answers]
            answer_index = answers_ids.index(answer_value)
            user_answer = answers[answer_index].answer_text
            fill_answer(q=question, a=user_answer)

        if question_type == 'pairs':
            for i in list(request.POST)[1:]:
                left_part = AnswerPair.objects.get(id=int(i)).left_part
                right_part = request.POST[i]
                fill_answer(q=question, left=left_part, right=right_part)

        if question_type == 'open':
            answer_value = request.POST['user-answer']
            fill_answer(q=question, a=answer_value)

        questions = AttemptQuestion.objects.filter(result=current_result)
        questions_id_list = [i.question.id for i in questions]
        try:
            index_of_next_question = questions_id_list.index(question.id) + 1
            return redirect('question',
                            test_id=test_id,
                            question_id=questions[index_of_next_question].question.id)
        except IndexError:
            return redirect('test_result', test_id=test_id, result_id=current_result.id)

    return render(request, 'question.html', {
        'question': question,
        'answers': answers,
        'right_parts': right_parts,
        'end_before': end_before_unix,
        'media_files': media_files,
    })


@csrf_protect
@login_required(login_url='login')
def practice_question_view(request, test_id, question_id):
    worker = Worker.objects.get(user=request.user)
    user_is_participating = TestMember.objects.filter(test__id=test_id, worker=worker).exists()
    role = get_role(request.user)
    if role in ['admin']:
        pass
    elif not user_is_participating:
        return render(request, '403.html', {
            'messages': ['Вы не участвуете в данном тестировании']
        })

    test = Test.objects.get(id=test_id)
    question = Question.objects.get(id=question_id)
    media_files = UploadedFile.objects.filter(question=question)
    question_types = Question.question_types

    variants = AnswerVariant.objects.filter(question=question)
    pairs = AnswerPair.objects.filter(question=question)
    open_answer = AnswerOpen.objects.filter(question=question)

    right_parts = [i.right_part for i in pairs] if pairs else None
    answers = list(variants) + list(pairs) + list(open_answer)
    random.shuffle(right_parts) if right_parts else None
    random.shuffle(answers)

    questions = Question.objects.filter(test=test)[:5]
    questions_id_list = [i.id for i in questions]
    if question_id not in questions_id_list:
        return render(request, '403.html', {
            'messages': ['Такой объект не существует']
        })
    if request.method == 'POST':
        try:
            index_of_next_question = questions_id_list.index(question_id) + 1
            return redirect('practice_question',
                            test_id=test_id, question_id=questions[index_of_next_question].id)
        except IndexError:
            return redirect('test', test_id=test_id)

    return render(request, 'practice_question.html', {
        'question': question,
        'answers': answers,
        'question_types': question_types,
        'right_parts': right_parts,
        'media_files': media_files,
    })


@csrf_protect
@login_required(login_url='login')
def question_edit_view(request, test_id, question_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    question = Question.objects.get(id=question_id)
    question_type = get_question_type(question)
    media_files = UploadedFile.objects.filter(question=question)

    variants = AnswerVariant.objects.filter(question=question)
    pairs = AnswerPair.objects.filter(question=question)
    open_answer = AnswerOpen.objects.filter(question=question)

    answers = list(variants) + list(pairs) + list(open_answer)

    if request.method == 'POST':
        form_dict = dict(request.POST)
        question_text = form_dict['question-text'][0]

        if question_text == '':
            return render(request, 'question_edit.html', {
                'question': question,
                'answers': answers,
                'media_files': media_files,
                'messages': ['Не указан текст вопроса'],
            })
        question.question_text = question_text
        question.save()

        uploaded_files = request.FILES.getlist('file')
        if uploaded_files:
            for media_file in uploaded_files:
                if media_file.content_type in ['image/png', 'image/jpeg', 'image/gif', 'image/webp']:
                    new_file = UploadedFile(question=question, file_type='img', file=media_file)
                    new_file.save()
                elif 'video' in media_file.content_type:
                    new_file = UploadedFile(question=question, file_type='mp4', file=media_file)
                    new_file.save()
                elif 'audio' in media_file.content_type:
                    new_file = UploadedFile(question=question, file_type='mp3', file=media_file)
                    new_file.save()
                else:
                    return render(request, 'question_edit.html', {
                        'question': question,
                        'question_type': question_type,
                        'answers': answers,
                        'media_files': media_files,
                        'messages': ['Ошибка при загрузке файла. Неправильный формат файла.'],
                    })

        if question_type == 'variants':
            correct_question_id = int(*form_dict['correct'])
            answers_id = []
            for key in form_dict.keys():
                if 'answer' in key:
                    answers_id.append(int(key[7:]))

            for answer in variants:
                answer.answer_text = form_dict[f'answer-{answer.id}'][0]
                answer.is_correct = True if correct_question_id == answer.id else False
                answer.save()

        elif question_type == 'pairs':
            lefts = []
            rights = []
            for key in form_dict.keys():
                if 'left' in key:
                    lefts.append(form_dict[key][0])
                elif 'right' in key:
                    rights.append(form_dict[key][0])

            for i in pairs:
                i.delete()

            for left, right in zip(lefts, rights):
                new_pair_obj = AnswerPair(
                    question=question,
                    left_part=left,
                    right_part=right
                )
                new_pair_obj.save()

        elif question_type == 'open':
            correct_answer = form_dict['open'][0]
            open_answer[0].correct_answer = correct_answer
            open_answer[0].save()

        return redirect('test', test_id=test_id)
    return render(request, 'question_edit.html', {
        'question': question,
        'answers': answers,
        'media_files': media_files,
    })


@csrf_protect
@login_required(login_url='login')
def delete_question(request, test_id, question_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    question_to_delete = Question.objects.get(id=question_id)

    if request.method == 'POST':
        if request.POST['confirm'] == 'yes':
            question_to_delete.delete()
        return redirect('test', test_id=test_id)
    return render(request, 'delete_confirmation.html', {'object': question_to_delete.question_text})


@login_required(login_url='login')
def delete_test_view(request, test_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    if request.method == 'POST':
        if request.POST['confirm'] == 'yes':
            test.delete()
            return redirect('testing')
        elif request.POST['confirm'] == 'no':
            return redirect('test', test_id=test_id)
    return render(request, 'delete_confirmation.html', {'object': test.test_name})


@login_required(login_url='login')
def delete_file(request, file_id):
    role = get_role(user=request.user)
    worker = Worker.objects.get(user=request.user)
    file_to_delete = UploadedFile.objects.get(id=file_id)
    test = file_to_delete.question.test

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    if request.method == 'POST':
        if request.POST['confirm'] == 'yes':
            file_to_delete.delete()
            return redirect('edit_question', test_id=test.id, question_id=file_to_delete.question.id)
        elif request.POST['confirm'] == 'no':
            return redirect('edit_question', test_id=test.id, question_id=file_to_delete.question.id)
    return render(request, 'delete_confirmation.html', {'object': file_to_delete.file})


@csrf_protect
@login_required(login_url='login')
def new_question_view(request, test_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    question_types = Question.question_types

    if request.method == 'POST':
        form_dict = dict(request.POST)
        question_text = form_dict['question-text'][0]
        question_type = form_dict['question-type'][0]

        if question_text == '':
            return render(request, 'new_question.html', {
                'question_types': question_types,
                'messages': ['Не указан текст вопроса'],
            })
        if question_type == '':
            return render(request, 'new_question.html', {
                'question_types': question_types,
                'messages': ['Не выбран тип вопроса'],
            })

        new_question_obj = Question(
            test=test,
            question_type=question_type,
            question_text=question_text
        )
        new_question_obj.save()

        uploaded_files = request.FILES.getlist('file')
        if uploaded_files:
            for media_file in uploaded_files:
                if media_file.content_type in ['image/png', 'image/jpeg', 'image/gif', 'image/webp']:
                    new_file = UploadedFile(question=new_question_obj, file_type='img', file=media_file)
                    new_file.save()
                elif 'video' in media_file.content_type:
                    new_file = UploadedFile(question=new_question_obj, file_type='mp4', file=media_file)
                    new_file.save()
                elif 'audio' in media_file.content_type:
                    new_file = UploadedFile(question=new_question_obj, file_type='mp3', file=media_file)
                    new_file.save()
                else:
                    return render(request, 'new_question.html', {
                        'question_types': question_types,
                        'messages': ['Ошибка при загрузке файлов'],
                    })

        question_type = get_question_type(new_question_obj)

        if question_type == 'variants':
            correct_question_i = int(*form_dict['correct'])

            answer_keys = []
            for key in form_dict.keys():
                if 'answer' in key:
                    answer_keys.append(key)

            for i, answer in enumerate(answer_keys):
                if form_dict[answer][0] == '':
                    return render(request, 'new_question.html', {
                        'test': test,
                        'question_types': question_types,
                        'messages': ['Пустые поля недопустимы'],
                    })
                new_answer_obj = AnswerVariant(
                    question=new_question_obj,
                    answer_text=form_dict[answer][0],
                    is_correct=True if i == correct_question_i-1 else False
                )
                new_answer_obj.save()

        elif question_type == 'pairs':
            lefts = []
            for key in form_dict.keys():
                if 'left' in key:
                    lefts.append(form_dict[key][0])

            rights = []
            for key in form_dict.keys():
                if 'right' in key:
                    rights.append(form_dict[key][0])

            for left, right in zip(lefts, rights):
                if left == '' or right == '':
                    return render(request, 'new_question.html', {
                        'test': test,
                        'question_types': question_types,
                        'messages': ['Пустые поля недопустимы'],
                    })

                new_pair_obj = AnswerPair(
                    question=new_question_obj,
                    left_part=left,
                    right_part=right
                )
                new_pair_obj.save()

        elif question_type == 'open':
            correct_answer = form_dict['open'][0]
            if correct_answer == '':
                return render(request, 'new_question.html', {
                    'question_types': question_types,
                    'test': test,
                    'messages': ['Пустые поля недопустимы'],
                })

            new_open_obj = AnswerOpen(
                question=new_question_obj,
                correct_answer=correct_answer.strip(),
            )
            new_open_obj.save()

        return redirect('test', test_id=test_id)

    return render(request, 'new_question.html', {
        'test': test,
        'question_types': question_types,
    })


@login_required(login_url='login')
def test_result(request, test_id, result_id):
    test_score = 0
    max_score = 0
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)
    user_results = Result.objects.filter(worker=worker, test=test)
    if not user_results.exists():
        return render(request, '403.html', {'messages': ['Вы не участвуете в данном тестировании']})
    curator = test.curator
    current_result = Result.objects.get(id=result_id)
    attempt_questions = AttemptQuestion.objects.filter(result=current_result).values_list('question', flat=True)
    test_questions = Question.objects.filter(id__in=attempt_questions, test__id=test_id)
    if not test_questions.exists():  # old tests compatibility
        test_questions = Question.objects.filter(test=test)
    variants = AnswerVariant.objects.filter(question__test=test, is_correct=True)
    pairs = AnswerPair.objects.filter(question__test=test).order_by('left_part')
    open_answer = AnswerOpen.objects.filter(question__test=test)
    test_questions = test_questions.prefetch_related(
        Prefetch('answervariant_set', queryset=variants, to_attr='variants')
    )
    test_questions = test_questions.prefetch_related(
        Prefetch('answerpair_set', queryset=pairs, to_attr='pairs')
    )
    test_questions = test_questions.prefetch_related(
        Prefetch('answeropen_set', queryset=open_answer, to_attr='open_answer')
    )

    user_answers = UserAnswer.objects.filter(question__test=test, result=current_result)
    user_answers = user_answers.order_by('left_part')

    for question in test_questions:
        max_score += 1
        question_type = get_question_type(question)
        answers_to_question = user_answers.filter(question=question)

        for answer in answers_to_question:
            if question_type == 'variants':
                if answer.simple_answer == question.variants[0].answer_text:
                    test_score += 1
            elif question_type == 'pairs':
                for pair in question.pairs:
                    if pair.left_part == answer.left_part:
                        if pair.right_part == answer.right_part:
                            test_score += round(1 / len(question.pairs), 2)
            elif question_type == 'open':
                if answer.simple_answer.lower() == question.open_answer[0].correct_answer.lower():
                    test_score += 1

    test_score = int(test_score) if round(test_score, 5) == int(test_score) else round(test_score, 5)
    current_result.result = test_score
    test_is_passed = True if (test_score / max_score * 100) >= test.percentage_to_pass else False
    if test_is_passed:
        current_result.is_passed = True
        current_result.save()

    if not current_result.finish_date:
        send_mail(
            f'Тестируемый {worker.full_name} закончил тест.',
            f'Набрано {test_score} из {max_score} \n'
            f'http:///127.0.0.1:8000/testing/{test_id}',
            recipient_list=[curator.user.email],
            fail_silently=False,
            from_email=None
        )
        current_result.finish_date = datetime.datetime.now(datetime.timezone.utc)
    current_result.save()
    time_spent = current_result.finish_date - current_result.start_date

    return render(request, 'test_result.html', {
        'result': current_result,
        'test': test,
        'time_spent': f'{time_spent.seconds//3600}:{time_spent.seconds//60%60}:{time_spent.seconds%60}',
        'score': test_score,
        'max_score': max_score,
        'questions': test_questions,
        'user_answers': user_answers,
    })


@login_required(login_url='login')
def reports(request):
    role = get_role(request.user)
    if role not in ['admin', 'curator']:
        return render(request, '403.html')
    return render(request, 'reports.html')


@csrf_protect
@login_required(login_url='login')
def new_test_view(request):
    role = get_role(request.user)
    if role not in ['admin', 'curator']:
        return render(request, '403.html')

    if request.method == 'POST':
        test_name = request.POST.get('test-name')
        uploaded_file = request.FILES.get('file')
        if not test_name and not uploaded_file:
            return render(request, 'new_test.html', {'messages': ['Пустые поля недопустимы']})

        if test_name:
            test_description = request.POST.get('test-description')
            percentage_to_pass = request.POST.get('percentage-to-pass')
            time_limit = request.POST.get('time-limit')
            max_tries = request.POST.get('max-attempts')
            questions_per_attempt = request.POST.get('questions-per-attempt')

            try:
                if percentage_to_pass != '':
                    percentage_to_pass = int(percentage_to_pass)
                    if percentage_to_pass > 100:
                        return render(request, 'new_test.html', {'messages': ['Максимум 100%']})
                else:
                    percentage_to_pass = Test._meta.get_field('percentage_to_pass').default
            except ValueError:
                return render(request, 'new_test.html', {'messages': ['Неверный формат полей']})

            try:
                if time_limit != '':
                    time_limit = int(time_limit)
                    if time_limit < 1:
                        return render(request, 'new_test.html', {'messages': ['Время > 0']})
                else:
                    time_limit = Test._meta.get_field('time_limit').default
            except ValueError:
                return render(request, 'new_test.html', {'messages': ['Неверный формат полей']})

            try:
                if max_tries != '':
                    max_tries = int(max_tries)
                    if max_tries < 1:
                        return render(request, 'new_test.html', {'messages': ['Попыток > 0']})
                else:
                    max_tries = Test._meta.get_field('max_tries').default
            except ValueError:
                return render(request, 'new_test.html', {'messages': ['Неверный формат полей']})

            try:
                if questions_per_attempt != '':
                    questions_per_attempt = int(questions_per_attempt)
                    if questions_per_attempt < 1:
                        return render(request, 'new_test.html', {'messages': ['Вопросов > 0']})
                else:
                    questions_per_attempt = Test._meta.get_field('questions_per_attempt').default
            except ValueError:
                return render(request, 'new_test.html', {'messages': ['Неверный формат полей']})

            curator = Worker.objects.get(user=request.user)
            new_test = Test(
                test_name=test_name,
                test_description=test_description,
                curator=curator,
                time_limit=time_limit,
                percentage_to_pass=percentage_to_pass,
                max_tries=max_tries,
                questions_per_attempt=questions_per_attempt,
            )
            new_test.save()
            new_test_member = TestMember(test=new_test, worker=curator)
            new_test_member.save()
            return redirect('new_question', test_id=new_test.id)
        elif uploaded_file:
            if uploaded_file.content_type == 'text/csv':
                try:
                    file_data = uploaded_file.read().decode('cp1251').splitlines()
                    headers = file_data[1].split(';')
                    test_name = headers[0]
                    test_description = headers[1]
                    time_limit = headers[2]
                    percentage_to_pass = headers[3]
                    max_tries = headers[4]
                    questions_per_attempt = headers[5]

                    curator = Worker.objects.get(user=request.user)
                    new_test = Test(
                        test_name=test_name,
                        test_description=test_description,
                        curator=curator,
                        percentage_to_pass=percentage_to_pass,
                        time_limit=time_limit,
                        max_tries=max_tries,
                        questions_per_attempt=questions_per_attempt
                    )
                    new_test.save()
                    new_test_member = TestMember(test=new_test, worker=curator)
                    new_test_member.save()
                    for row in file_data[3:]:
                        cells = row.split(';')
                        new_question = Question(
                            test=new_test,
                            question_type='choose_one',
                            question_text=cells[1],
                        )
                        new_question.save()
                        correct_answer = cells[-1]
                        for answer in cells[2:6]:
                            new_variant = AnswerVariant(
                                question=new_question,
                                answer_text=answer,
                                is_correct=True if answer == correct_answer else False,
                            )
                            new_variant.save()
                    return redirect('test', test_id=new_test.id)
                except:
                    return render(request, 'new_test.html', {'messages': ["Ошибка при загрузке файла"]})
            else:
                return render(request, 'new_test.html', {'messages': ["Ошибка при загрузке файла"]})
    else:
        return render(request, 'new_test.html')

    return render(request, 'new_test.html')


@csrf_protect
@login_required(login_url='login')
def test_edit_view(request, test_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html')

    if request.method == 'POST':
        test_name = request.POST.get('test-name')
        test_description = request.POST.get('test-description')
        time_limit = request.POST.get('time-limit')
        percentage_to_pass = request.POST.get('percentage-to-pass')
        max_tries = request.POST.get('max-attempts')
        questions_per_attempt = request.POST.get('questions-per-attempt')
        if test_name == '':
            return render(request, 'test_edit.html', {
                'test': test,
                'messages': ['Название теста не может быть пустым'],
            })
        if time_limit == '':
            return render(request, 'test_edit.html', {
                'test': test,
                'messages': ['Укажите лимит на прохождение теста в минутах'],
            })
        if percentage_to_pass == '':
            return render(request, 'test_edit.html', {
                'test': test,
                'messages': ['Укажите необходимый процент правильных ответов для прохождения теста'],
            })
        if max_tries == '':
            return render(request, 'test_edit.html', {
                'test': test,
                'messages': ['Укажите количество попыток на тест'],
            })
        if questions_per_attempt == '':
            return render(request, 'test_edit.html', {
                'test': test,
                'messages': ['Укажите количество вопросов в тесте'],
            })

        try:
            time_limit = int(request.POST.get('time-limit'))
            percentage_to_pass = int(request.POST.get('percentage-to-pass'))
            max_tries = int(request.POST.get('max-attempts'))
            questions_per_attempt = int(request.POST.get('questions-per-attempt'))
        except ValueError:
            return render(request, 'test_edit.html', {
                'test': test,
                'messages': ['Неверный формат полей'],
            })
        if time_limit < 1:
            return render(request, 'test_edit.html', {
                'test': test, 'messages': ['Время > 0']})
        if percentage_to_pass > 100:
            return render(request, 'test_edit.html', {
                'test': test, 'messages': ['Правильных вопросов <= 100']})
        if max_tries < 1:
            return render(request, 'test_edit.html', {
                'test': test, 'messages': ['Попыток > 0']})
        if questions_per_attempt < 1:
            return render(request, 'test_edit.html', {
                'test': test, 'messages': ['Вопросов > 0']})

        test.test_name = test_name
        test.test_description = test_description
        test.time_limit = time_limit
        test.percentage_to_pass = percentage_to_pass
        test.max_tries = max_tries
        test.questions_per_attempt = questions_per_attempt
        test.save()
        return redirect('test', test_id=test.id)
    return render(request, 'test_edit.html', {
        'test': test,
    })


@csrf_protect
@login_required(login_url='login')
def test_members_view(request, test_id):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    test = Test.objects.get(id=test_id)

    if role in ['admin']:
        pass
    elif role in ['curator'] and test.curator == worker:
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    departments = Departament.objects.all()
    test_members = TestMember.objects.filter(worker=OuterRef('pk'), test=test)
    workers = Worker.objects.annotate(
        is_test_member=Exists(test_members)
    )

    if request.method == 'POST':
        action = request.POST['action']
        worker_id = request.POST['worker_id']
        worker_to_change = Worker.objects.get(id=worker_id)

        if action == 'add':
            new_member, created = TestMember.objects.get_or_create(worker=worker_to_change, test=test)
            new_member.save()
            send_mail(
                'Вам необходимо пройти новый тест',
                'Перейдите по следующей ссылке, чтобы попасть на страницу теста:'
                f'http:///127.0.0.1:8000/testing/{test_id}',
                recipient_list=[worker_to_change.user.email],
                fail_silently=False,
                from_email=None
            )

        elif action == 'remove':
            existing_member, created = TestMember.objects.get_or_create(worker=worker_to_change, test=test)
            existing_member.delete()

    if request.method == 'GET':
        if 'name' in request.GET.keys():
            name = request.GET['name']
            departament = request.GET['departament']
            job_title = request.GET['job_title']
            filtered_workers = []
            if departament:
                workers = workers.filter(departament__id=int(departament))
            if job_title:
                for worker in workers:
                    if job_title.lower() in worker.job_title.lower():
                        filtered_workers.append(worker)
                workers = filtered_workers
            filtered_workers = []
            if name:
                for worker in workers:
                    if name.lower() in worker.full_name.lower():
                        filtered_workers.append(worker)
                workers = filtered_workers
    workers = sorted(workers, key=lambda x: x.full_name)
    return render(request, 'test_members.html', {
        'test': test,
        'workers': workers,
        'departments': departments,
    })


@login_required(login_url='login')
def analysis_view(request):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    departments = Departament.objects.all().order_by('departament_name')
    if role in ['admin']:
        tests = Test.objects.all()
        pass
    elif role in ['curator']:
        tests = Test.objects.filter(curator=worker)
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})
    tests = tests.order_by('test_name')
    if not tests.exists():
        return render(request, 'analysis_page.html', {
            'tests': tests,
            'departments': departments,
            'messages': ['Вы не являетесь куратором ни одного теста'],
        })
    chosen_test = tests[0]
    results = []
    avg_scores = []

    if request.method == 'GET':
        if 'test' in request.GET.keys():
            chosen_test_id = request.GET['test']
            chosen_departament_id = request.GET['departament']
            start_date = request.GET['start-date']
            end_date = request.GET['end-date']
            chosen_test = Test.objects.get(id=chosen_test_id)

            if role in ['admin']:
                pass
            elif worker != chosen_test.curator:
                return render(request, '403.html', {'messages': ['В доступе отказано']})

            if chosen_departament_id != '':
                results = Result.objects.filter(
                    test=chosen_test,
                    worker__departament__id=chosen_departament_id)
                results = results.filter(finish_date__gt=start_date) if start_date != '' else results
                results = results.filter(finish_date__lt=end_date) if end_date != '' else results
                results = results.order_by('worker__full_name', '-result')

                workers = []
                result_w_max_score = []
                for i in results:
                    if i.worker not in workers:
                        result_w_max_score.append(i)
                        workers.append(i.worker)
                results = result_w_max_score

            elif chosen_departament_id == '':
                for departament in departments:
                    data = Result.objects.filter(
                        test=chosen_test,
                        worker__departament=departament)
                    data = data.filter(finish_date__gt=start_date) if start_date != '' else data
                    data = data.filter(finish_date__lt=end_date) if end_date != '' else data

                    departament_avg_score = 0
                    for result in data:
                        departament_avg_score += result.result
                    if data:
                        avg_scores.append(departament_avg_score / len(data))
                    else:
                        avg_scores.append(0)
        else:
            for departament in departments:
                data = Result.objects.filter(
                    test=chosen_test,
                    worker__departament=departament)

                departament_avg_score = 0
                for result in data:
                    departament_avg_score += result.result
                if data:
                    avg_scores.append(departament_avg_score / len(data))
                else:
                    avg_scores.append(0)

    worker_scores = [i.result for i in results]
    if avg_scores or worker_scores:
        y_scale_max = max(avg_scores + worker_scores) + 2
    else:
        y_scale_max = 0
    return render(request, 'analysis_page.html', {
        'tests': tests,
        'departments': departments,
        'chosen_test': chosen_test,
        'results': results,
        'avg_scores': avg_scores,
        'y_scale_max': y_scale_max,
    })


@login_required(login_url='login')
def summary_view(request):
    role = get_role(request.user)
    worker = Worker.objects.get(user=request.user)
    departments = Departament.objects.all()
    if role in ['admin']:
        results = Result.objects.filter(finish_date__isnull=False)
        tests = Test.objects.all()
        pass
    elif role in ['curator']:
        results = Result.objects.filter(test__curator=worker, finish_date__isnull=False)
        tests = Test.objects.filter(curator=worker)
        pass
    else:
        return render(request, '403.html', {'messages': ['В доступе отказано']})

    results = results.order_by('worker__full_name')
    if not tests.exists():
        return render(request, 'analysis_page.html', {
            'tests': results,
            'messages': ['Вы не являетесь куратором ни одного теста'],
        })

    for result in results:
        result.result = int(result.result) if round(result.result, 5) == int(result.result) \
            else round(result.result, 5)

    if request.method == 'GET':
        if 'test' in request.GET.keys():
            chosen_test_id = request.GET['test']
            chosen_departament_id = request.GET['departament']
            job_title = request.GET['job_title']
            start_date = request.GET['start-date']
            end_date = request.GET['end-date']
            if chosen_test_id:
                results = results.filter(test__id=chosen_test_id)
            if chosen_departament_id:
                results = results.filter(worker__departament__id=chosen_departament_id)
            if job_title:
                filtered_results = []
                for result in results:
                    if job_title.lower() in result.worker.job_title.lower():
                        filtered_results.append(result)
                results = filtered_results

            results = results.filter(finish_date__gt=start_date) if start_date != '' else results
            results = results.filter(finish_date__lt=end_date) if end_date != '' else results

    return render(request, 'summary.html', {
        'results': results,
        'tests': tests,
        'departments': departments,
    })


@csrf_protect
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('login')
