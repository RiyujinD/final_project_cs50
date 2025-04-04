import os
import sqlite3
import time
import requests
from flask import Flask, url_for, redirect, request, jsonify, session, render_template, g 
from flask_session import Session
from urllib.parse import urlencode

from config import CLIENT_ID, REDIRECT_URI, SPOTIFY_TOKEN_HEADERS, TOKEN_URL, AUTHORIZATION_URL, youtube
from helpers import login_required, generate_secure_secret, refresh_access_token, get_user_playlist, get_all_tracks, get_playlists_tracks, get_saved_albums_tracks, store_user_profile

app = Flask(__name__)






# Configure session
app.config["SESSION_TYPE"] = "filesystem"  # Store session data in a folder on the server  
app.config["SESSION_PERMANENT"] = False  # Session data expire when browser is closed
app.config["SESSION_FILE_DIR"] = "./.flask_session/"  # Folder to store session datas
app.config["SESSION_COOKIE_SAMESITE"] = "Lax" # Handle CSRF attacks
app.permanent_session_lifetime = 0 # Force browser to delete cache when browser is closed 
app.secret_key = os.getenv("APP_STATE")  
app.config.update({"TEMPLATES_AUTO_RELOAD": True}) # Refresh page on changes *dev*

# Set headers to prevent caching
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

Session(app) 


# Path to database, abs-path for app join with /db file
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)) , 'database.db') 

# Connect database and link it to g flask flag
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

# Close db after each request auto
@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None) 
    if db is not None:
        db.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()  
    return redirect(url_for("index")) 


@app.route("/login")
def login():

    # Initiate Spotify OAuth flow
    state = generate_secure_secret() 
    session["oauth_state"] = state 
    scope = " ".join([
        "user-read-private",
        "playlist-read-private",
        "user-modify-playback-state",
        "user-read-playback-state",
        "playlist-read-collaborative",
        "user-library-read",
        "streaming"
    ])
    auth_url = AUTHORIZATION_URL + "?" + urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "scope": scope,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "show_dialog": "True"
    })
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # Handle the Spotify OAuth callback

    code = request.args.get("code")
    if not code:
        return redirect(url_for("index", error="user_cancelled")) # If user has cancel code it's null
          
    state = request.args.get("state")
    stored_state = session.get("oauth_state")
    if not state or state != stored_state:
        return redirect(url_for("index", error="state_mismatch"))

    session.pop("oauth_state", None) # Clear the stored state from the session

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post(TOKEN_URL, data=data, headers=SPOTIFY_TOKEN_HEADERS)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch tokens", "details": response.json()})
    
    token_data = response.json()

    session["access_token"] = token_data.get("access_token")
    session["refresh_token"] = token_data.get("refresh_token")
    session["expires_in"] = token_data.get("expires_in")
    session["token_expiry"] = time.time() + token_data.get("expires_in") # Current time + expiry token time
    session["is_authenticated"] = True

    # Fetch user metadata once and store the required fields in the session
    profile = store_user_profile()
    if profile is None:
        return {"error": "Error fetching user profile"}, 500    

    spotify_id = profile.get("id")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (spotify_user_id) VALUES (?)", (spotify_id,))

    # Db close auto after each request with @app.teardown_appcontext
    db.commit()

    return redirect(url_for("selection"))

@app.route("/selection")
@login_required
def selection():

    profileUser = {
        "id": session.get("spotify_id"),
        "display_name": session.get("username"),
        "images": [{"url": session.get("profile_image")}] if session.get("profile_image") else []
    }
    if not profileUser.get("id"):
        profileUser = store_user_profile()
    if profileUser is None:
        return {"error": "Error fetching user profile"}, 500    


    playlists = get_user_playlist()
    if isinstance(playlists, dict) and playlists.get("error"):
        return playlists, 500
    if not playlists:
        return {"error": "No playlists found"}, 404
    totalPlaylists = len(playlists)

    likedSongs, total_likedSongs = get_all_tracks()
    playlistTracks, total_PLtracks = get_playlists_tracks()
    albumTracks, total_albumTracks = get_saved_albums_tracks()

    # Calculate total unique songs/artist 
    unique_track_ids = set()
    unique_artist_ids = set()

    # Process liked songs
    for item in likedSongs:
        track = item.get("track", {})
        track_id = track.get("id")
        if track_id:
            unique_track_ids.add(track_id)
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if artist_id:
                unique_artist_ids.add(artist_id)

    # Process playlist tracks
    for item in playlistTracks:
        track = item.get("track", {})
        track_id = track.get("id")
        if track_id:
            unique_track_ids.add(track_id)
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if artist_id:
                unique_artist_ids.add(artist_id)

    # Process album tracks
    for track in albumTracks:
        track_id = track.get("id")
        if track_id:
            unique_track_ids.add(track_id)
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if artist_id:
                unique_artist_ids.add(artist_id)

    TOTAL_SONGS = len(unique_track_ids)
    TOTAL_ARTISTS = len(unique_artist_ids)

    return render_template(
        "selection.html",
        profile=profileUser,
        totalPlaylists=totalPlaylists,
        total_likedSongs=total_likedSongs,
        total_PLtracks=total_PLtracks,
        total_albumTracks=total_albumTracks,
        TOTAL_SONGS=TOTAL_SONGS,
        TOTAL_ARTISTS=TOTAL_ARTISTS
    )



















@app.route("/api/playlist-images")
def get_playlist_images():
    if "refresh_token" in session:
        refresh_access_token()

    playlists = get_user_playlist()
    if isinstance(playlists, tuple):
        return playlists  
    if not playlists:
        return jsonify({"error": "No playlists found"}), 404  
    playlists_img = [
        playlist.get("images", [{}])[0].get("url", "")
        for playlist in playlists
        if playlist.get("images")
    ]
    if not playlists_img:
        return jsonify({"error": "No playlist images available"}), 404
    return jsonify({"images": playlists_img})


if __name__ == "__main__":
    app.run(debug=True)