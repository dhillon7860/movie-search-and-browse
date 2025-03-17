"""
app.py
Flask back-end for CineMate:
 - Local watchlist (SQLite) as our 'Model'
 - TMDb-based searching & details
 - Personalized recommendation system
 - Renders the single-page front-end ('movie.html') as our 'View'

Follows a light MVC pattern:
 - Model: watchlist.db + DB queries
 - View:  movie.html (+ JavaScript)
 - Controller: Flask routes bridging the model & view

Includes error handling using try/except blocks and verifies HTTP status codes.

"""

import sqlite3
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

# -------------------------------------------------------------------------
# FLASK APP SETUP
# -------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# TMDb v3 API key (replace if needed)
TMDB_API_KEY = "03fb23d2e8ca73070c3bdb09bf268ae6"

def init_db():
    """
    Initializes watchlist.db if it doesn't exist. 
    Creates columns for favourite, rating, feedback if missing.
    """
    try:
        conn = sqlite3.connect("watchlist.db")
        c = conn.cursor()

        # 1) Create table if not present
        c.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                movie_id INTEGER PRIMARY KEY,
                favourite INTEGER DEFAULT 0,
                rating INTEGER DEFAULT 0
            )
        """)

        # 2) Check if 'feedback' column exists
        c.execute("PRAGMA table_info(watchlist);")
        columns = [row[1] for row in c.fetchall()]
        if "feedback" not in columns:
            c.execute("ALTER TABLE watchlist ADD COLUMN feedback TEXT DEFAULT NULL;")
            print("[DB] Added 'feedback' column to watchlist table.")

        conn.commit()
        conn.close()
        print("[DB] Initialization completed.")
    except sqlite3.Error as db_err:
        print(f"[DB] init_db error: {db_err}")

# -------------------------------------------------------------------------
# HOME ROUTE
# -------------------------------------------------------------------------
@app.route('/')
def home():
    """
    Renders the single-page front-end (movie.html),
    which calls our API routes for searching, watchlist, etc.
    """
    return render_template("movie.html")

# -------------------------------------------------------------------------
# SEARCH & DISCOVER (TMDb)
# -------------------------------------------------------------------------
@app.route('/api/search', methods=['GET'])
def search_movies():
    """
    GET /api/search
     -> ?query=Batman
     -> &year=YYYY
     -> &genre=28
     -> &minRating=7.5
     -> &sort=popularity.desc
    If 'query' given => /search/movie
    else => /discover/movie with optional year, genre, rating, sort
    Returns JSON: {"results":[...]}
    """
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
    try:
        if q:
            # Search
            tmdb_params["query"] = q
            resp = requests.get(base_url_search, params=tmdb_params)
        else:
            # Discover
            if year:
                tmdb_params["primary_release_year"] = year
            if genre:
                tmdb_params["with_genres"] = genre
            if min_rating:
                tmdb_params["vote_average.gte"] = min_rating
            if sort:
                tmdb_params["sort_by"] = sort

            resp = requests.get(base_url_discover, params=tmdb_params)

        resp.raise_for_status()
        data = resp.json().get("results", [])

        final_results = []
        for movie in data:
            final_results.append({
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

        return jsonify({"results": final_results})

    except requests.exceptions.HTTPError as http_err:
        return jsonify({"error": f"TMDb HTTP error: {http_err}"}), resp.status_code
    except requests.exceptions.RequestException as re:
        print(f"search_movies error: {re}")
        return jsonify({"error": "Failed to fetch search results"}), 500

# -------------------------------------------------------------------------
# MOVIE DETAILS (TMDb)
# -------------------------------------------------------------------------
@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """
    GET /api/movie/<movie_id> => title, overview, date, rating, cast(5), trailer
    """
    base_url = "https://api.themoviedb.org/3"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}

    try:
        # Main info
        r_main = requests.get(f"{base_url}/movie/{movie_id}", params=params)
        r_main.raise_for_status()
        main_data = r_main.json()

        # Credits
        r_credits = requests.get(f"{base_url}/movie/{movie_id}/credits", params=params)
        r_credits.raise_for_status()
        credits = r_credits.json()
        cast_info = []
        for c in credits.get("cast", [])[:5]:
            cast_info.append({"name": c.get("name","Unknown"), "character": c.get("character","")})

        # Trailer
        r_videos = requests.get(f"{base_url}/movie/{movie_id}/videos", params=params)
        r_videos.raise_for_status()
        vid_data = r_videos.json()

        trailer_url = None
        for v in vid_data.get("results", []):
            if v.get("site") == "YouTube" and "trailer" in v.get("type","").lower():
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
            "Cast": cast_info,
            "Trailer": trailer_url
        })

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return jsonify({"error": f"Movie with ID {movie_id} not found"}), 404
        return jsonify({"error": f"HTTP error: {http_err}"}), http_err.response.status_code
    except requests.exceptions.RequestException as e:
        print(f"get_movie_details error for ID={movie_id}: {e}")
        return jsonify({"error": "Failed to fetch movie details"}), 500

# -------------------------------------------------------------------------
# RECOMMENDATIONS (TMDb 'similar' as a naive rec system)
# -------------------------------------------------------------------------
def get_similar_movies(movie_id):
    """Helper: fetch /movie/{movie_id}/similar from TMDb."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json().get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"get_similar_movies error: {e}")
        return []

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """
    GET /api/recommendations
    Implementation:
      - check watchlist DB for (movie_id, feedback)
      - if feedback = 'not_interested' => skip
      - if feedback = 'like' => priority 2.0
      - if feedback = 'rated_X' => priority = X/5
      - else default priority=1
      - gather /similar for each, merge, sort desc by priority, deduplicate
    Returns { "recommendations": [... in priority desc] }
    """
    print("[Recommendations] Generating...")

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT movie_id, feedback FROM watchlist")
        rows = c.fetchall()
        conn.close()
    except sqlite3.Error as db_err:
        print(f"get_recommendations DB error: {db_err}")
        return jsonify({"error": "Database error in recommendations"}), 500

    if not rows:
        return jsonify({"recommendations": []})

    aggregated = []
    for row in rows:
        mid = row["movie_id"]
        fb = row["feedback"]
        # skip if not in watchlist or feedback=not_interested
        if not mid or fb == "not_interested":
            continue

        # fetch similar
        sims = get_similar_movies(mid)
        for s in sims:
            s["priority"] = 1.0  # default
            if fb == "like":
                s["priority"] = 2.0
            elif fb.startswith("rated_"):
                try:
                    rating_val = int(fb.split("_")[1])
                    s["priority"] = rating_val/5.0
                except ValueError:
                    pass
            aggregated.append(s)

    # sort desc by priority
    aggregated.sort(key=lambda x: x.get("priority",1.0), reverse=True)
    # deduplicate
    used = set()
    final_list = []
    for s in aggregated:
        sid = s.get("id")
        if sid not in used:
            used.add(sid)
            final_list.append({
                "id": s["id"],
                "title": s.get("title", "N/A"),
                "release_date": s.get("release_date","Unknown"),
                "rating": s.get("vote_average","N/A"),
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{s.get('poster_path')}"
                    if s.get("poster_path")
                    else "https://via.placeholder.com/500x750?text=No+Image"
                )
            })
    return jsonify({"recommendations": final_list})

