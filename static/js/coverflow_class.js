const images_playlist = [
  {
    url:
      "https://images.unsplash.com/photo-1734917141553-274732d788cb?q=80&w=2006&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    metadata: "Cosmic dust",
    artist: "Steve Busch"
  },
  {
    url:
      "https://images.unsplash.com/photo-1740387223785-6ab827ab4fb1?q=80&w=2022&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    metadata: "Burning View",
    artist: "Piermanuele Sberni"
  },
  {
    url:
      "https://images.unsplash.com/photo-1613078825094-3db5dac29c36?q=80&w=2942&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    metadata: "Monet",
    artist: "Nick Fewings"
  },
  {
    url:
      "https://images.unsplash.com/photo-1515405295579-ba7b45403062?q=80&w=2160&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    metadata: "Calm Ocean",
    artist: "Henrik Dønnestad"
  },
  {
    url:
      "https://images.unsplash.com/photo-1601042879364-f3947d3f9c16?q=80&w=2787&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    metadata: "Cyber Night",
    artist: "Valentin BEAUVAIS"
  },
  {
    url:
      "https://plus.unsplash.com/premium_photo-1661964177687-57387c2cbd14?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    metadata: "Fuji Peak",
    artist: "Getty Images"
  },
  {
    url:
      "https://plus.unsplash.com/premium_photo-1664304745123-36f04a51acb9?q=80&w=2942&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    metadata: "Danger zone",
    artist: "Getty Images"
  }
];

class CoverFlow {
  constructor(wrapperSelector, trackSelector, itemSelector, imagesData) {
    this.trackContainer = document.querySelector(wrapperSelector);
    this.track = document.querySelector(trackSelector);
    this.imagesList = imagesData;
    this.prevButton = document.querySelector("#previous_buttonCoverflow");
    this.nextButton = document.querySelector("#next_buttonCoverflow");

    // Render items / Covers
    this.populateImages();

    // Now that items render we can store them in the constructor/blueprint
    this.items = document.querySelectorAll(itemSelector);
    this.totalItems = this.items.length;

    // Calculate item width including margins-inline
    if (this.totalItems > 0) {
      this.itemStyle = window.getComputedStyle(this.items[0]); // Get all style of the first item
      const margin =
        parseFloat(this.itemStyle.marginInlineStart) +
        parseFloat(this.itemStyle.marginInlineEnd); // Parse to float margininline (left and right)
      this.itemWidth = this.items[0].offsetWidth + margin;
    } else {
      this.itemWidth = 0;
    }

    // Set current index of items to the middle point for centering (if even half - 1)
    this.currentIndex =
      this.totalItems % 2 === 0
        ? this.totalItems / 2 - 1
        : Math.floor(this.totalItems / 2);

    this.containerWidth = this.trackContainer.clientWidth; // container width = 100vw
    this.isAnimating = false;
    this.isDragging = false;
    this.startX = 0; // Starting position of drag
    this.currentDrag = 0;
    this.dragThreshold = 65; // Sensitivity for dragging on desktop
    this.touchDragThreshold = 50; // Sensitivity for dragging on touch screen device

    this.init();
  } // End of constructor

  // Helper: Update currentIndex and center() item (note: newIndex calculate in the setup functions)
  moveToIndex(newIndex) {
    this.currentIndex = Math.min(Math.max(newIndex, 0), this.totalItems - 1); // Clamp between 0 and totalItems - 1 and update currentIndex
    this.centerItem();
  }

  // Helper: Base offset for centering currentIndex in the track
  getBaseOffset() {
    return (
      this.currentIndex * this.itemWidth -
      this.containerWidth / 2 +
      this.itemWidth / 2
    );
  }

