
// ✅ Extract movie ID from URL & Load Movie when page loads
document.addEventListener("DOMContentLoaded", function () {
    const urlParams = new URLSearchParams(window.location.search);
    const movieId = urlParams.get("id");

    // If viewing a specific movie, fetch details
    if (movieId) {
        fetchMovieDetails(movieId);
    }

    // Load the watchlist
    loadWatchlist();
});

// ✅ Fetch & display movie details from the API
async function fetchMovieDetails(movieId) {
    const apiUrl = `/api/movie/${movieId}`;

    try {
        console.log(`🔍 Fetching details for Movie ID: ${movieId}`);
        const response = await fetch(apiUrl);

        if (!response.ok) {
            console.warn(`⚠️ Movie ID ${movieId} not found.`);
            updateMovieUI(null);
            return;
        }

        const data = await response.json();
        console.log("🎬 Movie Data:", data);

        updateMovieUI(data);
        checkIfInWatchlist(movieId);
        checkIfFavourite(movieId);
    } catch (error) {
        console.error("❌ Error fetching movie details:", error);
        updateMovieUI(null);
    }
}

// ✅ Send Rating Update to API
async function updateMovieRating(movieId, rating) {
    console.log(`🔄 Sending rating update for Movie ID: ${movieId} with rating: ${rating}`);

    try {
        const response = await fetch('/api/watchlist/rating', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId, rating })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} - ${await response.text()}`);
        }

        const data = await response.json();
        console.log("✅ API Response:", data);
        document.getElementById("rating-message").innerText = data.message; // Show success message
    } catch (error) {
        console.error("❌ Error updating rating:", error);
    }
}


// ✅ Update UI with movie details
function updateMovieUI(data) {
    if (!data) {
        document.getElementById("movie-title").innerText = "Movie Not Found";
        document.getElementById("movie-synopsis").innerText = "Try searching for another movie.";
        document.getElementById("release-date").innerText = "";
        document.getElementById("movie-rating").innerText = "";
        document.getElementById("movie-poster").src = "https://via.placeholder.com/500x750?text=No+Image";
        return;
    }

    document.getElementById("movie-title").innerText = data.Title || "Title not available";
    document.getElementById("movie-synopsis").innerText = data.Overview || "No synopsis available";
    document.getElementById("release-date").innerText = `Released: ${data["Release Date"]}`;
    document.getElementById("movie-rating").innerText = `Rating: ⭐ ${data.Rating}`;

    const poster = document.getElementById("movie-poster");
    poster.src = data["Poster URL"] || "https://via.placeholder.com/500x750?text=No+Image";
    poster.alt = data.Title;
}
// ✅ Search for Movies
async function searchMovies() {
    const query = document.getElementById("movie-name-input").value.trim();
    if (!query) {
        alert("Please enter a movie name!");
        return;
    }

    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error("Failed to fetch search results");

        const data = await response.json();
        console.log("🎬 API Response:", data);  // ✅ Debugging log

        let resultsContainer = document.getElementById("search-results");
        resultsContainer.innerHTML = ""; // Clear previous results

        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = "<p>No movies found. Try a different search term.</p>";
            return;
        }

        data.results.forEach(movie => {
            let movieDiv = document.createElement("div");
            movieDiv.innerHTML = `
                <strong>${movie.title} (${movie.release_date || "Unknown"})</strong>
                <br>Rating: ⭐ ${movie.rating}
                <br>
                <img src="${movie.poster_url}" alt="${movie.title}" width="100">
                <br>
                <button onclick="window.location.href='/?id=${movie.id}'">View Details</button>
                <button onclick="addToWatchlist(${movie.id})">Add to Watchlist</button>
            `;
            resultsContainer.appendChild(movieDiv);
        });
    } catch (error) {
        console.error("❌ Error searching for movies:", error);
        document.getElementById("search-results").innerHTML = "<p>Failed to fetch search results.</p>";
    }
}



// ✅ Check if the movie is in the watchlist
async function checkIfInWatchlist(movieId) {
    try {
        const response = await fetch('/api/watchlist');
        if (!response.ok) throw new Error("Failed to fetch watchlist");

        const watchlistData = await response.json();
        let watchlist = watchlistData.watchlist || [];

        updateWatchlistButtons(movieId, watchlist.includes(parseInt(movieId)));
    } catch (error) {
        console.error("❌ Error checking watchlist:", error);
    }
}

// ✅ Check if the movie is marked as favourite
async function checkIfFavourite(movieId) {
    try {
        const response = await fetch('/api/watchlist');
        if (!response.ok) throw new Error("Failed to fetch watchlist");

        const watchlistData = await response.json();
        let watchlist = watchlistData.watchlist || [];

        let movie = watchlist.find(m => m.movie_id == movieId);
        let isFavourite = movie ? movie.favourite : false;

        updateFavouriteButton(movieId, isFavourite);
    } catch (error) {
        console.error("❌ Error checking favourite status:", error);
    }
}

// ✅ Add a movie to the watchlist
async function addToWatchlist(movieId) {
    try {
        const response = await fetch('/api/watchlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId: movieId })
        });

        const data = await response.json();
        alert(data.message);
        updateWatchlistButtons(movieId, true);
        loadWatchlist();
    } catch (error) {
        console.error("❌ Error adding to watchlist:", error);
    }
}

// ✅ Remove a movie from the watchlist
async function removeFromWatchlist(movieId) {
    try {
        const response = await fetch('/api/watchlist', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId: movieId })
        });

        const data = await response.json();
        alert(data.message);
        updateWatchlistButtons(movieId, false);
        loadWatchlist();
    } catch (error) {
        console.error("❌ Error removing from watchlist:", error);
    }
}

// ✅ Update Watchlist Buttons (Add/Remove)
function updateWatchlistButtons(movieId, isInWatchlist) {
    let watchlistContainer = document.getElementById("watchlist-buttons");
    watchlistContainer.innerHTML = "";

    let button = document.createElement("button");
    button.innerText = isInWatchlist ? "Remove from Watchlist" : "Add to Watchlist";
    button.onclick = isInWatchlist ? () => removeFromWatchlist(movieId) : () => addToWatchlist(movieId);

    watchlistContainer.appendChild(button);
}

// ✅ Toggle Favourite Status
async function toggleFavourite(movieId) {
    if (!movieId) {
        console.error("❌ Invalid Movie ID");
        return;
    }

    console.log(`🟡 Sending PUT request to toggle favourite for Movie ID: ${movieId}`);

    try {
        const response = await fetch('/api/watchlist/favourite', {  // ✅ Correct API Call
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId })  // ✅ Pass movieId in request body
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} - ${await response.text()}`);
        }

        const data = await response.json();
        console.log("✅ API Response:", data);

        updateFavouriteButton(movieId, data.favourite);
    } catch (error) {
        console.error("❌ Error toggling favourite:", error);
    }
}

