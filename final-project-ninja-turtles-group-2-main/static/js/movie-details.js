// static/js/movie-details.js

let selectedRating = 0;

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM loaded...");

  // 1) Direct snippet for trending/all/week from TMDb
  fetchDirectAllWeek();

  // 2) If there's ?id= in URL, fetch details
  const urlParams = new URLSearchParams(window.location.search);
  const movieId = urlParams.get("id");
  if (movieId) {
    fetchMovieDetails(movieId);
  }

  // 3) Load watchlist
  loadWatchlist();

  // 4) Setup star rating
  const stars = document.querySelectorAll(".star");
  stars.forEach(star => {
    star.addEventListener("click", () => {
      const val = parseInt(star.getAttribute("data-value"));
      highlightStars(val);
      selectedRating = val;
    });
  });
});

/**********************************************
 * DIRECT SNIPPET: trending/all/week
 **********************************************/
function fetchDirectAllWeek() {
  // Insert your real TMDb v3 API key
  const apiKey = "03fb23d2e8ca73070c3bdb09bf268ae6";
  const apiUrl = `https://api.themoviedb.org/3/trending/movie/week?api_key=${apiKey}`;

  const moviesContainer = document.getElementById("movies");
  if (!moviesContainer) return;

  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      data.results.forEach(media => {
        const card = createMovieCardDirect(media);
        moviesContainer.appendChild(card);
      });
    })
    .catch(error => {
      console.error("Error fetching data (movie/week):", error);
      moviesContainer.innerHTML = "<p>Failed to load trending movie/week data.</p>";
    });
}

function createMovieCardDirect(media) {
  // media might have "title" for movies or "name" for TV
  const { id, title, name, backdrop_path } = media;

  const movieCard = document.createElement("div");
  movieCard.classList.add("movie_item");

  // Include “View Details” and “Add to Watchlist”:
  movieCard.innerHTML = `
    <img 
      src="https://image.tmdb.org/t/p/w500${backdrop_path}" 
      class="movie_img_rounded" 
      alt="${title || name}"
    />
    <div class="title">${title || name}</div>
    <button onclick="window.location.href='/?id=${id}'">View Details</button>
    <button onclick="addToWatchlist(${id})">Add to Watchlist</button>
  `;
  return movieCard;
}

/**********************************************
 * SEARCH, ADVANCED SEARCH, MOVIE DETAILS
 **********************************************/
async function searchMovies() {
  const queryInput = document.getElementById("movie-name-input");
  if (!queryInput) {
    alert("No search input found.");
    return;
  }
  const query = queryInput.value.trim();
  if (!query) {
    alert("Please enter a movie name!");
    return;
  }
  try {
    const resp = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
    if (!resp.ok) throw new Error("Search fetch error");
    const data = await resp.json();
    const results = data.results || [];

    const simpleSection = document.getElementById("simple-search-section");
    if (simpleSection) {
      simpleSection.classList.remove("hidden");
    }

    const simpleContainer = document.getElementById("search-results-simple");
    if (!simpleContainer) return;
    simpleContainer.innerHTML = "";

    if (!results.length) {
      simpleContainer.innerHTML = "<p>No movies found.</p>";
      return;
    }

    const grid = document.createElement("div");
    grid.style.display = "flex";
    grid.style.flexWrap = "wrap";
    grid.style.gap = "10px";

    results.forEach(movie => {
      const div = document.createElement("div");
      div.style.width = "150px";
      div.style.border = "1px solid #ccc";
      div.style.borderRadius = "4px";
      div.style.overflow = "hidden";
      div.style.textAlign = "center";
      div.innerHTML = `
        <img src="${movie.poster_url}" alt="${movie.title}" width="150">
        <div style="padding:5px;">
          <strong>${movie.title}</strong><br>
          (${movie.release_date || "Unknown"})<br>
          Rating: ${movie.rating}<br><br>
          <button onclick="window.location.href='/?id=${movie.id}'">View Details</button>
          <button onclick="addToWatchlist(${movie.id})">Add to Watchlist</button>
        </div>
      `;
      grid.appendChild(div);
    });
    simpleContainer.appendChild(grid);
  } catch (err) {
    console.error("searchMovies() error:", err);
    const c = document.getElementById("search-results-simple");
    if (c) c.innerHTML = "<p>Failed to fetch search results.</p>";
  }
}

