document.addEventListener('DOMContentLoaded', function() {
    const selectorField = document.getElementById('question-type-select');
    const answersContainer = document.getElementById('answers-container');
    const constructorContainer = document.getElementById('constructor-container');

    selectorField.addEventListener('change', function() {
        answersContainer.innerHTML = ''; // clear div

        if (!this.value) {
            const existingBtn = document.getElementById('add-variant-btn');
            if (existingBtn) {
                existingBtn.remove();
            }
        }

        if (this.value == 'choose_one') {

            const existingBtn = document.getElementById('add-variant-btn');
            if (existingBtn) {
                existingBtn.remove();
            }

            // add answer button
            const addNewBtn = document.createElement('button');
            addNewBtn.textContent = 'Добавить ответ';
            addNewBtn.id = 'add-variant-btn';
            addNewBtn.addEventListener('click', function() {
                let childrenAmount = 0;
                const children = answersContainer.children;
                for (const child of children) {
                    const elementId = child.id;
                    if (elementId.includes('answer')) {
                        childrenAmount += 1;
                    }
                }
                const labelAnswer = document.createElement('label');
                labelAnswer.textContent = `Ответ ${childrenAmount+1}:`;
                labelAnswer.id = `label-${childrenAmount+1}`;
                labelAnswer.setAttribute('for', `answer-${childrenAmount+1}`);
                const inputAnswer = document.createElement('input');
                inputAnswer.type = 'text';
                inputAnswer.name = `answer-${childrenAmount+1}`;
                inputAnswer.id = `answer-${childrenAmount+1}`;
                inputAnswer.placeholder = `Введите ответ ${childrenAmount+1}`;

                const inputIsCorrect = document.createElement('input');
                inputIsCorrect.type = 'radio';
                inputIsCorrect.name = `correct`;
                inputIsCorrect.value = `${childrenAmount+1}`;
                inputIsCorrect.id = `is-correct-${childrenAmount+1}`;

                answersContainer.appendChild(labelAnswer);
                answersContainer.appendChild(document.createElement('br'));
                answersContainer.appendChild(inputAnswer);
                answersContainer.appendChild(inputIsCorrect);
                answersContainer.appendChild(document.createElement('br'));
            })
            constructorContainer.appendChild(addNewBtn);


            for (let i = 1; i <= 4; i++) {
                // labels
                const labelAnswer = document.createElement('label');
                labelAnswer.textContent = `Ответ ${i}:`;
                labelAnswer.id = `label-${i}`;
                labelAnswer.setAttribute('for', `answer-${i}`);

                // value input
                const inputAnswer = document.createElement('input');
                inputAnswer.type = 'text';
                inputAnswer.name = `answer-${i}`;
                inputAnswer.id = `answer-${i}`;
                inputAnswer.placeholder = `Введите ответ ${i}`;

                // is correct input
                const inputIsCorrect = document.createElement('input');
                inputIsCorrect.type = 'radio';
                inputIsCorrect.name = `correct`;
                inputIsCorrect.value = `${i}`;
                inputIsCorrect.id = `is-correct-${i}`;
                inputIsCorrect.setAttribute('checked', 'checked');

                // add label and input
                answersContainer.appendChild(labelAnswer);
                answersContainer.appendChild(document.createElement('br'));
                answersContainer.appendChild(inputAnswer);
                answersContainer.appendChild(inputIsCorrect);
                answersContainer.appendChild(document.createElement('br'));
            }
        }

        if (this.value == 'pairs') {

            const existingBtn = document.getElementById('add-variant-btn');
            if (existingBtn) {
                existingBtn.remove();
            }

            // add answer button
            const addNewBtn = document.createElement('button');
            addNewBtn.textContent = 'Добавить пару';
            addNewBtn.id = 'add-variant-btn';
            addNewBtn.addEventListener('click', function() {
                let childrenAmount = 0;
                const children = answersContainer.children;
                for (const child of children) {
                    const elementId = child.id;
                    if (elementId.includes('left')) {
                        childrenAmount += 1;
                    }
                }
                const inputLeft = document.createElement('input');
                inputLeft.type = 'text';
                inputLeft.name = `left-${childrenAmount+1}`;
                inputLeft.id = `left-${childrenAmount+1}`;
                inputLeft.placeholder = `Левавя часть ${childrenAmount+1}`;
                const inputRight = document.createElement('input');
                inputRight.type = 'text';
                inputRight.name = `right-${childrenAmount+1}`;
                inputRight.id = `right-${childrenAmount+1}`;
                inputRight.placeholder = `Правая часть ${childrenAmount+1}`;
                answersContainer.appendChild(inputLeft);
                answersContainer.appendChild(inputRight);
                answersContainer.appendChild(document.createElement('br'));
            })
            constructorContainer.appendChild(addNewBtn);

            for (let i = 1; i <= 4; i++) {

                // labels
                // const labelAnswer = document.createElement('label');
                // labelAnswer.textContent = `Ответ ${i}:`;
                // labelAnswer.setAttribute('for', `answer-${i}`);

                // left input
                const inputLeft = document.createElement('input');
                inputLeft.type = 'text';
                inputLeft.name = `left-${i}`;
                inputLeft.id = `left-${i}`;
                inputLeft.placeholder = `Левавя часть ${i}`;

                // right input
                const inputRight = document.createElement('input');
                inputRight.type = 'text';
                inputRight.name = `right-${i}`;
                inputRight.id = `right-${i}`;
                inputRight.placeholder = `Правая часть ${i}`;

                // add label and input
                answersContainer.appendChild(inputLeft);
                answersContainer.appendChild(inputRight);
                answersContainer.appendChild(document.createElement('br'));
            }
        }

        if (this.value == 'open_answer') {

            const existingBtn = document.getElementById('add-variant-btn');
            if (existingBtn) {
                existingBtn.remove();
            }

            // labels
            const labelOpen = document.createElement('label');
            labelOpen.textContent = 'Правильный ответ:';
            labelOpen.setAttribute('for', 'open');

            // value input
            const inputOpen = document.createElement('input');
            inputOpen.type = 'text';
            inputOpen.name = 'open';
            inputOpen.id = 'open';

            // Добавляем label и input в контейнер
            answersContainer.appendChild(labelOpen);
            answersContainer.appendChild(document.createElement('br'));
            answersContainer.appendChild(inputOpen);
            answersContainer.appendChild(document.createElement('br'));
        }
    });
});