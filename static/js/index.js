// Remove blur on text in Title 
document.addEventListener('DOMContentLoaded', () => {

    blurText = document.getElementById('blur_text');

    blurText.addEventListener('click', function () {
        const stylesElement = window.getComputedStyle(this);
        const filter = stylesElement.getPropertyValue('filter');
        const webkitFilter = stylesElement.getPropertyValue('-webkit-filter');
        
        const hasBlur = filter.includes("blur") || webkitFilter.includes("blur");
        

        if (hasBlur) {
            if (!this.dataset.modernFilter) {
                this.dataset.modernFilter = filter;
                this.dataset.webkitFilter = webkitFilter;        
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
}); 


// Scroll and auto scroll for the slider carousel
document.addEventListener('DOMContentLoaded', () => {
    const slider = document.querySelector('#slider'),
          slides = document.querySelectorAll('#slider img'),
          navLinks = document.querySelectorAll('#slider-nav a');

    const sliderExist = slider && slides.length > 0 && navLinks.length > 0;
    
    if (!sliderExist) return;

    let currentIndex = 0;
    let autoScrollTimer, scrollEndTimer;

    navLinks[0].classList.add('active');
    
    const scrollToSlide = (index) => {
        slider.scrollTo({
            left: slides[index].offsetLeft,
            behavior: 'smooth'
        });
        navLinks.forEach((link, i) => link.classList.toggle('active', i === index));
        currentIndex = index;
    };

    const startAutoScroll = () => {
        clearTimeout(autoScrollTimer);
        autoScrollTimer = setTimeout(() => {
            scrollToSlide((currentIndex + 1) % slides.length);
            startAutoScroll();
        }, 5000);
    };

    navLinks.forEach((link, index) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            scrollToSlide(index);
            startAutoScroll();
        });
    });

    slider.addEventListener('scroll', () => {
        clearTimeout(scrollEndTimer);
        scrollEndTimer = setTimeout(() => startAutoScroll(), 200); // Only reset after user stops scrolling
    });

    startAutoScroll();
});


// expand cards and add shadow base on color theme
document.addEventListener("DOMContentLoaded", () => {
    
    const cards = document.querySelectorAll('.card');

    if (cards.length > 0) {
        
        const firstCard = cards[0]; 
        firstCard.classList.add('expanded'); 
        
        cards.forEach((target) => {
            target.addEventListener('click', () => {
                cards.forEach((card) => card.classList.remove('expanded'));               
                target.classList.add('expanded');               
            });
        });
    }
});