async function advancedSearch() {
  const q = document.getElementById("adv-search-query")?.value.trim();
  const year = document.getElementById("adv-search-year")?.value.trim();
  const genre = document.getElementById("adv-search-genre")?.value.trim();
  const minRating = document.getElementById("adv-search-minrating")?.value.trim();
  const sort = document.getElementById("adv-search-sort")?.value.trim();

  let url = "/api/search?";
  if (q) url += `query=${encodeURIComponent(q)}&`;
  if (year) url += `year=${encodeURIComponent(year)}&`;
  if (genre) url += `genre=${encodeURIComponent(genre)}&`;
  if (minRating) url += `minRating=${encodeURIComponent(minRating)}&`;
  if (sort) url += `sort=${encodeURIComponent(sort)}`;

  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error("Advanced search fetch error");
    const data = await resp.json();
    const advContainer = document.getElementById("search-results-adv");
    if (!advContainer) return;
    advContainer.innerHTML = "";

    if (!data.results || data.results.length === 0) {
      advContainer.innerHTML = "<p>No movies found with the given criteria.</p>";
      return;
    }

    const grid = document.createElement("div");
    grid.style.display = "flex";
    grid.style.flexWrap = "wrap";
    grid.style.gap = "10px";

    data.results.forEach(movie => {
      const div = document.createElement("div");
      div.style.width = "150px";
      div.style.border = "1px solid #ccc";
      div.style.borderRadius = "4px";
      div.style.overflow = "hidden";
      div.style.textAlign = "center";
      div.innerHTML = `
        <img src="${movie.poster_url}" alt="${movie.title}" width="150">
        <div style="padding:5px;">
          <strong>${movie.title}</strong><br>
          (${movie.release_date || "Unknown"})<br>
          Rating: ${movie.rating}<br><br>
          <button onclick="window.location.href='/?id=${movie.id}'">View Details</button>
          <button onclick="addToWatchlist(${movie.id})">Add to Watchlist</button>
        </div>
      `;
      grid.appendChild(div);
    });
    advContainer.appendChild(grid);
  } catch (err) {
    console.error("advancedSearch() error:", err);
    const c = document.getElementById("search-results-adv");
    if (c) c.innerHTML = "<p>Failed advanced search.</p>";
  }
}

async function fetchMovieDetails(movieId) {
  try {
    const resp = await fetch(`/api/movie/${movieId}`);
    if (!resp.ok) {
      console.warn(`Movie with ID ${movieId} not found or invalid.`);
      updateMovieUI(null);
      return;
    }
    const data = await resp.json();
    updateMovieUI(data);

    checkIfInWatchlist(movieId);
    checkIfFavourite(movieId);
  } catch (err) {
    console.error("Error fetching movie details:", err);
    updateMovieUI(null);
  }
}

function updateMovieUI(data) {
  if (!data) {
    console.warn("No data to display in detail UI");
    return;
  }
  const detailSection = document.getElementById("detail-section");
  if (detailSection) detailSection.classList.remove("hidden");

  const posterEl = document.getElementById("detail-poster");
  if (posterEl) {
    posterEl.src = data["Poster URL"] || "https://via.placeholder.com/500x750?text=No+Image";
    posterEl.alt = data.Title || "Poster";
  }

  const titleEl = document.getElementById("detail-title");
  if (titleEl) {
    titleEl.textContent = data.Title || "No Title";
  }

  const releaseEl = document.getElementById("detail-release");
  if (releaseEl) {
    releaseEl.textContent = `Release Date: ${data["Release Date"] || "Unknown"}`;
  }

  const ratingEl = document.getElementById("detail-rating");
  if (ratingEl) {
    ratingEl.textContent = `TMDb Rating: ${data.Rating || "N/A"}`;
  }

  const overviewEl = document.getElementById("detail-overview");
  if (overviewEl) {
    overviewEl.textContent = data.Overview || "No synopsis available.";
  }

  const castEl = document.getElementById("detail-cast");
  if (castEl) {
    if (data.Cast && data.Cast.length) {
      let castHtml = "<strong>Cast:</strong><ul>";
      data.Cast.forEach(c => {
        castHtml += `<li>${c.name} as ${c.character}</li>`;
      });
      castHtml += "</ul>";
      castEl.innerHTML = castHtml;
    } else {
      castEl.innerHTML = "<strong>Cast:</strong> No cast data.";
    }
  }

  const trailerEl = document.getElementById("detail-trailer");
  if (trailerEl) {
    if (data.Trailer) {
      trailerEl.innerHTML = `<strong>Trailer:</strong> <a href="${data.Trailer}" target="_blank">Watch on YouTube</a>`;
    } else {
      trailerEl.innerHTML = "<strong>Trailer:</strong> No trailer available.";
    }
  }
}

/**********************************************
 * WATCHLIST
 **********************************************/
