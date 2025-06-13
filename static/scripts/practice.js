document.addEventListener('DOMContentLoaded', function() {
    const nextBtn = document.getElementById('next-btn');
    const rightAnswersContainer = document.getElementById('right-answers');
    const showRightAnswer = function() {
        if (nextBtn.type == 'button') {
            event.preventDefault();
            nextBtn.textContent = 'Далее';
            nextBtn.type = 'submit';

            rightAnswers.forEach((answer) => {
                let child = document.createElement('span');
                let br = document.createElement('br');
                if (['choose_one', 'open_answer'].includes(questionType)) {
                    child.textContent += answer;
                }
                else if (questionType == 'pairs') {
                    child.textContent += answer[0];
                    child.textContent += ' - ';
                    child.textContent += answer[1];
                }
                rightAnswersContainer.style.padding = '10px';
                rightAnswersContainer.appendChild(child);
                rightAnswersContainer.appendChild(br);
            });
        }
    }

    nextBtn.addEventListener('click', showRightAnswer);
});