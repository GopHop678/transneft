from django.db import models
from django.contrib.auth.models import User


def upload_path(instance, filename):
    test_id = instance.question.test.id
    question_id = instance.question.id
    return f'uploads/{test_id}/{question_id}/{filename}'


class Departament(models.Model):
    departament_name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.departament_name}'


class Worker(models.Model):
    worker_roles = [
        ('admin', 'Администратор'),
        ('curator', 'Куратор'),
        ('worker', 'Сотрудник'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(choices=worker_roles)
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=255, null=True)
    full_name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.full_name} - {self.job_title} - {self.departament}'


class Test(models.Model):
    test_name = models.CharField(max_length=255, null=False)
    test_description = models.CharField(max_length=1000, null=True, blank=True,
                                        default='Описание отсутствует')
    curator = models.ForeignKey(Worker, on_delete=models.CASCADE)
    max_tries = models.IntegerField(null=True, default=2)
    questions_per_attempt = models.IntegerField(null=True, default=10)
    time_limit = models.IntegerField(null=True, default=20)
    percentage_to_pass = models.IntegerField(null=True, default=80)

    def __str__(self):
        return f'{self.test_name}'


class TestMember(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.test} is available to {self.worker}'


class Question(models.Model):
    question_types = [
        ('choose_one', 'Выбрать правильный'),
        ('pairs', 'На соответствие'),
        ('open_answer', 'Открытый вопрос'),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question_type = models.CharField(choices=question_types)
    question_text = models.CharField(max_length=1000, null=False)

    def __str__(self):
        return f'{self.id} {self.question_text[:75]}'


class UploadedFile(models.Model):
    file_types = [
        ('img', 'Фото'),
        ('mp4', 'Видео'),
        ('mp3', 'Аудио'),
    ]

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    file_type = models.CharField(choices=file_types)
    file = models.FileField(upload_to=upload_path)

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.id} {self.question} - {self.file_type}'


class AnswerVariant(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=255, null=False)
    is_correct = models.BooleanField(null=True)

    def __str__(self):
        return f'{self.question}: {self.answer_text}'


class AnswerPair(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    left_part = models.CharField(max_length=255, null=False)
    right_part = models.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.question}: {self.left_part} - {self.right_part}'


class AnswerOpen(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    correct_answer = models.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.question}: {self.correct_answer}'


class Result(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    result = models.FloatField(null=True)
    is_passed = models.BooleanField(null=True, default=False)
    start_date = models.DateTimeField(null=False)
    finish_date = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.id} {self.test} - {self.worker.full_name}'


class AttemptQuestion(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.result} - {self.question}'


class UserAnswer(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    simple_answer = models.CharField(max_length=255, null=True)
    left_part = models.CharField(max_length=255, null=True)
    right_part = models.CharField(max_length=255, null=True)

    # def __str__(self):
    #     return f'{self.question}, {self.worker}'
