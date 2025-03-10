// Remove blur on the text in Title 
document.addEventListener('DOMContentLoaded', () => {

    // Remove blur on the text in the main page
    document.getElementById('blur_text').addEventListener('click', function () {

        // Store the filter style of element
        const stylesElement = window.getComputedStyle(this);
        const Filter = stylesElement.getPropertyValue('filter');
        const WebkitFilter = stylesElement.getPropertyValue('-webkit-filter');

        // Checking if blur applyed
        const hasBlur = Filter.includes("blur") || WebkitFilter.includes("blur");

        // If blur store the value in the element html
        if (hasBlur) {
            if (!this.dataset.modernFilter) {
                this.dataset.modernFilter = Filter;
                this.dataset.webkitFilter = WebkitFilter;        
            }

            // Remove the blur due to the click event
            this.style.filter = 'none';
            this.style.webkitFilter = 'none';
        }
        else {
            this.style.filter = this.dataset.modernFilter;
            this.style.webkitFilter = this.dataset.webkitFilter;
        }
    });
}); // End of remove blur on click


// Carrousel scrolling and click nav link event
document.addEventListener('DOMContentLoaded', () => {
    
    // Smooth scroll for slider navigation on carrousel
    const navLinks = document.querySelectorAll('.slider-nav a');
    const slides = document.querySelectorAll('.slider img');
    const slider = document.querySelector('.slider');

    if (navLinks.length > 0 && slides.length > 0 && slider) {
        // Smooth scroll to the specific slide when nav links are clicked
        navLinks.forEach((link, i) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();

                slider.scrollTo({
                    left: slides[i].offsetLeft, // Scroll to the slide's left position
                    behavior: 'smooth'         // Smooth scrolling effect
                });

                // Use a timeout to ensure smooth scroll completes before updating active state
                setTimeout(() => {
                    // Update active nav link
                    navLinks.forEach((l) => l.classList.remove('active'));
                    link.classList.add('active');
                }, 20); 
            });
        });

        // Update active nav link on scroll
        slider.addEventListener('scroll', () => {
            const index = Math.round(slider.scrollLeft / slider.offsetWidth);
            navLinks.forEach((link, i) => {
                link.classList.toggle('active', i === index);
            });
        });
    }
});


// Expand cards on click (3 cards below title)
document.addEventListener("DOMContentLoaded", () => {

    const cards = document.querySelectorAll('.card');
    if (cards.length > 0) {

        // Expanding first card on page load
        const firstCard = cards[0]; 
        firstCard.classList.add('expanded'); 
        
        cards.forEach((card) => {
            card.addEventListener('click', () => {
                cards.forEach((c) => c.classList.remove('expanded'));               
                card.classList.add('expanded');               
            });
        });
    }
});