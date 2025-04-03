import os
import sqlite3
import secrets
import string
import base64
import time
import requests
from flask import Flask, url_for, redirect, request, jsonify, session, render_template, g 
from flask_session import Session
from dotenv import load_dotenv
from urllib.parse import urlencode
from googleapiclient.discovery import build
from helpers import login_required

load_dotenv()

app = Flask(__name__)


# Configure session
app.config["SESSION_TYPE"] = "filesystem"  # Store session data in a folder on the server  
app.config["SESSION_PERMANENT"] = False  # Session data expire when browser is closed
app.config["SESSION_FILE_DIR"] = "./.flask_session/"  # Folder to store session datas
app.config["SESSION_COOKIE_SAMESITE"] = "Lax" # Handle CSRF attacks
app.permanent_session_lifetime = 0 # Force browser to delete cache when browser is closed 
app.secret_key = os.getenv("APP_STATE")  
app.config.update({"TEMPLATES_AUTO_RELOAD": True}) # Refresh page on changes *dev*

Session(app) 

# Load Spotify credentials 
CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  
REDIRECT_URI = os.getenv("REDIRECT_URI") # Redirect URI Spotify OAuth flow
AUTHORIZATION_URL = "https://accounts.spotify.com/authorize" 
TOKEN_URL = "https://accounts.spotify.com/api/token" # Spotify token endpoint

# Base64 encoding of the client ID and secret
auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"                 
auth_bytes = auth_str.encode("utf-8")                       # Convert to bytes
auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")  # Base64 encode and decode to string

# Load YouTube API Key from environment variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY) # Initialize YouTube API client

# Sqlite3 database Setup
appDir = os.path.abspath(os.path.dirname(__file__)) 
DATABASE = os.path.join(appDir, 'database.db') # absolute path of database.db

# Connect database and link it to g flask flag
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

# Close db after each request
@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None) 
    if db is not None:
        db.close()

# Set headers to prevent caching
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def generate_secure_secret(length=16):
    characters = string.ascii_letters + string.digits    
    return ''.join(secrets.choice(characters) for _ in range(length))

# Spotify Oauth token
def refresh_access_token(refresh_token):
    if not refresh_token:
        return {"error": "No refresh token found", "status": 401}
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    try: 
        response = requests.post(TOKEN_URL, data=data, headers=headers)
    except requests.RequestException as e:
        return {"error": "Request exception", "details": str(e), "status": 500}
    if response.status_code != 200:
        return {"error": "Failed to refresh token", "details": response.json(), "status": 500}
    
    token_data = response.json()
    session["access_token"] = token_data.get("access_token")
    session["expires_in"] = token_data.get("expires_in")
    session["token_expiry"] = time.time() + token_data.get("expires_in")
    return {
        "access_token": session["access_token"],
        "expires_in": session["expires_in"],
        "refreshed": True
    }

# Spotify headers for API calls
def get_auth_headers():

    if "access_token" not in session:
        return {"error": "User not authenticated", "status": 401}
    
    access_token = session.get("access_token")

    if time.time() > session.get("token_expiry", 0) - 5:  # Check if token need to be refresh
        token_data = refresh_access_token(session.get("refresh_token")) 
        if "error" in token_data:
            raise RuntimeError("Failed to refresh access token.")
        access_token = session.get("access_token")

    return {"Authorization": f"Bearer {access_token}"}


def get_user_spotifyMD():

    url = "https://api.spotify.com/v1/me"

    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    
    response = requests.get(url, headers=headers)
    profile = response.json()

    if not profile: 
        return profile
    

    image = profile.get("images", [])
    if image:
        print(str(image[0]))
    else:
        print("Images not found")

    return profile




def get_user_playlist():  

    # Get users playlists (in multiple 'page' if user has many)
    url = "https://api.spotify.com/v1/me/playlists"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    playlists = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200: 
            return {"error": "Failed to fetch playlists", "details": response.text}
        data = response.json()  
        playlists.extend(data.get("items", []))  # Add playlists from the current page
        url = data.get("next")  # Get the URL for the next page
    return playlists


def get_all_tracks():
    url = "https://api.spotify.com/v1/me/tracks"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        raise RuntimeError(f"Authentication error: {str(e)}")
    
    all_tracks = [] 
    tracksTotal = 0
    first_page = True

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error when fetching response tracks: {response.status_code} - {response.text}")
        tracksData = response.json()
        tracksData = response.json()
        if first_page:
            tracksTotal = tracksData.get('total', 0)
            first_page = False
            
        all_tracks.extend(tracksData.get("items", []))
        url = tracksData.get("next")
    
    print(f"ALL TRACKS: {all_tracks}")
    return all_tracks, tracksTotal