# -------------------------------------------------------------------------
# WATCHLIST (SQLITE) + FEEDBACK
# -------------------------------------------------------------------------
def get_db_connection():
    return sqlite3.connect("watchlist.db")

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """
    GET /api/watchlist => {"watchlist":[ {movie_id,favourite,rating}, ...]}
    """
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT movie_id, favourite, rating, feedback FROM watchlist")
        rows = c.fetchall()
        conn.close()

        watchlist_data = []
        for r in rows:
            watchlist_data.append({
                "movie_id": r["movie_id"],
                "favourite": bool(r["favourite"]),
                "rating": r["rating"]
            })
        return jsonify({"watchlist": watchlist_data})
    except sqlite3.Error as db_err:
        print(f"GET /api/watchlist DB error: {db_err}")
        return jsonify({"error": "Database error reading watchlist"}), 500

@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """
    POST /api/watchlist
    Body: {movieId: <int>}
    """
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO watchlist (movie_id) VALUES (?)", (movie_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Movie {movie_id} added to watchlist!"})
    except sqlite3.IntegrityError:
        return jsonify({"message": f"Movie {movie_id} is already in the watchlist."})

@app.route('/api/watchlist', methods=['DELETE'])
def remove_from_watchlist():
    """
    DELETE /api/watchlist
    Body: {movieId: <int>}
    """
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM watchlist WHERE movie_id = ?", (movie_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Movie {movie_id} removed from watchlist!"})
    except sqlite3.Error as db_err:
        return jsonify({"error": str(db_err)}), 500

@app.route('/api/watchlist/favourite', methods=['PUT'])
def toggle_favourite():
    """
    PUT /api/watchlist/favourite
    Body: {movieId: <int>}
    Toggles the favourite column.
    """
    data = request.json
    movie_id = data.get("movieId")
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT favourite FROM watchlist WHERE movie_id = ?", (movie_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Movie not found in watchlist"}), 404

        new_status = 1 if row["favourite"] == 0 else 0
        c.execute("UPDATE watchlist SET favourite = ? WHERE movie_id = ?", (new_status, movie_id))
        conn.commit()
        conn.close()

        msg = "marked as favourite" if new_status else "removed from favourites"
        return jsonify({
            "message": f"Movie {movie_id} {msg}!",
            "favourite": bool(new_status)
        })
    except sqlite3.Error as db_err:
        return jsonify({"error": str(db_err)}), 500

@app.route('/api/watchlist/rating', methods=['PUT'])
def update_movie_rating():
    """
    PUT /api/watchlist/rating
    Body: {movieId: <int>, rating: <int> (0..5?)}
    """
    data = request.json
    movie_id = data.get("movieId")
    rating = data.get("rating")
    if movie_id is None or rating is None:
        return jsonify({"error": "movieId and rating are required"}), 400

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
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
    except sqlite3.Error as db_err:
        return jsonify({"error": str(db_err)}), 500

@app.route('/api/watchlist/feedback', methods=['PUT'])
def update_feedback():
    """
    PUT /api/watchlist/feedback
    Body: { movieId: <int>, feedback: <str> }
    e.g. "like", "not_interested", "rated_3"
    """
    data = request.json
    movie_id = data.get("movieId")
    feedback = data.get("feedback")
    if not movie_id or not feedback:
        return jsonify({"error": "movieId and feedback are required"}), 400

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT movie_id FROM watchlist WHERE movie_id = ?", (movie_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Movie not found in watchlist"}), 404

        c.execute("UPDATE watchlist SET feedback = ? WHERE movie_id = ?", (feedback, movie_id))
        conn.commit()
        conn.close()

        return jsonify({
            "message": f"Feedback for movie {movie_id} updated to {feedback}.",
            "feedback": feedback
        })
    except sqlite3.Error as db_err:
        return jsonify({"error": str(db_err)}), 500

# -------------------------------------------------------------------------
# MAIN LAUNCH
# -------------------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    print("[Flask] Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule} -> {rule.methods}")
    print("[Flask] Starting server with debug=True")
    app.run(debug=True)