async function addToWatchlist(movieId) {
  try {
    const resp = await fetch("/api/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId })
    });
    const result = await resp.json();
    alert(result.message);
  } catch (err) {
    console.error("Error adding to watchlist:", err);
  }
}

async function removeFromWatchlist(movieId) {
  try {
    const resp = await fetch("/api/watchlist", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId })
    });
    const result = await resp.json();
    alert(result.message);
    loadWatchlist();
  } catch (err) {
    console.error("Error removing from watchlist:", err);
  }
}

async function loadWatchlist() {
  try {
    const resp = await fetch("/api/watchlist");
    if (!resp.ok) throw new Error("Watchlist fetch error");
    const data = await resp.json();
    const container = document.getElementById("watchlist-container");
    if (!container) return;
    container.innerHTML = "";

    for (let item of (data.watchlist || [])) {
      const detailResp = await fetch(`/api/movie/${item.movie_id}`);
      if (!detailResp.ok) continue;
      const detailData = await detailResp.json();

      const div = document.createElement("div");
      div.style.display = "flex";
      div.style.alignItems = "center";
      div.style.gap = "10px";
      div.style.border = "1px solid #ccc";
      div.style.borderRadius = "4px";
      div.style.marginBottom = "10px";
      div.innerHTML = `
        <img src="${detailData["Poster URL"]}" alt="${detailData.Title}" style="width:60px;border-radius:4px;">
        <div>
          <strong>${detailData.Title}</strong> (${detailData["Release Date"]})<br>
          TMDb Rating: ${detailData.Rating}
          <p>Your Rating: ${item.rating || 0}/5</p>
          <button onclick="removeFromWatchlist(${item.movie_id})">Remove</button>
          <button id="fav-btn-${item.movie_id}" onclick="toggleFavourite(${item.movie_id})">
            ${item.favourite ? "Unfavourite" : "Mark as Favourite"}
          </button>
        </div>
      `;
      container.appendChild(div);
      updateFavouriteButton(item.movie_id, item.favourite);
    }
  } catch (err) {
    console.error("loadWatchlist error:", err);
  }
}

/**********************************************
 * FAVOURITES
 **********************************************/
async function toggleFavourite(movieId) {
  if (!movieId) return;
  try {
    const resp = await fetch("/api/watchlist/favourite", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId })
    });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`Fav toggle error: ${resp.status} - ${txt}`);
    }
    const data = await resp.json();
    updateFavouriteButton(movieId, data.favourite);
  } catch (err) {
    console.error("toggleFavourite error:", err);
  }
}

function updateFavouriteButton(movieId, isFav) {
  let favBtn = document.getElementById(`fav-btn-${movieId}`);
  if (!favBtn) return;
  favBtn.innerText = isFav ? "Unfavourite" : "Mark as Favourite";
  favBtn.classList.toggle("favorite", isFav);
}

/**********************************************
 * CHECK WATCHLIST / FAV
 **********************************************/
async function checkIfInWatchlist(movieId) {
  try {
    const resp = await fetch("/api/watchlist");
    if (!resp.ok) throw new Error("Watchlist fetch error");
    // no immediate UI updates
  } catch (err) {
    console.error("checkIfInWatchlist error:", err);
  }
}

async function checkIfFavourite(movieId) {
  try {
    const resp = await fetch("/api/watchlist");
    if (!resp.ok) throw new Error("Watchlist fetch error");
    const data = await resp.json();
    const item = data.watchlist.find(w => w.movie_id === parseInt(movieId));
    const isFav = item ? item.favourite : false;
    updateFavouriteButton(movieId, isFav);
  } catch (err) {
    console.error("checkIfFavourite error:", err);
  }
}

/**********************************************
 * STAR RATING
 **********************************************/
function highlightStars(rating) {
  const stars = document.querySelectorAll(".star");
  stars.forEach(star => {
    const val = parseInt(star.getAttribute("data-value"));
    star.classList.toggle("selected", val <= rating);
  });
  selectedRating = rating;
}

async function submitRating() {
  const urlParams = new URLSearchParams(window.location.search);
  const movieId = urlParams.get("id");
  if (!movieId || !selectedRating) {
    alert("Select a movie (View Details) and pick a star rating first.");
    return;
  }
  try {
    const resp = await fetch("/api/watchlist/rating", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId, rating: selectedRating })
    });
    const data = await resp.json();
    if (resp.ok) {
      alert(`Rating updated: ${selectedRating}/5`);
      loadWatchlist();
    } else {
      alert(`Error: ${data.error || data.message}`);
    }
  } catch (err) {
    console.error("submitRating error:", err);
  }
}
