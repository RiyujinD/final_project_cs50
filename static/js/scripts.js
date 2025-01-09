// remove blur on the text in main page
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('blur-text').addEventListener('click', function () {
        this.style.filter = 'none';
    });
});