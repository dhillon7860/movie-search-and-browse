"""
app.py
Flask back-end for CineMate, including:
 - TMDb search & details
 - Local SQLite watchlist
 - Trending & recommended movies
Serves the single-page front-end at movie.html
"""

import sqlite3
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# --- 1) Your TMDb API key
TMDB_API_KEY = "03fb23d2e8ca73070c3bdb09bf268ae6"

def init_db():
    """Create or verify the watchlist.db structure."""
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

@app.route("/")
def home():
    """Serve the front-end HTML (movie.html)."""
    return render_template("movie.html")

# ----------------------------------------------------------------------
# (A) SEARCH & ADVANCED SEARCH (TMDb)
# ----------------------------------------------------------------------
@app.route("/api/search", methods=["GET"])
def search_movies():
    base_url_search = "https://api.themoviedb.org/3/search/movie"
    base_url_discover = "https://api.themoviedb.org/3/discover/movie"

    query = request.args.get("query")
    year = request.args.get("year")
    genre = request.args.get("genre")
    min_rating = request.args.get("minRating")
    sort = request.args.get("sort")

    tmdb_params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": "false"
    }

    # Basic or advanced search logic
    if query:
        tmdb_params["query"] = query
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
        final = []
        for movie in data:
            final.append({
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
        return jsonify({"results": final})
    else:
        return jsonify({"error": "Failed to fetch search results"}), 500

# ----------------------------------------------------------------------
# (B) MOVIE DETAILS (TMDb)
# ----------------------------------------------------------------------
@app.route("/api/movie/<int:movie_id>", methods=["GET"])
def get_movie_details(movie_id):
    """Fetch detailed info for a single movie ID from TMDb."""
    base_url = "https://api.themoviedb.org/3/movie"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}

    try:
        # Main info
        resp_main = requests.get(f"{base_url}/{movie_id}", params=params)
        resp_main.raise_for_status()
        main_data = resp_main.json()

        # Cast
        resp_cast = requests.get(f"{base_url}/{movie_id}/credits", params=params)
        resp_cast.raise_for_status()
        cast_data = resp_cast.json()
        cast_list = []
        for c in cast_data.get("cast", [])[:5]:
            cast_list.append({
                "name": c.get("name", "Unknown"),
                "character": c.get("character", "")
            })

        # Trailer
        resp_vid = requests.get(f"{base_url}/{movie_id}/videos", params=params)
        resp_vid.raise_for_status()
        vid_data = resp_vid.json()
        trailer_url = None
        for v in vid_data.get("results", []):
            if v.get("site") == "YouTube" and "trailer" in v.get("type", "").lower():
                trailer_url = f"https://www.youtube.com/watch?v={v['key']}"
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
            "Cast": cast_list,
            "Trailer": trailer_url
        })

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return jsonify({"error": f"Movie with ID {movie_id} not found"}), 404
        else:
            return jsonify({"error": f"HTTP error: {str(http_err)}"}), resp_main.status_code
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to fetch movie details"}), 500

# ----------------------------------------------------------------------
# (C) WATCHLIST (SQLITE)
# ----------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("watchlist.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    conn = get_db_connection()
    rows = conn.execute("SELECT movie_id, favourite, rating FROM watchlist").fetchall()
    conn.close()

    output = []
    for r in rows:
        output.append({
            "movie_id": r[0],
            "favourite": bool(r[1]),
            "rating": r[2]
        })
    return jsonify({"watchlist": output})

@app.route("/api/watchlist", methods=["POST"])
def add_to_watchlist():
    data = request.json
    m_id = data.get("movieId")
    if not m_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO watchlist (movie_id) VALUES (?)", (m_id,))
        conn.commit()
        msg = f"Movie {m_id} added to watchlist!"
    except sqlite3.IntegrityError:
        msg = f"Movie {m_id} is already in the watchlist."
    conn.close()
    return jsonify({"message": msg})

@app.route("/api/watchlist", methods=["DELETE"])
def remove_from_watchlist():
    data = request.json
    m_id = data.get("movieId")
    if not m_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = get_db_connection()
    conn.execute("DELETE FROM watchlist WHERE movie_id = ?", (m_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Movie {m_id} removed from watchlist!"})

@app.route("/api/watchlist/favourite", methods=["PUT"])
def toggle_favourite():
    data = request.json
    m_id = data.get("movieId")
    if not m_id:
        return jsonify({"error": "movieId is required"}), 400

    conn = get_db_connection()
    row = conn.execute(
        "SELECT favourite FROM watchlist WHERE movie_id = ?",
        (m_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    new_val = 1 if row[0] == 0 else 0
    conn.execute(
        "UPDATE watchlist SET favourite = ? WHERE movie_id = ?",
        (new_val, m_id)
    )
    conn.commit()
    conn.close()

    msg = "marked as favourite" if new_val else "removed from favourites"
    return jsonify({
        "message": f"Movie {m_id} {msg}!",
        "favourite": bool(new_val)
    })

@app.route("/api/watchlist/rating", methods=["PUT"])
def update_movie_rating():
    data = request.json
    m_id = data.get("movieId")
    rating = data.get("rating")

    if m_id is None or rating is None:
        return jsonify({"error": "movieId and rating are required"}), 400

    conn = get_db_connection()
    row = conn.execute(
        "SELECT movie_id FROM watchlist WHERE movie_id = ?",
        (m_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    conn.execute(
        "UPDATE watchlist SET rating = ? WHERE movie_id = ?",
        (rating, m_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Rating for movie {m_id} updated to {rating}.",
        "rating": rating
    })

# ----------------------------------------------------------------------
# (D) PERSONALIZED RECOMMENDATIONS (MOVIES ONLY)
#     Calls /movie/<id>/recommendations for each watchlist item
# ----------------------------------------------------------------------
@app.route("/api/recommendations", methods=["GET"])
def get_personal_recommendations():
    conn = get_db_connection()
    rows = conn.execute("SELECT movie_id FROM watchlist").fetchall()
    conn.close()

    rec_map = {}
    for r in rows:
        m_id = r["movie_id"]
        url = f"https://api.themoviedb.org/3/movie/{m_id}/recommendations"
        params = {"api_key": TMDB_API_KEY, "language": "en-US"}

        try:
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json().get("results", [])
                for rec in data:
                    rid = rec["id"]
                    rec_map[rid] = {
                        "id": rid,
                        "title": rec.get("title", "N/A"),
                        "overview": rec.get("overview", ""),
                        "release_date": rec.get("release_date", ""),
                        "rating": rec.get("vote_average", 0),
                        "poster_url": (
                            f"https://image.tmdb.org/t/p/w500{rec['poster_path']}"
                            if rec.get("poster_path")
                            else "https://via.placeholder.com/500x750?text=No+Image"
                        )
                    }
            else:
                print(f"Recommendations failed for {m_id}, status {resp.status_code}")

        except requests.exceptions.RequestException as e:
            print("Error fetching recs for movie_id=", m_id, "->", e)

    # Convert dict to list, optionally limit
    final_list = list(rec_map.values())[:20]
    return jsonify({"results": final_list})

if __name__ == "__main__":
    init_db()
    print("Registered Flask Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.methods}")
    app.run(debug=True)
