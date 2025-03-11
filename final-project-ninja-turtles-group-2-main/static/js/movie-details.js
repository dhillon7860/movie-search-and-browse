/******************************************************************************
 movie-details.js
 Purpose:
   - Fetch trending movies for the week in a horizontal scroller
   - Basic search & advanced search calls
   - Display movie details
   - Manage a local watchlist (favorite toggles, ratings)
******************************************************************************/

let selectedRating = 0;

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM loaded -> Attempting to fetch trending 'week' movies...");

  // 1) Fetch trending movies this week from TMDb
  fetchTrendingMoviesWeek();

  // 2) If there's ?id= in URL, load that movie's details
  const urlParams = new URLSearchParams(window.location.search);
  const movieId = urlParams.get("id");
  if (movieId) {
    fetchMovieDetails(movieId);
  }

  // 3) Load watchlist from local DB
  loadWatchlist();

  // 4) Setup star rating clicks
  const stars = document.querySelectorAll(".star");
  stars.forEach(star => {
    star.addEventListener("click", () => {
      const val = parseInt(star.getAttribute("data-value"));
      highlightStars(val);
      selectedRating = val;
    });
  });
});

/******************************************************************************
 * TRENDING MOVIES THIS WEEK
 ******************************************************************************/
function fetchTrendingMoviesWeek() {
  const container = document.getElementById("movies");
  if (!container) return;

  const tmdbKey = "03fb23d2e8ca73070c3bdb09bf268ae6";
  const trendUrl = `https://api.themoviedb.org/3/trending/movie/week?api_key=${tmdbKey}`;

  fetch(trendUrl)
    .then(resp => resp.json())
    .then(data => {
      if (!data.results || !data.results.length) {
        container.innerHTML = "<p>No trending data found for this week.</p>";
        return;
      }
      // We'll place them in a horizontal row with fancy styling
      data.results.forEach(movie => {
        const card = createTrendWeekCard(movie);
        container.appendChild(card);
      });
    })
    .catch(err => {
      console.error("Failed to fetch trending movies this week:", err);
      container.innerHTML = "<p>Failed to load trending movies this week.</p>";
    });
}

/** Creates a horizontally friendly card with a "score" and "Add to Watchlist" */
function createTrendWeekCard(movie) {
  const { id, title, name, poster_path, vote_average, release_date } = movie;
  const displayTitle = title || name || "Untitled";
  const posterUrl = poster_path
    ? `https://image.tmdb.org/t/p/w500${poster_path}`
    : "https://via.placeholder.com/500x750?text=No+Image";
  const userScore = vote_average ? `${(vote_average * 10).toFixed(0)}%` : "N/A";
  const card = document.createElement("div");
  card.classList.add("trend-card");

  card.innerHTML = `
    <div class="trend-poster">
      <img src="${posterUrl}" alt="${displayTitle}" />
      <div class="score-badge">${userScore}</div>
    </div>
    <div class="trend-title">${displayTitle}</div>
    <small>${release_date || ""}</small>
    <br>
    <button onclick="window.location.href='/?id=${id}'">View Details</button>
    <button onclick="addToWatchlist(${id})">Add to Watchlist</button>
  `;
  return card;
}

/******************************************************************************
 * SEARCH: Basic & Advanced
 ******************************************************************************/
async function searchMovies() {
  const inputElem = document.getElementById("movie-name-input");
  if (!inputElem) {
    alert("Cannot find search input element!");
    return;
  }
  const query = inputElem.value.trim();
  if (!query) {
    alert("Please enter a movie name!");
    return;
  }

  try {
    const resp = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
    if (!resp.ok) throw new Error("search fetch error");
    const data = await resp.json();
    const results = data.results || [];

    const section = document.getElementById("simple-search-section");
    const resultsBox = document.getElementById("search-results-simple");
    if (section) section.classList.remove("hidden");
    if (!resultsBox) return;

    resultsBox.innerHTML = "";
    if (!results.length) {
      resultsBox.innerHTML = "<p>No movies found!</p>";
      return;
    }

    const flexWrap = document.createElement("div");
    flexWrap.style.display = "flex";
    flexWrap.style.flexWrap = "wrap";
    flexWrap.style.gap = "10px";

    results.forEach(item => {
      const div = document.createElement("div");
      div.style.width = "150px";
      div.style.border = "1px solid #ccc";
      div.style.borderRadius = "4px";
      div.style.overflow = "hidden";
      div.style.textAlign = "center";

      div.innerHTML = `
        <img src="${item.poster_url}" alt="${item.title}" width="150" />
        <div style="padding:5px;">
          <strong>${item.title}</strong><br>
          (${item.release_date || "Unknown"})<br>
          Rating: ${item.rating}<br><br>
          <button onclick="window.location.href='/?id=${item.id}'">View Details</button>
          <button onclick="addToWatchlist(${item.id})">Add to Watchlist</button>
        </div>
      `;
      flexWrap.appendChild(div);
    });

    resultsBox.appendChild(flexWrap);

  } catch (err) {
    console.error("searchMovies error:", err);
    const resultsBox = document.getElementById("search-results-simple");
    if (resultsBox) {
      resultsBox.innerHTML = "<p>Failed to fetch search results.</p>";
    }
  }
}

