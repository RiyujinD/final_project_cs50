async function fetchPlaylistImages() {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/playlist-images");
      if (!response.ok) throw new Error("Failed to fetch images");
  
      const data = await response.json();
      console.log(data); // Debug: Check the response in console
  
      if (data.error) {
        console.error("Error:", data.error);
        return;
      }
  }
}

fetchPlaylistImages();
  