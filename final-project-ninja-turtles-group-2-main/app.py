import sqlite3  #For database operations
import requests  #To make API calls to TMDB
from flask import Flask, jsonify, request, render_template  #Flask framework for handling requests and rendering pages
from flask_cors import CORS  #To enable cross-origin requests

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  #Allow cross-origin requests (useful for frontend communication)

#TMDB API Key
TMDB_API_KEY = "05886b0a875a5f5f5258bef80f28dd71"

#Connect to SQLite Database
def get_db_connection():
    """
    Establish a connection to the SQLite database and return the connection object.
    """
    conn = sqlite3.connect("watchlist.db")  # Connect to the watchlist database
    conn.row_factory = sqlite3.Row  # Allow fetching rows as dictionaries
    return conn

#Fetch Movie Details from TMDB API
@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """
    Retrieve movie details from TMDB API using the movie ID.
    Returns JSON containing title, overview, release date, rating, and poster URL.
    """
    tmdb_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    
    try:
        response = requests.get(tmdb_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        movie_data = response.json()  # Parse JSON response
        
        #Return formatted movie details
        return jsonify({
            "Title": movie_data.get("title", "N/A"),
            "Overview": movie_data.get("overview", "No synopsis available"),
            "Release Date": movie_data.get("release_date", "Unknown"),
            "Rating": movie_data.get("vote_average", "N/A"),
            "Poster URL": f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" 
                          if movie_data.get("poster_path") else "https://via.placeholder.com/500x750?text=No+Image"
        })
    except requests.exceptions.RequestException as e:
        print(f"🛑 API Error: {e}")
        return jsonify({"error": "Failed to fetch movie details"}), 500

#Search Movies by Name in TMDB API
@app.route('/api/search', methods=['GET'])
def search_movies():
    """
    Search for movies in TMDB using a query parameter.
    Returns a list of movies matching the query.
    """
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400  # Return error if no query is provided

    tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(tmdb_url)

    if response.status_code == 200:
        search_results = response.json().get("results", [])  # Extract search results

        #Format results to return only necessary details
        formatted_results = [
            {
                "id": movie["id"],
                "title": movie.get("title", "N/A"),
                "overview": movie.get("overview", "No synopsis available"),
                "release_date": movie.get("release_date", "Unknown"),
                "rating": movie.get("vote_average", "N/A"),
                "poster_url": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" 
                              if movie.get("poster_path") else "https://via.placeholder.com/500x750?text=No+Image"
            }
            for movie in search_results
        ]

        return jsonify({"results": formatted_results})  # Return the formatted movie list
    
    return jsonify({"error": "Failed to fetch search results"}), 500

#Watchlist API: Get List of Watchlisted Movies
@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """
    Retrieve the list of watchlisted movies with their favourite status.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, COALESCE(favourite, 0) FROM watchlist")  # Ensure favourite is not NULL
    movies = [{"movie_id": row[0], "favourite": bool(row[1])} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"watchlist": movies})

#Add Movie to Watchlist
@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """
    Add a movie to the watchlist if it's not already present.
    """
    data = request.json
    movie_id = data.get("movieId")
    
    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400  #Validate input

    conn = get_db_connection()
    cursor = conn.cursor()
    
    #Check if movie is already in the watchlist
    cursor.execute("SELECT movie_id FROM watchlist WHERE movie_id = ?", (movie_id,))
    if cursor.fetchone():
        message = f"Movie {movie_id} is already in the watchlist."
    else:
        #Insert new movie into watchlist
        cursor.execute("INSERT INTO watchlist (movie_id) VALUES (?)", (movie_id,))
        conn.commit()
        message = f"Movie {movie_id} added to watchlist!"

    conn.close()
    return jsonify({"message": message})  #Return success message
@app.route('/api/watchlist/favourite', methods=['PUT'])
def toggle_favourite():
    """
    Toggle the favourite status of a movie in the watchlist.
    """
    data = request.json
    movie_id = data.get("movieId")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the movie exists in the watchlist
    cursor.execute("SELECT favourite FROM watchlist WHERE movie_id = ?", (movie_id,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return jsonify({"error": "Movie not found in watchlist"}), 404  # 🔴 Your 404 Error

    # Toggle favourite status (1 = favourite, 0 = not favourite)
    new_status = 1 if result[0] == 0 else 0
    cursor.execute("UPDATE watchlist SET favourite = ? WHERE movie_id = ?", (new_status, movie_id))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Movie {movie_id} {'marked as favourite' if new_status else 'removed from favourites'}!", "favourite": bool(new_status)})
#Remove Movie from Watchlist
@app.route('/api/watchlist', methods=['DELETE'])
def remove_from_watchlist():
    """
    Remove a movie from the watchlist based on the provided movie ID.
    """
    data = request.json
    movie_id = data.get("movieId")
    
    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400  #Validate input

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE movie_id = ?", (movie_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Movie {movie_id} removed from watchlist!"})  #Return success message

#Serve the Home Page
@app.route('/')
def home():
    """
    Render the main movie search and watchlist page.
    """
    return render_template("movie.html")  #Load the HTML file from the templates folder

#Run Flask App
if __name__ == '__main__':
    app.run(debug=True)  #Start the Flask server in debug mode for easier development








