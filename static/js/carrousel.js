document.querySelectorAll('.slider-nav a').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const targetId = e.target.getAttribute('href').substring(1); // Get target ID
        const targetImage = document.getElementById(targetId);

        // Smooth scroll to the image
        targetImage.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
    });
});