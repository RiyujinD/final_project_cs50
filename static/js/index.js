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
    const navLinks = document.querySelectorAll('.slider-nav a');
    const slides = document.querySelectorAll('.slider img');
    const slider = document.querySelector('.slider');

    if (navLinks.length > 0 && slides.length > 0 && slider) {

        navLinks[0].classList.add('active'); // Default active slide 

        // Smooth scroll to specific slide when nav links are clicked
        navLinks.forEach((link, i) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                scrollToSlide(i);
            });
        });

        // Automatically switch slides every 5 seconds
        let currentIndex = 0;
        const switchSlide = () => {
            currentIndex = (currentIndex + 1) % slides.length; // Loop back to the first slide
            scrollToSlide(currentIndex);
        };

        const scrollToSlide = (index) => {
            slider.scrollTo({
                left: slides[index].offsetLeft,
                behavior: 'smooth',
            });
            updateActiveNav(index);
        };

        const updateActiveNav = (index) => {
            navLinks.forEach((link, i) => link.classList.toggle('active', i === index));
        };

        // Start the automatic slide switch with a 5-second interval
        setInterval(switchSlide, 5000);
    }
});


// expand cards and add shadow base on color theme
document.addEventListener("DOMContentLoaded", () => {

    const html = document.documentElement;
    const cards = document.querySelectorAll('.card');
    
    // Expand cards on click 
    if (cards.length > 0) {

        // Expanding first card on page load
        const firstCard = cards[0]; 
        firstCard.classList.add('expanded'); 
        
        
        cards.forEach((target) => {
            target.addEventListener('click', () => {
                cards.forEach((card) => card.classList.remove('expanded'));               
                target.classList.add('expanded');               
            });
        });
    }
    
    // Change shadow of cards 
    const shadowHandler = () => {
        const theme = html.getAttribute('data-theme');

        cards.forEach((card) => {
            if (theme === "dark") {
                card.style.boxShadow = "0px 25px 20px -20px rgba(40, 197, 66, 0.45), 0 0 10px rgba(255, 255, 255, 0.2)";
            }
            else if (theme === "light") {
                card.style.boxShadow = "13px 13px 10px -4px rgba(0, 0, 0, 0.4),"
                                    + "5px 3px 6px -2px rgba(0, 0, 0, 0.5),"
                                    + "inset 4px 15px 13px -14px rgba(255, 255, 255, 1)";
            }
        });
    };

    shadowHandler();

    // Observe change to html data-theme
    const observer = new MutationObserver(shadowHandler);

    observer.observe(html, {
        attributes: true,                   // Watch for changes to attributes
        attributeFilter: ['data-theme']     // Only watch changes to the 'data-theme' attribute
    });


});



