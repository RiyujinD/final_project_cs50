// Theme-Button 
document.addEventListener('DOMContentLoaded', () => {
    const checkbox = document.getElementById('theme_toggle');
    const svgDay = document.getElementById('svg_day');
    const svgNight = document.getElementById('svg_night');
    const svgs = [svgDay, svgNight];
    const html = document.documentElement;
  
    // Function to handle opacity animations
    const opacityAnimation = (fadeOutSvg, fadeInSvg) => {
      requestAnimationFrame(() => {
        fadeOutSvg.classList.remove('fadeIn', 'fadeOut');
        fadeInSvg.classList.remove('fadeIn', 'fadeOut');
  
        fadeOutSvg.classList.add('fadeOut');
        fadeInSvg.classList.add('fadeIn');
      });
    };
    
    checkbox.addEventListener('change', (e) => {
      const isChecked = e.target.checked;
  
      html.setAttribute('data-theme', isChecked ? 'light' : 'dark');
  
      // Move & Rotate both SVGs same direction and rotation
      svgs.forEach(svg => {
        svg.classList.toggle('offsetCheck', isChecked);
        svg.classList.toggle('offsetUncheck', !isChecked);
      });
  
      // One svg fadeOut as other fadeIn (fadeOut :: fadeIn)
      opacityAnimation(isChecked ? svgNight : svgDay, isChecked ? svgDay : svgNight);
    });
    
  }); // End of domContentLoaded Theme-Button 