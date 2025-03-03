document.addEventListener('DOMContentLoaded', () => {


    // Remove blur on the text in the main page
    document.getElementById('blur_text').addEventListener('click', function () {
        this.style.filter = 'none';
    });


    let items = document.querySelectorAll('.nav-item');
    items.forEach(item => {
        item.classList.remove("no-animate");
    });


    // Smooth scroll for slider navigation
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
            }, 20); // Adjust the timeout if needed (in ms)
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

    

    // Select all cards
    const cards = document.querySelectorAll('.card');
    
    if (cards.length > 0) {
        // Automatically expand the third card on page load
        const firstCard = cards[0]; // Zero-based index, so 2 is the third card
        if (firstCard) {
            firstCard.classList.add('expanded');
        }

        // Add click event listeners to each card
        cards.forEach(card => {
            card.addEventListener('click', () => {
                // Remove the "expanded" class from all other cards
                cards.forEach(c => c.classList.remove('expanded'));

                // Add the "expanded" class to the clicked card
                card.classList.add('expanded');
            });
        });
    }
});

