// On the Night/Light toggle wait page load to remove no-animate to change 
document.addEventListener('DOMContentLoaded', () => {

    setTimeout(() => {
        let items = document.querySelectorAll('.nav-item');
        items.forEach(item => {
            item.classList.remove("no-animate");
        });
    }, 3000);
})