// ✅ Add event listeners to stars for selection
document.addEventListener("DOMContentLoaded", function () {
    const stars = document.querySelectorAll(".star");
    stars.forEach(star => {
        star.addEventListener("click", function () {
            const rating = parseInt(this.getAttribute("data-value"));
            highlightStars(rating);
            selectedRating = rating;
        });
    });
});

// ✅ Highlight selected stars
function highlightStars(rating) {
    const stars = document.querySelectorAll(".star");
    stars.forEach(star => {
        if (parseInt(star.getAttribute("data-value")) <= rating) {
            star.classList.add("selected");
        } else {
            star.classList.remove("selected");
        }
    });
}

// ✅ Submit the rating to the server
async function submitRating() {
    const urlParams = new URLSearchParams(window.location.search);
    const movieId = urlParams.get("id");

    if (!movieId || !selectedRating) {
        alert("Please select a rating before submitting!");
        return;
    }

    console.log(`Submitting rating ${selectedRating} for movie ${movieId}`);

    try {
        const response = await fetch('/api/watchlist/rating', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId, rating: selectedRating })
        });

        const data = await response.json();
        if (response.ok) {
            document.getElementById("rating-message").innerText = data.message;
            document.getElementById("rating-message").style.display = "block";
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error("❌ Error submitting rating:", error);
    }
}


// ✅ Update Favourite Button for both Watchlist & Movie Details
function updateFavouriteButton(movieId, isFavourite) {
    let favButton = document.getElementById(`fav-btn-${movieId}`);

    // If the button is not found in the watchlist, check for the movie details page button
    if (!favButton) {
        favButton = document.getElementById("favorite-button");
    }

    if (!favButton) {
        console.warn(`⚠️ Favourite button not found for Movie ID ${movieId}`);
        return;
    }

    console.log(`🔄 Updating Favourite Button for ${movieId}: ${isFavourite ? "⭐" : "☆"}`);

    favButton.innerText = isFavourite ? "⭐ Unfavourite" : "☆ Mark as Favourite";
    favButton.classList.toggle("favorite", isFavourite);
    favButton.onclick = () => toggleFavourite(movieId);
}

// ✅ Load the Watchlist
async function loadWatchlist() {
    try {
        const response = await fetch('/api/watchlist');
        if (!response.ok) throw new Error("Failed to fetch watchlist");

        const data = await response.json();
        let watchlist = data.watchlist || [];

        let watchlistContainer = document.getElementById("watchlist-container");
        watchlistContainer.innerHTML = "";

        for (let movie of watchlist) {
            const movieResponse = await fetch(`/api/movie/${movie.movie_id}`);
            if (movieResponse.ok) {
                const movieData = await movieResponse.json();

                let movieDiv = document.createElement("div");
                movieDiv.classList.add("watchlist-movie");
                movieDiv.dataset.movieId = movie.movie_id;

                movieDiv.innerHTML = `
                    <strong>${movieData.Title}</strong> (${movieData["Release Date"]}) 
                    <br>Rating: ⭐ ${movieData.Rating}
                    <br>
                    <img src="${movieData["Poster URL"]}" alt="${movieData.Title}" width="100">
                    <br>
                    <button onclick="removeFromWatchlist(${movie.movie_id})">Remove</button>
                    <button id="fav-btn-${movie.movie_id}" onclick="toggleFavourite(${movie.movie_id})">
                        ${movie.favourite ? "⭐ Unfavourite" : "☆ Mark as Favourite"}
                    </button>
                `;

                watchlistContainer.appendChild(movieDiv);
            }
        }
    } catch (error) {
        console.error("❌ Error loading watchlist:", error);
    }
}

// ✅ Auto-load watchlist when the page loads
window.onload = loadWatchlist;
