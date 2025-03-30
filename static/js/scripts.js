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





  // document.addEventListener('DOMContentLoaded', => {

  //   /* 
  //   * Configure Youtube Iframe API
  //   * https://developers.google.com/youtube/iframe_api_reference
  //   **/ 
  //   const tag = document.createElement('script');
  //   tag.src = "https://www.youtube.com/iframe_api";
  //   var firstScriptTag = document.getElementsByTagName('script')[0];
  //   firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
  //   var player;

  //   function onYouTubeIframeAPIReady() {
  //     player = new YT.Player('player', {
  //       height: '390',
  //       width: '640',
  //       videoId: 'M7lc1UVf-VE',
  //       playerVars: {
  //         'playsinline': 1
  //       },
  //       events: {
  //         'onReady': onPlayerReady,
  //         'onStateChange': onPlayerStateChange
  //       }
  //     });
  //   }

  //   function onPlayerReady(event) {
  //     event.targetplayVideo();
  //   }

  //   var done = false;
  //   function onPlayerStateChange(event) {
  //     if (event.data == YT.PlayerState.PLAYING && !done) {
  //       setTimeout(stopVideo, 6000);
  //       done = true;
  //     }
  //   }
  //   function stopVideo() {
  //     player.stopVideo();
  //   }
  //   // Initialize the player
  //   onYouTubeIframeAPIReady();
  // })