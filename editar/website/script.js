let gallery = document.getElementById('image-gallery'); // Main image container
let perPage = 15; // Number of images per page
let currentPage = 1; // Current page index
let images = []; // All images retrieved from the server
let filteredImages = []; // Images after filtering

// Fetch initial set of images and load the first page
fetch('/images')
    .then((response) => {
        if (!response.ok) {
            console.error("Failed to fetch images:", response.statusText);
            return; // Exit if the fetch fails
        }
        return response.json();  // Parse the response as JSON
    })
    .then((data) => {
        if (!data || !Array.isArray(data)) {
            console.error("Unexpected data format:", data);
            return; // Exit if data is invalid
        }
        
        images = data; // Store fetched images
        filteredImages = images; // Start with all images
        loadPage(currentPage); // Load the first page with initial data
    })
    .catch((error) => {
        console.error("Error fetching images:", error); // Log fetch error
    });

function loadPage(page) {
    currentPage = page; // Update the current page index

    gallery.innerHTML = ""; // Clear existing content

    let start = (page - 1) * perPage;
    let end = Math.min(start + perPage, filteredImages.length);

    for (let i = start; i < end; i++) {
        let div = document.createElement("div");
        div.className = "image-item";

        let img = document.createElement("img");
        img.src = filteredImages[i].path;
        img.alt = `Image ${i + 1}`; // Add an alt attribute for accessibility
        img.addEventListener("click", () => viewImageDetails(filteredImages[i])); // Redirect to the new page
        div.appendChild(img);  // Add the image to the div

        gallery.appendChild(div); // Append div to the gallery
    }

    updatePagination(); // Update the pagination controls
}

function updatePagination() {
    let prevButton = document.getElementById("prev-button");
    let nextButton = document.getElementById("next-button");
    let prevButtonBottom = document.getElementById("prev-button-bottom");
    let nextButtonBottom = document.getElementById("next-button-bottom");

    let totalPageCount = Math.ceil(filteredImages.length / perPage); // Total number of pages

    prevButton.disabled = currentPage <= 1; // Disable if at the first page
    nextButton.disabled = currentPage >= totalPageCount; // Disable if at the last page
    prevButtonBottom.disabled = currentPage <= 1; // Disable if at the first page
    nextButtonBottom.disabled = currentPage >= totalPageCount; // Disable if at the last page

    if (!prevButton.hasAttribute("data-initialized")) {
        prevButton.setAttribute("data-initialized", "true");
        prevButton.addEventListener("click", () => {
            if (currentPage > 1) {
                loadPage(currentPage - 1); // Load the previous page
            }
        });
    }

    if (!nextButton.hasAttribute("data-initialized")) {
        nextButton.setAttribute("data-initialized", "true");
        nextButton.addEventListener("click", () => {
            if (currentPage < totalPageCount) {
                loadPage(currentPage + 1); // Load the next page
            }
        });
    }

    if (!prevButtonBottom.hasAttribute("data-initialized")) {
        prevButtonBottom.setAttribute("data-initialized", "true");
        prevButtonBottom.addEventListener("click", () => {
            if (currentPage > 1) {
                loadPage(currentPage - 1); // Load the previous page
            }
        });
    }

    if (!nextButtonBottom.hasAttribute("data-initialized")) {
        nextButtonBottom.setAttribute("data-initialized", "true");
        nextButtonBottom.addEventListener("click", () => {
            if (currentPage < totalPageCount) {
                loadPage(currentPage + 1); // Load the next page
            }
        });
    }
}

function viewImageDetails(image) {
    window.location.href = `/image-details/${image.id}`;
}