async function advancedSearch() {
  const qVal = document.getElementById("adv-search-query")?.value.trim();
  const yVal = document.getElementById("adv-search-year")?.value.trim();
  const gVal = document.getElementById("adv-search-genre")?.value.trim();
  const rVal = document.getElementById("adv-search-minrating")?.value.trim();
  const sVal = document.getElementById("adv-search-sort")?.value.trim();

  let url = "/api/search?";
  if (qVal) url += `query=${encodeURIComponent(qVal)}&`;
  if (yVal) url += `year=${encodeURIComponent(yVal)}&`;
  if (gVal) url += `genre=${encodeURIComponent(gVal)}&`;
  if (rVal) url += `minRating=${encodeURIComponent(rVal)}&`;
  if (sVal) url += `sort=${encodeURIComponent(sVal)}`;

  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error("advanced search error");
    const data = await resp.json();
    const advBox = document.getElementById("search-results-adv");
    if (!advBox) return;
    advBox.innerHTML = "";

    const items = data.results || [];
    if (!items.length) {
      advBox.innerHTML = "<p>No advanced matches found.</p>";
      return;
    }

    const flexBox = document.createElement("div");
    flexBox.style.display = "flex";
    flexBox.style.flexWrap = "wrap";
    flexBox.style.gap = "10px";

    items.forEach(one => {
      const card = document.createElement("div");
      card.style.width = "150px";
      card.style.border = "1px solid #ccc";
      card.style.borderRadius = "4px";
      card.style.overflow = "hidden";
      card.style.textAlign = "center";

      card.innerHTML = `
        <img src="${one.poster_url}" alt="${one.title}" width="150">
        <div style="padding:5px;">
          <strong>${one.title}</strong><br>
          (${one.release_date || "Unknown"})<br>
          Rating: ${one.rating}<br><br>
          <button onclick="window.location.href='/?id=${one.id}'">View Details</button>
          <button onclick="addToWatchlist(${one.id})">Add to Watchlist</button>
        </div>
      `;
      flexBox.appendChild(card);
    });

    advBox.appendChild(flexBox);

  } catch (err) {
    console.error("advancedSearch error:", err);
    const advBox = document.getElementById("search-results-adv");
    if (advBox) advBox.innerHTML = "<p>Failed advanced search.</p>";
  }
}

/******************************************************************************
 * MOVIE DETAILS
 ******************************************************************************/
async function fetchMovieDetails(movieId) {
  try {
    const resp = await fetch(`/api/movie/${movieId}`);
    if (!resp.ok) {
      console.warn("fetchMovieDetails not OK for ID:", movieId);
      updateMovieUI(null);
      return;
    }
    const data = await resp.json();
    updateMovieUI(data);

    checkIfInWatchlist(movieId);
    checkIfFavourite(movieId);
  } catch (err) {
    console.error("fetchMovieDetails error:", err);
    updateMovieUI(null);
  }
}

function updateMovieUI(data) {
  const detailSection = document.getElementById("detail-section");
  if (!detailSection) return;

  if (!data) {
    detailSection.classList.remove("hidden");
    detailSection.innerHTML = "<h2>Movie Not Found</h2>";
    return;
  }
  detailSection.classList.remove("hidden");

  const posterEl = document.getElementById("detail-poster");
  if (posterEl) {
    posterEl.src = data["Poster URL"] || "https://via.placeholder.com/500x750?text=No+Image";
    posterEl.alt = data.Title || "??";
  }
  const titleEl = document.getElementById("detail-title");
  if (titleEl) titleEl.textContent = data.Title || "N/A";

  const releaseEl = document.getElementById("detail-release");
  if (releaseEl) releaseEl.textContent = `Release Date: ${data["Release Date"] || "???"}`;

  const ratingEl = document.getElementById("detail-rating");
  if (ratingEl) ratingEl.textContent = `TMDb Rating: ${data.Rating || "N/A"}`;

  const overviewEl = document.getElementById("detail-overview");
  if (overviewEl) overviewEl.textContent = data.Overview || "No synopsis available.";

  // Cast
  const castEl = document.getElementById("detail-cast");
  if (castEl) {
    if (data.Cast && data.Cast.length) {
      let cHtml = "<strong>Cast:</strong><ul>";
      data.Cast.forEach(p => {
        cHtml += `<li>${p.name} as ${p.character}</li>`;
      });
      cHtml += "</ul>";
      castEl.innerHTML = cHtml;
    } else {
      castEl.innerHTML = "<strong>Cast:</strong> Not listed.";
    }
  }

  // Trailer
  const trailerEl = document.getElementById("detail-trailer");
  if (trailerEl) {
    if (data.Trailer) {
      trailerEl.innerHTML = `<strong>Trailer:</strong> <a href="${data.Trailer}" target="_blank">Watch on YouTube</a>`;
    } else {
      trailerEl.innerHTML = "<strong>Trailer:</strong> Not available.";
    }
  }
}

