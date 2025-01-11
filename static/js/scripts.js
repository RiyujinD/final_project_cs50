// remove blur on the text in main page
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('blur-text').addEventListener('click', function () {
        this.style.filter = 'none';
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.slider-nav a');
    const slides = document.querySelectorAll('.slider img');
    const slider = document.querySelector('.slider');

    // Smooth scroll to the specific slide when nav links are clicked
    navLinks.forEach((link, i) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            slider.scrollTo({
                left: slides[i].offsetLeft, // Scroll to the slide's left position
                behavior: 'smooth'         // Smooth scrolling effect
            });

            // Update active nav link
            navLinks.forEach((l) => l.classList.remove('active'));
            link.classList.add('active');
        });
    });

    // Update active nav link on scroll
    slider.addEventListener('scroll', () => {
        const index = Math.round(slider.scrollLeft / slider.offsetWidth);
        navLinks.forEach((link, i) => {
            link.classList.toggle('active', i === index);
        });
    });
});