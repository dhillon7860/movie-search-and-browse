import sqlite3          # For connecting to our local SQLite database
import requests         # For making requests to TMDB
import time             # For caching (timestamp checks)
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # Allow cross-origin requests

# Your TMDB API key
TMDB_API_KEY = "05886b0a875a5f5f5258bef80f28dd71"

# Simple in-memory cache for trending movies
TRENDING_CACHE_DURATION = 60 * 5  # 5 minutes
trending_cache = {
    "data": None,
    "timestamp": 0
}


def get_db_connection():
    """
    Opens a connection to the local 'watchlist.db' file.
    """
    conn = sqlite3.connect("watchlist.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """
    Retrieves detailed information about a movie from TMDB using the provided numeric ID.
    Returns JSON with fields like title, overview, release date, and poster URL.
    """
    tmdb_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"

    try:
        response = requests.get(tmdb_url)
        response.raise_for_status()  # Raises HTTPError if 4xx or 5xx status
        movie_data = response.json()

        return jsonify({
            "Title": movie_data.get("title", "N/A"),
            "Overview": movie_data.get("overview", "No synopsis available"),
            "Release Date": movie_data.get("release_date", "Unknown"),
            "Rating": movie_data.get("vote_average", "N/A"),
            "Poster URL": (
                f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}"
                if movie_data.get("poster_path")
                else "https://via.placeholder.com/500x750?text=No+Image"
            )
        })

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return jsonify({"error": f"Movie with ID {movie_id} not found on TMDB"}), 404
        else:
            return jsonify({"error": f"TMDB HTTP error: {str(http_err)}"}), http_err.response.status_code
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return jsonify({"error": "Failed to fetch movie details"}), 500

@app.route('/api/search', methods=['GET'])
def search_movies():
    """
    Searches TMDB for movies that match the 'query' param (e.g. /api/search?query=Matrix).
    Returns a JSON list of matching movies with basic info: title, overview, release date, rating, and poster.
    """
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(tmdb_url)

    if response.status_code == 200:
        search_results = response.json().get("results", [])
        formatted_results = [
            {
                "id": movie["id"],
                "title": movie.get("title", "N/A"),
                "overview": movie.get("overview", "No synopsis available"),
                "release_date": movie.get("release_date", "Unknown"),
                "rating": movie.get("vote_average", "N/A"),
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                    if movie.get("poster_path")
                    else "https://via.placeholder.com/500x750?text=No+Image"
                )
            }
            for movie in search_results
        ]
        return jsonify({"results": formatted_results})

    return jsonify({"error": "Failed to fetch search results"}), 500

@app.route('/api/trending', methods=['GET'])
def get_trending_movies():
    """
    Fetches trending movies from TMDB using /trending/movie/day.
    Caches results in memory for 5 minutes to improve performance.
    """
    current_time = time.time()

    # If cached data is still valid, return from cache
    if (trending_cache["data"] is not None and
        (current_time - trending_cache["timestamp"]) < TRENDING_CACHE_DURATION):
        print("Serving trending movies from cache...")
        return jsonify({"results": trending_cache["data"]})

    # Otherwise, fetch from TMDB
    tmdb_url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}"
    response = requests.get(tmdb_url)

    if response.status_code == 200:
        trending_results = response.json().get("results", [])
        formatted_results = [
            {
                "id": movie["id"],
                "title": movie.get("title", "N/A"),
                "overview": movie.get("overview", "No synopsis available"),
                "release_date": movie.get("release_date", "Unknown"),
                "rating": movie.get("vote_average", "N/A"),
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                    if movie.get("poster_path")
                    else "https://via.placeholder.com/500x750?text=No+Image"
                )
            }
            for movie in trending_results
        ]
        trending_cache["data"] = formatted_results
        trending_cache["timestamp"] = current_time
        print("Fetched trending movies from TMDB and cached the result.")
        return jsonify({"results": formatted_results})
    else:
        return jsonify({"error": "Failed to fetch trending movies"}), 500

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """
    Returns the list of movies in our watchlist, along with whether each is favorited.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, COALESCE(favourite, 0) FROM watchlist")
    movies = [{"movie_id": row[0], "favourite": bool(row[1])} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"watchlist": movies})

@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """
    Adds a movie to the watchlist. If it's already present, we don't duplicate it.
    """
    data = request.json
    movie_id = data.get("movieId")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id FROM watchlist WHERE movie_id = ?", (movie_id,))
    if cursor.fetchone():
        message = f"Movie {movie_id} is already in the watchlist."
    else:
        cursor.execute("INSERT INTO watchlist (movie_id) VALUES (?)", (movie_id,))
        conn.commit()
        message = f"Movie {movie_id} added to watchlist!"

    conn.close()
    return jsonify({"message": message})

@app.route('/api/watchlist', methods=['DELETE'])
def remove_from_watchlist():
    """
    Removes a movie from the watchlist if present.
    """
    data = request.json
    movie_id = data.get("movieId")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE movie_id = ?", (movie_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Movie {movie_id} removed from watchlist!"})

@app.route('/api/watchlist/favourite', methods=['PUT'])
def toggle_favourite():
    """
    Toggles the 'favourite' status for a movie in the watchlist.
    """
    data = request.json
    movie_id = data.get("movieId")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT favourite FROM watchlist WHERE movie_id = ?", (movie_id,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    new_status = 1 if result[0] == 0 else 0
    cursor.execute("UPDATE watchlist SET favourite = ? WHERE movie_id = ?", (new_status, movie_id))
    conn.commit()
    conn.close()

    action_msg = "marked as favourite" if new_status else "removed from favourites"
    return jsonify({
        "message": f"Movie {movie_id} {action_msg}!",
        "favourite": bool(new_status)
    })

@app.route('/')
def home():
    """
    Renders our main HTML page (movie.html), which handles searching, watchlist, etc.
    """
    return render_template("movie.html")

if __name__ == '__main__':
    print("Registered Flask Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.methods}")
    app.run(debug=True)
