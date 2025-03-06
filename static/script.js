document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM fully loaded");
    const bookTitles = document.querySelectorAll(".book-title");
    console.log("Found book titles:", bookTitles.length);

    bookTitles.forEach(title => {
        title.addEventListener("click", function() {
            const bookId = this.getAttribute("data-book");
            const highlights = document.getElementById(`highlights-${bookId}`);
            const toggleIcon = this.querySelector(".toggle-icon");

            console.log(`Clicked: ${bookId}`);
            if (highlights) {
                if (highlights.style.display === "none" || highlights.style.display === "") {
                    highlights.style.display = "block";
                    toggleIcon.classList.add("active");
                } else {
                    highlights.style.display = "none";
                    toggleIcon.classList.remove("active");
                }
            } else {
                console.error(`Highlights not found for ${bookId}`);
            }
        });
    });
});