  centerItem() {
    if (this.totalItems === 0) return;

    /* 
         Loop through all items and update their styles based on their position relative to currentIndex:
         - Remove old state classes
         - Apply rotation, scaling, and visibility adjustments based on distance
         - Assign appropriate z-index to maintain proper layering
      */
    this.items.forEach((item, index) => {
      item.classList.remove("active", "leftItem", "rightItem"); // Remove previous state classes

      const direction = index - this.currentIndex; // Negative left, positive right, 0 current one
      const distance = Math.abs(direction);
      let rotation = 0;
      const baseRotation = 70; // Base rotation before multiplying by factor
      const minRotation = 0.3;
      const rotationFactor = 0.8; // Factor to adjust rotation (further = less rotation)
      const adjustmentRate = 0.2; // Controls how much the factor changes based on distance
      let zIndex = 0;

      // Calculate rotation factor
      let factor = rotationFactor - (distance - 1) * adjustmentRate;
      factor = Math.max(factor, minRotation); // Ensure minimum rotation limit

      if (direction === 0) {
        item.classList.add("active");
        rotation = 0;
        zIndex = 100;
        item.style.transform = `rotateY(0deg) scale(1.5)`;
      } else if (direction < 0) {
        item.classList.add("leftItem");
        rotation = baseRotation * factor; // Apply leftward rotation
        zIndex = 100 - distance;
        item.style.transform = `rotateY(${rotation}deg) scale(1)`;
      } else {
        item.classList.add("rightItem");
        rotation = -baseRotation * factor; // Apply rightward rotation
        zIndex = 100 - distance;
        item.style.transform = `rotateY(${rotation}deg) scale(1)`;
      }

      item.style.zIndex = zIndex;
      item.style.visibility = distance > 4 ? "hidden" : "visible"; // Hide items too far from center
    });

    // Center the track based on the current active index and offset
    const offset = this.getBaseOffset();
    this.track.style.transform = `translateX(${-offset}px)`;
  } // End of centerItem

  populateImages() {
    this.track.innerHTML = "";

    this.imagesList.forEach((imageObj) => {
        const item = document.createElement("div");
        item.classList.add("itemCoverflow");
        
        // Preload image before setting background
        const img = new Image();
        img.onload = () => {
            item.style.setProperty("--cover-url", `url(${imageObj.url})`);
        };
        img.src = imageObj.url;

        // Create metadata wrapper
        const metadataWrapper = document.createElement("div");
        metadataWrapper.classList.add("metadata_wrapper");
        
        // Add title and artist
        const songTitle = document.createElement("div");
        songTitle.classList.add("metadata_songTitle");
        songTitle.textContent = imageObj.metadata;
        
        const artistName = document.createElement("div");
        artistName.classList.add("metadata_artist");
        artistName.textContent = imageObj.artist;
        
        metadataWrapper.appendChild(songTitle);
        metadataWrapper.appendChild(artistName);
        item.appendChild(metadataWrapper);
        this.track.appendChild(item);
    });
  } // End of populateImages

  init() {
    if (this.totalItems <= 1) return;
    this.centerItem();

    // Update container width and re-center on window resize
    window.addEventListener("resize", () => {
      this.containerWidth = this.trackContainer.clientWidth;
      this.centerItem();
    });

    this.setupSvgEvent();
    this.setupWheelScrolling();
    this.setupDragging();
    this.setupTouchEvents();
    this.setupClickEvents();
  } // End of init

  setupSvgEvent() {
    // Handler for the previous button: moves to the previous index and animates the prevButton.
    const prevHandler = () => {
      this.moveToIndex(this.currentIndex - 1);
      this.prevButton.classList.remove("anime_prev");
      void this.prevButton.offsetWidth; // Force reflow by removing state
      this.prevButton.classList.add("anime_prev");
    };

    // Handler for the next button: moves to the next index and animates the nextButton.
    const nextHandler = () => {
      this.moveToIndex(this.currentIndex + 1);
      this.nextButton.classList.remove("anime_next");
      void this.nextButton.offsetWidth; // Force reflow by removing state
      this.nextButton.classList.add("anime_next");
    };

    // Event listener implementation for click and touch
    ["click", "touchend"].forEach((event) => {
      this.prevButton.addEventListener(event, prevHandler);
      this.nextButton.addEventListener(event, nextHandler);
    });

    this.prevButton.addEventListener("animationend", () => {
      this.prevButton.classList.remove("anime_prev");
    });

    this.nextButton.addEventListener("animationend", () => {
      this.nextButton.classList.remove("anime_next");
    });
  } // End of setupSvgEvent

