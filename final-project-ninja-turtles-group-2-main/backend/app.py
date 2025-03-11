import sqlite3
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# TMDb v3 API key
TMDB_API_KEY = "03fb23d2e8ca73070c3bdb09bf268ae6"

def init_db():
    """Initializes watchlist.db if not present."""
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
    """Renders movie.html (the single-page app)."""
    return render_template("movie.html")

# ------------------------------------------------------------------------
# SEARCH (TMDb)
# ------------------------------------------------------------------------
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

# ------------------------------------------------------------------------
# MOVIE DETAILS (TMDb)
# ------------------------------------------------------------------------
@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    }

    try:
        resp_main = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}", params=params)
        resp_main.raise_for_status()
        main_data = resp_main.json()

        resp_credits = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/credits", params=params)
        resp_credits.raise_for_status()
        credits_data = resp_credits.json()

        cast_info = []
        for c in credits_data.get("cast", [])[:5]:
            cast_info.append({
                "name": c.get("name", "Unknown"),
                "character": c.get("character", "")
            })

        resp_videos = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/videos", params=params)
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
            return jsonify({"error": f"Movie with ID {movie_id} not found"}), 404
        else:
            return jsonify({"error": f"HTTP error: {str(http_err)}"}), resp_main.status_code
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to fetch movie details"}), 500

# ------------------------------------------------------------------------
# WATCHLIST - local DB
# ------------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("watchlist.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, favourite, rating FROM watchlist")
    rows = cursor.fetchall()
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

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO watchlist (movie_id) VALUES (?)", (movie_id,))
        conn.commit()
        msg = f"Movie {movie_id} added to watchlist!"
    except sqlite3.IntegrityError:
        msg = f"Movie {movie_id} is already in the watchlist."
    finally:
        conn.close()
    return jsonify({"message": msg})

@app.route('/api/watchlist', methods=['DELETE'])
def remove_from_watchlist():
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = get_db_connection()
    conn.execute("DELETE FROM watchlist WHERE movie_id = ?", (movie_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Movie {movie_id} removed from watchlist!"})

@app.route('/api/watchlist/favourite', methods=['PUT'])
def toggle_favourite():
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT favourite FROM watchlist WHERE movie_id = ?", (movie_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    new_status = 1 if row[0] == 0 else 0
    cur.execute("UPDATE watchlist SET favourite = ? WHERE movie_id = ?", (new_status, movie_id))
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

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT movie_id FROM watchlist WHERE movie_id = ?", (movie_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    cur.execute("UPDATE watchlist SET rating = ? WHERE movie_id = ?", (rating, movie_id))
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