def get_playlists_tracks():
    # Get all tracks from all playlists of the user
    playlists = get_user_playlist()


    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        raise RuntimeError(f"Authentication error: {str(e)}")

    all_PLtracks = []
    total_PLtracks = 0
    first_page = True

    for playlist in playlists:
        tracks_url = playlist.get("tracks", {}).get("href")  # Get track endpoint
        if not tracks_url:
            continue  
        
        while tracks_url:
            response = requests.get(tracks_url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Error fetching tracks: {response.status_code} - {response.text}")

            data = response.json()
            if first_page:
                total_PLtracks = data.get("total", 0)
                first_page = False

            all_PLtracks.extend(data.get("items", []))  
            tracks_url = data.get("next")  

    print(f"total of tracks in playlist OOOO: {total_PLtracks}")

    return all_PLtracks, total_PLtracks


def get_saved_albums_tracks():
    url = "https://api.spotify.com/v1/me/albums"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        raise RuntimeError(f"Authentication error: {str(e)}")

    all_album_tracks = []
    total_album_tracks = 0

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error fetching albums: {response.status_code} - {response.text}")

        data = response.json()
        albums = data.get("items", [])

        for album in albums:
            album_tracks = album.get("album", {}).get("tracks", {}).get("items", [])
            all_album_tracks.extend(album_tracks)
            total_album_tracks += len(album_tracks)

        url = data.get("next")  # Pagination

    return all_album_tracks, total_album_tracks

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

    session["is_authenticated"] = True

    code = request.args.get("code")         
    state = request.args.get("state")
    stored_state = session.get("oauth_state")

    if not state or state != stored_state:
        return redirect(url_for("index", error="state_mismatch"))

    session.pop("oauth_state", None) # Clear the stored state from the session
    
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch tokens", "details": response.json()})
    
    token_data = response.json()

    session["access_token"] = token_data.get("access_token")
    session["refresh_token"] = token_data.get("refresh_token")
    session["expires_in"] = token_data.get("expires_in")
    session["token_expiry"] = time.time() + token_data.get("expires_in") # Current time + expiry token time

    return redirect(url_for("selection"))

@app.route("/selection")
@login_required
def selection():
    # Fetch user metadata
    profileUser = get_user_spotifyMD()
    if not profileUser or "error" in profileUser:
        return {"error": "User metadata couldn't be fetched"}, 500

    # Fetch playlists and check for errors
    playlists = get_user_playlist()
    if isinstance(playlists, dict) and playlists.get("error"):
        return playlists, 500
    if not playlists:
        return {"error": "No playlists found"}, 404
    totalPlaylists = len(playlists)

    # Fetch liked songs (saved tracks)
    likedSongs, total_likedSongs = get_all_tracks()

    # Fetch tracks from playlists
    playlistTracks, total_PLtracks = get_playlists_tracks()

    # Fetch tracks from saved albums
    albumTracks, total_albumTracks = get_saved_albums_tracks()

    # Calculate total unique songs by de-duplicating based on track ID.
    unique_track_ids = set()

    # Also build a set of unique artist IDs.
    unique_artist_ids = set()

    # Process liked songs (each item contains a "track" object)
    for item in likedSongs:
        track = item.get("track", {})
        track_id = track.get("id")
        if track_id:
            unique_track_ids.add(track_id)
        # Add all artist IDs from the track
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if artist_id:
                unique_artist_ids.add(artist_id)

    # Process playlist tracks (each item contains a "track" object)
    for item in playlistTracks:
        track = item.get("track", {})
        track_id = track.get("id")
        if track_id:
            unique_track_ids.add(track_id)
        # Add all artist IDs
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if artist_id:
                unique_artist_ids.add(artist_id)

    # Process album tracks (each item is a track object)
    for track in albumTracks:
        track_id = track.get("id")
        if track_id:
            unique_track_ids.add(track_id)
        # Add all artist IDs
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if artist_id:
                unique_artist_ids.add(artist_id)

    # Total unique songs and artists
    TOTAL_SONGS = len(unique_track_ids)
    TOTAL_ARTISTS = len(unique_artist_ids)

    # Print log messages
    print(f"Total Liked Songs: {total_likedSongs}")
    print(f"Total Playlist Tracks: {total_PLtracks}")
    print(f"Total Album Tracks: {total_albumTracks}")
    print(f"Total Unique Songs (TOTAL_SONGS): {TOTAL_SONGS}")
    print(f"Total Unique Artists (TOTAL_ARTISTS): {TOTAL_ARTISTS}")

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
        playlist.get("images", [{}])[0].get("url", "")  # Store first img of playlists and the url for it
        for playlist in playlists
        if playlist.get("images")  # Filter out playlists with no images
    ]
    if not playlists_img:
        return jsonify({"error": "No playlist images available"}), 404
    return jsonify({"images": playlists_img})




if __name__ == "__main__":
    app.run(debug=True)