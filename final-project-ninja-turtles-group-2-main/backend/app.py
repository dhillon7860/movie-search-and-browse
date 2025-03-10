import sqlite3
import requests
import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# PUT YOUR REAL KEY HERE
TMDB_API_KEY = "05886b0a875a5f5f5258bef80f28dd71"

TRENDING_CACHE_DURATION = 300  # 5 minutes
trending_cache = {
    "data": None,
    "timestamp": 0
}

def init_db():
    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            movie_id INTEGER PRIMARY KEY,
            favourite INTEGER DEFAULT 0,
            rating INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def home():
    """Renders the multi-tab single page (movie.html)."""
    return render_template("movie.html")

@app.route('/api/trending', methods=['GET'])
def get_trending_movies():
    """
    Returns trending movies from TMDb (/trending/movie/day).
    Caches results for 5 minutes to reduce API calls.
    Logs status code so you can see if TMDb is returning 200 or an error.
    """
    now = time.time()
    if trending_cache["data"] and (now - trending_cache["timestamp"] < TRENDING_CACHE_DURATION):
        print("Serving trending movies from cache...")
        return jsonify({"results": trending_cache["data"]})

    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}"
    resp = requests.get(url)
    print("TMDb trending endpoint status:", resp.status_code)  # Debug log

    if resp.status_code == 200:
        data = resp.json().get("results", [])
        results = []
        for m in data:
            results.append({
                "id": m["id"],
                "title": m.get("title", "N/A"),
                "overview": m.get("overview", ""),
                "release_date": m.get("release_date", "Unknown"),
                "rating": m.get("vote_average", "N/A"),
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}"
                    if m.get("poster_path")
                    else "https://via.placeholder.com/500x750?text=No+Image"
                )
            })
        trending_cache["data"] = results
        trending_cache["timestamp"] = now
        print("Fetched trending movies from TMDB and cached the result.")
        return jsonify({"results": results})
    else:
        print("TMDb trending fetch failed. Status code:", resp.status_code, "Body:", resp.text)
        return jsonify({"error": "Failed to fetch trending movies"}), 500

@app.route('/api/search', methods=['GET'])
def search_movies():
    base_url_search = "https://api.themoviedb.org/3/search/movie"
    base_url_discover = "https://api.themoviedb.org/3/discover/movie"

    q = request.args.get("query")
    year = request.args.get("year")
    genre = request.args.get("genre")
    min_rating = request.args.get("minRating")
    sort = request.args.get("sort")

    tmdb_params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": "false"
    }

    if q:
        tmdb_params["query"] = q
        resp = requests.get(base_url_search, params=tmdb_params)
    else:
        if year:
            tmdb_params["primary_release_year"] = year
        if genre:
            tmdb_params["with_genres"] = genre
        if min_rating:
            tmdb_params["vote_average.gte"] = min_rating
        if sort:
            tmdb_params["sort_by"] = sort
        resp = requests.get(base_url_discover, params=tmdb_params)

    if resp.status_code == 200:
        data = resp.json().get("results", [])
        formatted = []
        for movie in data:
            formatted.append({
                "id": movie["id"],
                "title": movie.get("title", "N/A"),
                "overview": movie.get("overview", "No synopsis available"),
                "release_date": movie.get("release_date", "Unknown"),
                "rating": movie.get("vote_average", "N/A"),
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}"
                    if movie.get("poster_path")
                    else "https://via.placeholder.com/500x750?text=No+Image"
                )
            })
        return jsonify({"results": formatted})
    else:
        return jsonify({"error": "Failed to fetch search results"}), 500

@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    base_url = "https://api.themoviedb.org/3"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}

    try:
        resp_main = requests.get(f"{base_url}/movie/{movie_id}", params=params)
        resp_main.raise_for_status()
        main_data = resp_main.json()

        resp_credits = requests.get(f"{base_url}/movie/{movie_id}/credits", params=params)
        resp_credits.raise_for_status()
        credits_data = resp_credits.json()
        cast_info = []
        if "cast" in credits_data:
            for c in credits_data["cast"][:5]:
                cast_info.append({
                    "name": c.get("name", "Unknown"),
                    "character": c.get("character", "")
                })

        resp_videos = requests.get(f"{base_url}/movie/{movie_id}/videos", params=params)
        resp_videos.raise_for_status()
        videos_data = resp_videos.json()
        trailer_url = None
        for vid in videos_data.get("results", []):
            if vid.get("site") == "YouTube" and "trailer" in vid.get("type", "").lower():
                trailer_url = f"https://www.youtube.com/watch?v={vid['key']}"
                break

        return jsonify({
            "Title": main_data.get("title", "N/A"),
            "Overview": main_data.get("overview", "No synopsis available"),
            "Release Date": main_data.get("release_date", "Unknown"),
            "Rating": main_data.get("vote_average", "N/A"),
            "Poster URL": (
                f"https://image.tmdb.org/t/p/w500{main_data.get('poster_path')}"
                if main_data.get("poster_path")
                else "https://via.placeholder.com/500x750?text=No+Image"
            ),
            "Cast": cast_info,
            "Trailer": trailer_url
        })

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return jsonify({"error": f"Movie with ID {movie_id} not found on TMDB"}), 404
        else:
            return jsonify({"error": f"TMDB HTTP error: {str(http_err)}"}), http_err.response.status_code
    except requests.exceptions.RequestException as e:
        print("API Error:", e)
        return jsonify({"error": "Failed to fetch movie details"}), 500

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("SELECT movie_id, favourite, rating FROM watchlist")
    rows = c.fetchall()
    conn.close()

    watchlist_data = []
    for row in rows:
        watchlist_data.append({
            "movie_id": row[0],
            "favourite": bool(row[1]),
            "rating": row[2]
        })
    return jsonify({"watchlist": watchlist_data})

@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO watchlist (movie_id) VALUES (?)", (movie_id,))
        conn.commit()
        msg = f"Movie {movie_id} added to watchlist!"
    except sqlite3.IntegrityError:
        msg = f"Movie {movie_id} is already in the watchlist."
    conn.close()
    return jsonify({"message": msg})

@app.route('/api/watchlist', methods=['DELETE'])
def remove_from_watchlist():
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE movie_id = ?", (movie_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Movie {movie_id} removed from watchlist!"})

@app.route('/api/watchlist/favourite', methods=['PUT'])
def toggle_favourite():
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("SELECT favourite FROM watchlist WHERE movie_id = ?", (movie_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    new_status = 1 if row[0] == 0 else 0
    c.execute("UPDATE watchlist SET favourite = ? WHERE movie_id = ?", (new_status, movie_id))
    conn.commit()
    conn.close()

    msg = "marked as favourite" if new_status else "removed from favourites"
    return jsonify({
        "message": f"Movie {movie_id} {msg}!",
        "favourite": bool(new_status)
    })

@app.route('/api/watchlist/rating', methods=['PUT'])
def update_movie_rating():
    data = request.json
    movie_id = data.get("movieId")
    rating = data.get("rating")

    if movie_id is None or rating is None:
        return jsonify({"error": "movieId and rating are required"}), 400

    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("SELECT movie_id FROM watchlist WHERE movie_id = ?", (movie_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    c.execute("UPDATE watchlist SET rating = ? WHERE movie_id = ?", (rating, movie_id))
    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Rating for movie {movie_id} updated to {rating}.",
        "rating": rating
    })

if __name__ == '__main__':
    init_db()
    print("Registered Flask Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.methods}")
    app.run(debug=True)
