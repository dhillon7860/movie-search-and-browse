// static/js/movie-details.js

let selectedRating = 0;

// On page load, check URL for ?id=<movieID> and fetch details if present.
// Also load the watchlist immediately.
document.addEventListener("DOMContentLoaded", function () {
    const urlParams = new URLSearchParams(window.location.search);
    const movieId = urlParams.get("id");

    if (movieId) {
        fetchMovieDetails(movieId);
    }

    // Load the watchlist on page load
    loadWatchlist();
});

// Fetch detailed information about a movie from the server and update the UI
async function fetchMovieDetails(movieId) {
    const apiUrl = `/api/movie/${movieId}`;

    try {
        console.log(`Fetching details for Movie ID: ${movieId}`);
        const response = await fetch(apiUrl);
        if (!response.ok) {
            console.warn(`Movie ID ${movieId} not found or invalid.`);
            updateMovieUI(null);
            return;
        }
        const data = await response.json();
        console.log("Movie Data:", data);

        // Update the UI with the fetched movie data
        updateMovieUI(data);

        // Check if it's in the watchlist and if it's favorited
        checkIfInWatchlist(movieId);
        checkIfFavourite(movieId);
    } catch (error) {
        console.error("Error fetching movie details:", error);
        updateMovieUI(null);
    }
}

// Update (PUT) the rating of a specific movie in the watchlist (not shown in app.py above, but example usage)
async function updateMovieRating(movieId, rating) {
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
        console.log("Server Response:", data);
        document.getElementById("rating-message").innerText = data.message;
    } catch (error) {
        console.error("Error updating rating:", error);
    }
}

// Update the HTML elements on the page to reflect current movie details
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
    document.getElementById("movie-rating").innerText = `Rating: ${data.Rating}`;
    
    const poster = document.getElementById("movie-poster");
    poster.src = data["Poster URL"] || "https://via.placeholder.com/500x750?text=No+Image";
    poster.alt = data.Title;
}

// Search for movies by title (query) and display the results
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
        console.log("Search Results:", data);

        const resultsContainer = document.getElementById("search-results");
        resultsContainer.innerHTML = ""; // Clear old results

        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = "<p>No movies found. Try a different search term.</p>";
            return;
        }

        data.results.forEach(movie => {
            const movieDiv = document.createElement("div");
            movieDiv.innerHTML = `
                <strong>${movie.title} (${movie.release_date || "Unknown"})</strong>
                <br>Rating: ${movie.rating}
                <br>
                <img src="${movie.poster_url}" alt="${movie.title}" width="100">
                <br>
                <button onclick="window.location.href='/?id=${movie.id}'">View Details</button>
                <button onclick="addToWatchlist(${movie.id})">Add to Watchlist</button>
            `;
            resultsContainer.appendChild(movieDiv);
        });
    } catch (error) {
        console.error("Error searching for movies:", error);
        document.getElementById("search-results").innerHTML = "<p>Failed to fetch search results.</p>";
    }
}

// NEW: Fetch trending movies from our `/api/trending` endpoint
async function fetchTrendingMovies() {
    try {
        const response = await fetch('/api/trending');
        if (!response.ok) throw new Error("Failed to fetch trending movies");

        const data = await response.json();
        const trendingMovies = data.results || [];
        console.log("Trending Movies:", trendingMovies);

        const trendingContainer = document.getElementById("trending-results");
        trendingContainer.innerHTML = "";

        if (trendingMovies.length === 0) {
            trendingContainer.innerHTML = "<p>No trending movies found.</p>";
            return;
        }

        trendingMovies.forEach(movie => {
            const movieDiv = document.createElement("div");
            movieDiv.innerHTML = `
                <strong>${movie.title} (${movie.release_date || "Unknown"})</strong>
                <br>Rating: ${movie.rating}
                <br>
                <img src="${movie.poster_url}" alt="${movie.title}" width="100">
                <br>
                <button onclick="window.location.href='/?id=${movie.id}'">View Details</button>
                <button onclick="addToWatchlist(${movie.id})">Add to Watchlist</button>
            `;
            trendingContainer.appendChild(movieDiv);
        });
    } catch (error) {
        console.error("Error fetching trending movies:", error);
        document.getElementById("trending-results").innerHTML = "<p>Failed to fetch trending movies.</p>";
    }
}

// Check if the given movie is in our watchlist
async function checkIfInWatchlist(movieId) {
    try {
        const response = await fetch('/api/watchlist');
        if (!response.ok) throw new Error("Failed to fetch watchlist");

        const watchlistData = await response.json();
        const watchlist = watchlistData.watchlist || [];
        const inList = watchlist.some(entry => entry.movie_id === parseInt(movieId));

        updateWatchlistButtons(movieId, inList);
    } catch (error) {
        console.error("Error checking watchlist:", error);
    }
}