  setupWheelScrolling() {
    const sensitivityFactor = 0.1; // Lower = slower scrolling

    // Handle wheel scroll to navigate items
    this.track.addEventListener("wheel", (e) => {
      if (!this.isAnimating) {
        this.isAnimating = true;
        requestAnimationFrame(() => {
          if (e.deltaY * sensitivityFactor > 1) {
            // Apply factor for slower effect
            this.moveToIndex(this.currentIndex + 1);
          } else if (e.deltaY * sensitivityFactor < -1) {
            this.moveToIndex(this.currentIndex - 1);
          }
          this.isAnimating = false;
        });
      }
    });
  } // End of setupWheelScrolling

  setupDragging() {
    // Mouse down on track to start dragging
    this.track.addEventListener("mousedown", (e) => {
      this.isDragging = true;
      this.startX = e.clientX; // Store event position
      this.currentDrag = 0;
      // Add dragging class to change cursor to 'grabbing'
      this.track.classList.add("dragging");
    });

    document.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      this.currentDrag = e.clientX - this.startX; // Update drag every time mouse moves
      if (Math.abs(this.currentDrag) >= this.dragThreshold) {
        if (this.currentDrag > 0) {
          this.moveToIndex(this.currentIndex - 1);
        } else {
          this.moveToIndex(this.currentIndex + 1);
        }
        this.startX = e.clientX; // Reset start so threshold needs to be passed again
        this.currentDrag = 0;
      } else {
        // Translate track during drag
        const baseOffset = this.getBaseOffset();
        this.track.style.transform = `translateX(${
          -baseOffset - this.currentDrag
        }px)`;
      }
    });

    document.addEventListener("mouseup", () => {
      if (!this.isDragging) return;
      this.isDragging = false;
      this.currentDrag = 0;
      // Remove dragging class when drag ends
      this.track.classList.remove("dragging");
      this.centerItem();
    });
  } // End of setupDragging

  setupClickEvents() {
    // Navigate to item on click
    this.items.forEach((item, index) => {
      item.addEventListener("click", () => {
        this.moveToIndex(index);
      });
    });
  } // End of setupClickEvents

  // Mobile / tablet handler
  setupTouchEvents() {
    this.track.addEventListener("touchstart", (e) => {
      this.isDragging = true;
      this.startX = e.touches[0].clientX; // Store the first touch position
      this.touchMoved = false; // Flag to handle click
    });

    document.addEventListener("touchmove", (e) => {
      if (!this.isDragging) return;
      const currentTouch = e.touches[0].clientX; // Update as it moves
      const delta = currentTouch - this.startX; // Distance dragged
      if (Math.abs(delta) >= this.touchDragThreshold) {
        this.touchMoved = true;

        // Determine direction and update the currentIndex
        if (delta > 0) {
          this.moveToIndex(this.currentIndex - 1);
        } else {
          this.moveToIndex(this.currentIndex + 1);
        }
        this.startX = currentTouch; // Reset position for further changes
      } else {
        const baseOffset = this.getBaseOffset();
        this.track.style.transform = `translateX(${-baseOffset - delta}px)`;
      }
    });

    document.addEventListener("touchend", (e) => {
      if (!this.isDragging) return;
      this.isDragging = false;

      // If there was little or no movement, treat as a click/tap
      let touchedItem = !this.touchMoved ? e.target.closest(".item") : null;
      if (touchedItem) touchedItem.click();

      this.centerItem();
    });
  } // End of setupTouchEvents
} // End of CoverFlow class


// Initialize CoverFlow instance on DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  // Initialize CoverFlow instance
  const coverflow = new CoverFlow(
    "#wrapper_sliderCoverflow",
    "#slider_trackCoverflow",
    ".itemCoverflow",
    images_playlist
  );
});