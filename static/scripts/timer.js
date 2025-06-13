document.addEventListener('DOMContentLoaded', function() {
    const timerContainer = document.getElementById('timer');
    const updateTimer = function() {
        const now = new Date();
        let timeLeftUnix = endBefore - now;
        const minutes = Math.floor(timeLeftUnix / 60000);
        const seconds = Math.round((timeLeftUnix % 60000) / 1000);
        if (minutes >= 0) {
            timerContainer.textContent = `${minutes}:${seconds}`;
        }
        else {
            timerContainer.textContent = '0:0';
        }

    }
    updateTimer();
    setInterval(updateTimer, 1000);
});