// Check if the movie is favorited in the watchlist
async function checkIfFavourite(movieId) {
    try {
        const response = await fetch('/api/watchlist');
        if (!response.ok) throw new Error("Failed to fetch watchlist");

        const watchlistData = await response.json();
        const watchlist = watchlistData.watchlist || [];
        const movie = watchlist.find(m => m.movie_id == movieId);
        const isFavourite = movie ? movie.favourite : false;

        updateFavouriteButton(movieId, isFavourite);
    } catch (error) {
        console.error("Error checking favorite status:", error);
    }
}

// Add a movie to the watchlist
async function addToWatchlist(movieId) {
    try {
        const response = await fetch('/api/watchlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId })
        });
        const data = await response.json();
        alert(data.message);

        updateWatchlistButtons(movieId, true);
        loadWatchlist();
    } catch (error) {
        console.error("Error adding to watchlist:", error);
    }
}

// Remove a movie from the watchlist
async function removeFromWatchlist(movieId) {
    try {
        const response = await fetch('/api/watchlist', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId })
        });
        const data = await response.json();
        alert(data.message);

        updateWatchlistButtons(movieId, false);
        loadWatchlist();
    } catch (error) {
        console.error("Error removing from watchlist:", error);
    }
}

// Update the "Add/Remove" watchlist button
function updateWatchlistButtons(movieId, isInWatchlist) {
    const watchlistContainer = document.getElementById("watchlist-buttons");
    watchlistContainer.innerHTML = "";

    const button = document.createElement("button");
    button.innerText = isInWatchlist ? "Remove from Watchlist" : "Add to Watchlist";
    button.onclick = isInWatchlist
        ? () => removeFromWatchlist(movieId)
        : () => addToWatchlist(movieId);

    watchlistContainer.appendChild(button);
}

// Toggle the favorite status of a movie in the watchlist
async function toggleFavourite(movieId) {
    if (!movieId) {
        console.error("Invalid Movie ID provided for toggling favorite.");
        return;
    }

    console.log(`Toggling favorite status for Movie ID: ${movieId}`);

    try {
        const response = await fetch('/api/watchlist/favourite', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movieId })
        });
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} - ${await response.text()}`);
        }

        const data = await response.json();
        console.log("Toggle Favorite Response:", data);
        updateFavouriteButton(movieId, data.favourite);
    } catch (error) {
        console.error("Error toggling favorite:", error);
    }
}

// Apply click listeners for star rating
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

// Highlight stars up to the selected rating
function highlightStars(rating) {
    const stars = document.querySelectorAll(".star");
    stars.forEach(star => {
        const value = parseInt(star.getAttribute("data-value"));
        star.classList.toggle("selected", value <= rating);
    });
}

// Send the selected rating to the server
async function submitRating() {
    const urlParams = new URLSearchParams(window.location.search);
    const movieId = urlParams.get("id");

    if (!movieId || !selectedRating) {
        alert("Please select a rating before submitting.");
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
        console.error("Error submitting rating:", error);
    }
}

// Update the text of the favorite button
function updateFavouriteButton(movieId, isFavourite) {
    let favButton = document.getElementById(`fav-btn-${movieId}`);
    if (!favButton) {
        favButton = document.getElementById("favorite-button");
    }
    if (!favButton) {
        console.warn(`Favorite button not found for Movie ID ${movieId}`);
        return;
    }

    favButton.innerText = isFavourite ? "Unfavourite" : "Mark as Favourite";
    favButton.classList.toggle("favorite", isFavourite);
    favButton.onclick = () => toggleFavourite(movieId);
}

// Load all movies from the watchlist
async function loadWatchlist() {
    try {
        const response = await fetch('/api/watchlist');
        if (!response.ok) throw new Error("Failed to fetch watchlist");

        const data = await response.json();
        const watchlist = data.watchlist || [];

        const watchlistContainer = document.getElementById("watchlist-container");
        watchlistContainer.innerHTML = "";

        // For each watchlist movie, fetch details
        for (let movie of watchlist) {
            const movieResponse = await fetch(`/api/movie/${movie.movie_id}`);
            if (movieResponse.ok) {
                const movieData = await movieResponse.json();

                const movieDiv = document.createElement("div");
                movieDiv.classList.add("watchlist-movie");
                movieDiv.dataset.movieId = movie.movie_id;

                movieDiv.innerHTML = `
                    <strong>${movieData.Title}</strong> (${movieData["Release Date"]})
                    <br>Rating: ${movieData.Rating}
                    <br>
                    <img src="${movieData["Poster URL"]}" alt="${movieData.Title}" width="100">
                    <br>
                    <button onclick="removeFromWatchlist(${movie.movie_id})">Remove</button>
                    <button id="fav-btn-${movie.movie_id}" onclick="toggleFavourite(${movie.movie_id})">
                        ${movie.favourite ? "Unfavourite" : "Mark as Favourite"}
                    </button>
                `;

                watchlistContainer.appendChild(movieDiv);
            }
        }
    } catch (error) {
        console.error("Error loading watchlist:", error);
    }
}

// Automatically load the watchlist once the window has loaded
window.onload = loadWatchlist;