/******************************************************************************
 * WATCHLIST
 ******************************************************************************/
async function addToWatchlist(movieId) {
  try {
    const resp = await fetch("/api/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId })
    });
    const msg = await resp.json();
    alert(msg.message);
  } catch (err) {
    console.error("addToWatchlist error:", err);
  }
}

async function removeFromWatchlist(movieId) {
  try {
    const resp = await fetch("/api/watchlist", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId })
    });
    const msg = await resp.json();
    alert(msg.message);
    loadWatchlist();
  } catch (err) {
    console.error("removeFromWatchlist error:", err);
  }
}

async function loadWatchlist() {
  const container = document.getElementById("watchlist-container");
  if (!container) return;
  container.innerHTML = "";

  try {
    const resp = await fetch("/api/watchlist");
    if (!resp.ok) throw new Error("loadWatchlist fetch error");
    const data = await resp.json();

    const items = data.watchlist || [];
    for (let w of items) {
      const detailResp = await fetch(`/api/movie/${w.movie_id}`);
      if (!detailResp.ok) continue;
      const detail = await detailResp.json();

      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.gap = "10px";
      row.style.border = "1px solid #ccc";
      row.style.borderRadius = "4px";
      row.style.marginBottom = "10px";

      row.innerHTML = `
        <img
          src="${detail["Poster URL"]}"
          alt="${detail.Title}"
          style="width:60px; border-radius:4px;"
        >
        <div>
          <strong>${detail.Title}</strong> (${detail["Release Date"]})<br>
          TMDb Rating: ${detail.Rating}
          <p>Your Rating: ${w.rating || 0}/5</p>
          <button onclick="removeFromWatchlist(${w.movie_id})">Remove</button>
          <button id="fav-btn-${w.movie_id}" onclick="toggleFavourite(${w.movie_id})">
            ${w.favourite ? "Unfavourite" : "Mark as Favourite"}
          </button>
        </div>
      `;
      container.appendChild(row);
      updateFavouriteButton(w.movie_id, w.favourite);
    }
  } catch (err) {
    console.error("loadWatchlist error:", err);
    container.innerHTML = "<p>Failed to load watchlist.</p>";
  }
}

/******************************************************************************
 * FAVOURITES
 ******************************************************************************/
async function toggleFavourite(movieId) {
  if (!movieId) return;
  try {
    const resp = await fetch("/api/watchlist/favourite", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId })
    });
    if (!resp.ok) {
      const t = await resp.text();
      throw new Error(`toggleFavourite error: ${resp.status} - ${t}`);
    }
    const data = await resp.json();
    updateFavouriteButton(movieId, data.favourite);
  } catch (err) {
    console.error("toggleFavourite error:", err);
  }
}

function updateFavouriteButton(movieId, isFav) {
  const favBtn = document.getElementById(`fav-btn-${movieId}`);
  if (!favBtn) return;
  favBtn.innerText = isFav ? "Unfavourite" : "Mark as Favourite";
  favBtn.classList.toggle("favorite", isFav);
}

/******************************************************************************
 * CHECK WATCHLIST / FAV
 ******************************************************************************/
async function checkIfInWatchlist(movieId) {
  // currently no direct UI effect
  try {
    const resp = await fetch("/api/watchlist");
    if (!resp.ok) throw new Error("checkIfInWatchlist fetch error");
  } catch (err) {
    console.error("checkIfInWatchlist error:", err);
  }
}
async function checkIfFavourite(movieId) {
  try {
    const resp = await fetch("/api/watchlist");
    if (!resp.ok) throw new Error("checkIfFavourite fetch error");
    const data = await resp.json();
    const item = data.watchlist.find(v => v.movie_id === parseInt(movieId));
    const isFav = item ? item.favourite : false;
    updateFavouriteButton(movieId, isFav);
  } catch (err) {
    console.error("checkIfFavourite error:", err);
  }
}

/******************************************************************************
 * STAR RATING
 ******************************************************************************/
function highlightStars(rating) {
  const allStars = document.querySelectorAll(".star");
  allStars.forEach(s => {
    const val = parseInt(s.getAttribute("data-value"));
    s.classList.toggle("selected", val <= rating);
  });
  selectedRating = rating;
}

async function submitRating() {
  const urlParams = new URLSearchParams(window.location.search);
  const movieId = urlParams.get("id");
  if (!movieId || !selectedRating) {
    alert("Select a movie and a star rating first!");
    return;
  }
  try {
    const resp = await fetch("/api/watchlist/rating", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movieId, rating: selectedRating })
    });
    const responseMsg = await resp.json();
    if (resp.ok) {
      alert(`Rating updated to ${selectedRating}/5`);
      loadWatchlist();
    } else {
      alert(`Error: ${responseMsg.error || responseMsg.message}`);
    }
  } catch (err) {
    console.error("submitRating error:", err);
  }
}
