
document.addEventListener('DOMContentLoaded', () => {

    // Scroll and auto scroll for the slider carousel
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
    if (cards.length === 0) return;

    const firstCard = cards[0];
    firstCard.classList.add('expanded');

    cards.forEach((target) => {
        target.addEventListener('click', () => {
            if (target.classList.contains('expanded')) return; // Skip if already expanded
            
            cards.forEach((card) => card.classList.remove('expanded'));
            target.classList.add('expanded');
        });
    });
});


document.addEventListener('DOMContentLoaded', () => {
    const buttonWrapper = document.getElementById('containerSplitButtonNResult');
    const leftHalfButton = document.querySelector('.left');
    const rightHalfButton = document.querySelector('.right');

    if (!leftHalfButton || !rightHalfButton || !buttonWrapper) return;

    let isActiveButton = false;
    const halfsButton = [leftHalfButton, rightHalfButton];

    halfsButton.forEach((button) => {
        button.addEventListener('click', (e) => {

            halfsButton.forEach((b) => {
                b.innerHTML = "Login Now!";
            });

            if (!isActiveButton) {
                let resultInfo = document.createElement('p');
                let logoInfo = document.createElement('p');
                logoInfo.classList.add('LogoResult');

                if (e.target === leftHalfButton) {
                    resultInfo.classList.add('Aclicked');
                    resultInfo.innerHTML = '🎉 Success: '; 
                    logoInfo.innerHTML = '🏆'; 
                } 
                else if (e.target === rightHalfButton) {
                    resultInfo.classList.add('Bclicked');
                    resultInfo.innerHTML = '❌ Failure ❌';
                    logoInfo.innerHTML = '😔';
                }
                buttonWrapper.prepend(logoInfo);
                buttonWrapper.append(resultInfo);
                isActiveButton = true;
            }
            else {
                console.log("CTA button on");
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.querySelector(".searchForm");
    const searchInput = document.querySelector(".ryuji_button");
    const clearButton = document.getElementById("clear_button");
    const searchIcon = document.getElementById("searchIcon");
    const metaData = document.querySelector('.metadata_wrapper');
    const playButton = document.getElementById('svg-container');
    const audio = document.getElementById('audioExtract');
    const cdImage = document.querySelector('.cdImage');
    const svgContainer =document.getElementById('svg-container');
    const buttonCTA = document.querySelector('.btn_callToAction');
  
    let isMissing = !clearButton || !searchInput || !searchForm || !metaData || !searchIcon || !playButton || !audio || !cdImage || !svgContainer;
    if (isMissing) return;
  
    // Search form functionality
    clearButton.addEventListener('click', () => {
      searchInput.value = '';
      searchInput.focus();
    });
  
    searchIcon.addEventListener('click', (event) => {
      searchForm.dispatchEvent(new Event('submit', { bubbles: true }));
      searchInput.focus();
    });

    let failCount = 0;
  
    searchForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const oldResult = searchForm.querySelector('.ResultTagAG');
      if (oldResult) oldResult.remove();
  
      let resultPTag = document.createElement('p');
      resultPTag.classList.add('ResultTagAG');
  
      let formInput = searchInput.value.replace(/\s+/g, '').toLowerCase(); // Regex to remove all whitespace /s
      if (formInput === 'radiohead') {
        resultPTag.classList.add('SuccessResultAG');
        resultPTag.innerHTML = '🎉 Success 🎉';
        metaData.style.display = "flex";
        buttonCTA.style.display = "flex";
        
        // Red or Green outline on search Icon
        searchInput.classList.add('success');
        searchInput.classList.remove('fail');
        
        // Remove class after 3 seconds to return to focus outline color
        setTimeout(() => {
          searchInput.classList.remove('success');
        }, 3000);
      } 
      else {
        failCount += 1 % 3;

        if (failCount === 3) {
            buttonCTA.style.display = "flex";
        }
        resultPTag.classList.add('failResultAG');
        resultPTag.innerHTML = '❌ Failure ❌';
        metaData.style.display = "none";
        
        searchInput.classList.add('fail');
        searchInput.classList.remove('success');
        
        setTimeout(() => {
          searchInput.classList.remove('fail');
        }, 3000);
      }
  
      searchForm.appendChild(resultPTag);
    });
  
    // Audio and play button functionality
    let pulseInterval;
  
    function startPulseCycle() {
      stopPulseCycle();
      pulseInterval = setInterval(() => {
        playButton.classList.add('hover_state');
        setTimeout(() => {
          playButton.classList.remove('hover_state');
        }, 3000);
      }, 6000);
    }
  
    function stopPulseCycle() {
      clearInterval(pulseInterval);
      pulseInterval = null;
    }
  
    audio.addEventListener('play', () => {
      stopPulseCycle();
      playButton.classList.add('hover_state');
      svgContainer.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25v13.5m-7.5-13.5v13.5" />
            </svg>`;
    });
  
    function handleAudioStop() {
      playButton.classList.remove('hover_state');
      startPulseCycle();
      svgContainer.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />`;
    }
  
    audio.addEventListener('pause', handleAudioStop);
    audio.addEventListener('ended', handleAudioStop);
  
    // CD Rotation functionality
    let rotationAngle = 0;
    let currentSpeed = 0;
    const maxSpeed = 0.5;
    const accelerationRate = 0.010;
    const decelerationRate = 0.005;
    let rotationInterval = null;
  
    function updateRotation() {
      if (!audio) return;
  
      if (!audio.paused && !audio.ended) {
        currentSpeed = Math.min(currentSpeed + accelerationRate, maxSpeed);
      } else {
        currentSpeed = Math.max(currentSpeed - decelerationRate, 0);
      }
  
      rotationAngle = (rotationAngle + currentSpeed) % 360;
      cdImage.style.transform = `rotate(${rotationAngle}deg)`;
  
      requestAnimationFrame(updateRotation);
    }
    updateRotation(); 
  
    // Sound fade functionality
    audio.currentTime = 153;
    audio.volume = 0;
    const maxVolume = 0.2;
    const fadeStep = 0.005;
    let isFading = false;
    let fadeFrameId;

    function fadeIn(callback) {
        cancelAnimationFrame(fadeFrameId);
        let vol = audio.volume;

        function increaseVolume() {
        if (vol < maxVolume) {
            vol = Math.min(vol + fadeStep, maxVolume);
            audio.volume = vol;
            fadeFrameId = requestAnimationFrame(increaseVolume);
        } else {
            isFading = false;
            if (callback) callback();
        }
        }

        isFading = true;
        fadeFrameId = requestAnimationFrame(increaseVolume);
    }

    function fadeOut(callback) {
        cancelAnimationFrame(fadeFrameId);
        let vol = audio.volume;

        function decreaseVolume() {
        if (vol > 0) {
            vol = Math.max(vol - fadeStep / 1.5, 0);
            audio.volume = vol;
            fadeFrameId = requestAnimationFrame(decreaseVolume);
        } else {
            isFading = false;
            if (callback) callback();
        }
        }

        isFading = true;
        fadeFrameId = requestAnimationFrame(decreaseVolume);
    }

    playButton.addEventListener('click', () => {
        if (audio.paused || audio.ended) {
        fadeIn(() => audio.play());
        } else {
        fadeOut(() => audio.pause());
        }
    });

    audio.addEventListener('timeupdate', () => {
        if (audio.currentTime >= 169 && !isFading) {
        fadeOut(() => {
            audio.pause();
            audio.currentTime = 153;
        });
        }
    });

    audio.addEventListener('ended', () => {
        fadeOut(() => {
        audio.currentTime = 153;
        });
    });
});



// Remove blur on text in Title 
document.addEventListener('DOMContentLoaded', () => {

    blurText = document.getElementById('blur_text');

    if (!blurText) return;

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
