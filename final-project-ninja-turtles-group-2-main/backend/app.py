import sqlite3          # For connecting to our local SQLite database
import requests         # For making requests to TMDB
from flask import Flask, jsonify, request, render_template  # Flask for building our web server
from flask_cors import CORS                                  # For allowing cross-origin requests

# We create an instance of Flask, specifying where to find templates and static files
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # This allows different domains or ports to talk to our Flask server

# This is our personal API key for TMDB (The Movie Database)
TMDB_API_KEY = "05886b0a875a5f5f5258bef80f28dd71"

def get_db_connection():
    """
    Opens a connection to the local 'watchlist.db' file.
    We set 'row_factory' so each fetched row acts more like a dictionary,
    which can make retrieving column data a bit more convenient.
    """
    conn = sqlite3.connect("watchlist.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """
    Retrieves detailed information about a movie from TMDB using the provided numeric ID.
    If the ID doesn't exist in TMDB, you'll receive a "Movie with ID X not found" message.
    Otherwise, we'll return a JSON object that contains data like the title, overview,
    release date, average rating, and a link to the poster image if available.
    """
    # We build the URL for TMDB's "movie details" endpoint using the movie ID
    tmdb_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"

    try:
        # Make a GET request to TMDB
        response = requests.get(tmdb_url)
        # If the status code indicates an error (4xx or 5xx), raise_for_status() will throw an exception
        response.raise_for_status()
        # Convert the response to JSON so we can read the movie details
        movie_data = response.json()

        # Return specific fields from the movie data as JSON
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
        # If the status code is 404, we specifically say the movie was not found.
        # For other types of errors, we pass along the HTTP error message and status code.
        if http_err.response.status_code == 404:
            return jsonify({"error": f"Movie with ID {movie_id} not found on TMDB"}), 404
        else:
            return jsonify({"error": f"TMDB HTTP error: {str(http_err)}"}), http_err.response.status_code
    except requests.exceptions.RequestException as e:
        # This block handles other network-related issues (like timeouts or DNS problems)
        print(f"API Error: {e}")
        return jsonify({"error": "Failed to fetch movie details"}), 500

@app.route('/api/search', methods=['GET'])
def search_movies():
    """
    Allows you to search TMDB for movies that match a text query.
    You must include a 'query' parameter in the URL, e.g. /api/search?query=Matrix
    The endpoint returns a list of matching movies along with basic info like title and poster image.
    """
    # We look for the 'query' parameter in the request
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Construct the TMDB URL to search by movie title
    tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(tmdb_url)

    # If TMDB responds with a success code (200), we parse and return relevant data for each movie
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

    # If TMDB doesn't return a 200 status code, we let the user know we couldn't complete the search
    return jsonify({"error": "Failed to fetch search results"}), 500

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """
    Returns the list of movies currently in our watchlist, along with a boolean
    indicating whether each movie is marked as a favorite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, COALESCE(favourite, 0) FROM watchlist")
    # Build a list of dictionaries that describes each watchlist entry
    movies = [{"movie_id": row[0], "favourite": bool(row[1])} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"watchlist": movies})

@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """
    Adds a movie to our watchlist, given its ID in the JSON body.
    If the movie is already in the database, we don't add it again,
    but we'll respond with a message saying it's already there.
    """
    data = request.json
    movie_id = data.get("movieId")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the movie is already in the watchlist
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
    Removes a movie from our watchlist, given its ID in the JSON body.
    If it's not in the watchlist, there's no error— we just delete nothing.
    Either way, we'll confirm that the movie was removed.
    """
    data = request.json
    movie_id = data.get("movieId")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    # Delete the entry, if it exists
    cursor.execute("DELETE FROM watchlist WHERE movie_id = ?", (movie_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Movie {movie_id} removed from watchlist!"})

@app.route('/api/watchlist/favourite', methods=['PUT'])
def toggle_favourite():
    """
    Toggles a movie's 'favourite' status in the watchlist.
    If the movie isn't in the watchlist at all, we'll respond with a 404 error.
    Otherwise, we flip the 'favourite' bit from 0 to 1 or from 1 to 0.
    """
    data = request.json
    movie_id = data.get("movieId")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    # Get the current favourite status (0 or 1) for this movie
    cursor.execute("SELECT favourite FROM watchlist WHERE movie_id = ?", (movie_id,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404

    # Flip the current status
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
    Renders our main HTML page (movie.html). This is where you might have
    your frontend code for searching movies, managing your watchlist, etc.
    """
    return render_template("movie.html")

if __name__ == '__main__':
    # Print out the registered routes so you can see what's available
    print("Registered Flask Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.methods}")
    # Start the Flask server in debug mode, which automatically reloads on changes
    app.run(debug=True)
