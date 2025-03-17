
---

```markdown
# INFR 3200 U - Intro to DevOps & Infrastructure Automation (Phase 1 Deliverable)
### By: Bilal Dhillon (100701650), Naman Patel (ID?), Fatima Khan (100812028), Zuhaib Shafi (ID?), Matthew Allicock (ID?)
**Team Name**: Ninja Turtles (Group 2)

---

## Table of Contents
- [Introduction](#introduction)
- [5 Implemented Features](#5-implemented-features)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Set Up a Virtual Environment](#2-set-up-a-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure the API Key](#4-configure-the-api-key)
  - [5. Initialize the Database](#5-initialize-the-database)
  - [6. Run the Application](#6-run-the-application)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Contributors](#contributors)
- [License](#license)

---

## Introduction
**CineMate** is a fully web-based **movie discovery and watchlist platform**.  
It provides a **graphical user interface (GUI)**—meaning you **don’t** need to run Python scripts directly in the terminal to use it. Instead, just open your browser to access all the features.  

We also employ a **lightweight MVC design**:  
- **Model**: `watchlist.db` plus database-access code in `app.py`.  
- **View**: Our single-page `movie.html`, styled with HTML/CSS, plus interactive JavaScript (`movie-details.js`).  
- **Controller**: Flask route functions in `app.py` that bridge data (Model) and the front-end (View).

---

## 5 Implemented Features
This phase of the project implements (and demonstrates) **five** primary features:

1. **Search & Browse**  
   - Users can perform basic or advanced searches to find movies by title, year, genre, and sorting options.

2. **Movie Details**  
   - Clicking “View Details” shows an in-depth page with cast info, release date, rating, trailer link, etc.

3. **Watchlist Management**  
   - Users can add or remove any movie from their personal watchlist.

4. **User Ratings & Favorites**  
   - Each watchlist item can be rated from 1–5 stars and toggled as a favorite.

5. **Personalized Recommendations**  
   - The system suggests recommended movies based on “like,” “not interested,” or “rated_X” feedback.

*Future expansions*, such as streaming availability or watch-party features, are planned but **not** in this phase.

---

## Installation
Below are step-by-step instructions to install and run CineMate. All commands assume a standard Python 3 environment.

### 1. Clone the Repository
```bash
git clone https://github.com/Ontario-Tech-NITS/final-project-ninja-turtles-group-2.git
cd final-project-ninja-turtles-group-2
```

### 2. Set Up a Virtual Environment
A **virtual environment** is recommended to keep dependencies isolated:

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
You should see `(venv)` in your terminal prompt once activated.

### 3. Install Dependencies
With the virtual environment active, install required Python packages:
```bash
pip install -r requirements.txt
```
This will install Flask, Requests, and any other needed libraries.

### 4. Configure the API Key
We rely on the **TMDb API** for movie data. Obtain a free key from [TMDb](https://www.themoviedb.org/settings/api).

In **`app.py`**, find the line:
```python
TMDB_API_KEY = "03fb23d2e8ca73070c3bdb09bf268ae6"
```
…and replace the string if needed with your own. Alternatively, set an environment variable or `.env` approach.

### 5. Initialize the Database
**CineMate** uses a local **SQLite** database to store watchlist information.

1. Ensure you are in the project root.
2. Start the Flask server (see below). The `init_db()` function in `app.py` will create **`watchlist.db`** automatically if it doesn’t exist.
3. Confirm that a `watchlist.db` file appears in your project folder.

### 6. Run the Application
Finally, launch CineMate:
```bash
python app.py
```
Flask will start on `http://127.0.0.1:5000` by default.  
Open that in your **web browser** to explore the app GUI.

---

## Usage Guide

1. **Search for Movies**  
   - On the homepage, enter a title in the search bar. Press **Search** to see matching results.

2. **View Movie Details**  
   - For any movie, click **View Details** to see cast, rating, trailer link, etc.

3. **Add to Watchlist**  
   - In the search/trending results, click **Add to Watchlist** to store it locally.  
   - Open **My Watchlist** to see all saved items.

4. **Rate Movies**  
   - Inside your watchlist or in the detail page, pick a star rating (1–5). The rating is stored in the local DB.

5. **Browse Personalized Recommendations**  
   - Under **Recommendations**, the system suggests relevant titles based on your likes or star ratings.  
   - If you mark “not interested,” it excludes those from recs.

**Note**: The system is a single-page UI. By toggling the watchlist or advanced search sections, you can remain on the same page but see different features.

---

## Project Structure

```
final-project-ninja-turtles-group-2/
├── app.py               # Flask back-end (Controller + Model)
├── watchlist.db         # Created at runtime; local SQLite DB
├── requirements.txt     # Python dependencies
├── README.md            # This document
├── templates/
│    └── movie.html      # Main front-end "View" (HTML) 
└── static/
     └── js/
         └── movie-details.js  # JavaScript for front-end interactions
```

---

## Technologies Used
- **Python 3** + **Flask** for the back-end
- **SQLite** for watchlist and rating storage
- **JavaScript, HTML, CSS** for the web-based GUI
- **TMDb API** for movie search/details
- **Git/GitHub** for version control
- **MVC**-inspired structure (light)

---

## Contributors

| Name           | Role(s)                                                     | GitHub                               |
| -------------- | ----------------------------------------------------------- | ------------------------------------ |
| **Fatima Khan**   | Watchlist Management, Recorder/Developer                   | [@FatimaK03](https://github.com/fatimak03) |
| **Matthew Allicock**   | Movie Details, Scrum Leader/Developer                   | [@MatthewA15](https://github.com/MatthewA15) |
| **Bilal Dhillon** | Search & Browse, Advanced Filtering/Sorting, Product Owner/Lead Tester | [@dhillon7860](https://github.com/dhillon7860) |
| **Naman Patel**   | User Ratings & Favorites, Project Manager/Developer        | [@naman4257](https://github.com/naman4257) |
| **Zuhaib Shafi**  | Personalized Recommendations, UX/UI Designer/Developer     | [@ZuhaibShafi03](https://github.com/ZuhaibShafi03) |

---

## License
All code in this repository is for academic demonstration purposes.  
© 2025 The Ninja Turtles (Group 2). All rights reserved.

```

---