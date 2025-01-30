document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.querySelector(".ryuji_button");
    const clearButton = document.getElementById("clear_button");
  
    clearButton.addEventListener("click", () => {
      searchInput.value = ""; // Clear input
      searchInput.focus(); // Keep focus
    });
  });