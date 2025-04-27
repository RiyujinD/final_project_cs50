import os
import time
from flask import Flask, flash, url_for, redirect, request, jsonify, session, render_template # g 
from flask_session import Session
from urllib.parse import urlencode

from config import CLIENT_ID, REDIRECT_URI, SPOTIFY_TOKEN_HEADERS, TOKEN_URL, AUTHORIZATION_URL, youtube
from helpers import login_required, spotify_requests, generate_secure_secret, get_user_spotifyMD, unique_tracks
from helpersDB import insert_userID

app = Flask(__name__)

# Configure session
app.config["SESSION_TYPE"] = "filesystem"  # Store session data in a folder on the server  
app.config["SESSION_PERMANENT"] = False  # Session data expire when browser is closed
app.config["SESSION_FILE_DIR"] = "./.flask_session/"  # Folder to store session datas
app.config.update({"TEMPLATES_AUTO_RELOAD": True}) # Refresh page on changes *dev*
app.config["SESSION_COOKIE_SAMESITE"] = "Lax" # Handle CSRF attacks
app.permanent_session_lifetime = 0 # Force browser to delete cache when browser is closed 
app.secret_key = os.getenv("APP_STATE")  

# Set headers to prevent caching
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

Session(app) 


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
        session["is_authenticated"] = None
        return redirect(url_for("index", error="cancelled_login")) # If user has cancel code it's null
          
    state = request.args.get("state")
    stored_state = session.get("oauth_state")
    if not state or state != stored_state:
        session["is_authenticated"] = None
        return redirect(url_for("index", error="state_mismatch"))

    session.pop("oauth_state", None) # Clear the stored state from the session

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    response = spotify_requests(TOKEN_URL, "Error in callback response", 'post', data, headers=SPOTIFY_TOKEN_HEADERS)
    token_data = response.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expire_in = token_data.get("expires_in")

    if not access_token or not refresh_token or not expire_in:
        return redirect(url_for("index", error="token data not found in callback"))

    session["access_token"] = token_data.get("access_token")
    session["refresh_token"] = token_data.get("refresh_token")
    session["expires_in"] = token_data.get("expires_in")
    session["token_expiry"] = time.time() + token_data.get("expires_in") # Current time + expiry token time
    
    # Fetch user metadata and store it
    get_user_spotifyMD() # Store id and others fields in session
    spotify_id = session["spotify_id"]
    insert_userID(spotify_id)
    
    # Dict of track key by track_id
    unique_tracks()

    session["is_authenticated"] = True

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
        return {"error:" "error getting user meta data in callback"}

    total_tracks = session["total_tracks"]

    total_playlists = session['total_playlists']
    total_albums = session['total_albums']
    total_likedTracks = session['total_liked_tracks']


    return render_template(
        "selection.html",
        profile=profileUser,
        totalPlaylists=total_playlists,
        total_likedSongs=total_likedTracks,
        total_albums=total_albums,
        TOTAL_TRACKS=total_tracks,
    )

# Dynamic url pass in selection.html
@app.route("/selection/<mode>")
@login_required
def selection_mode(mode):

    valid_mods = ['favorite_song', 'song_battle', 'guess_song_info']
    if mode not in valid_mods:
        return redirect(url_for('index.html'), error="Incorrect mode pass")

    return render_template('parameter.html', mode=mode, validMods=valid_mods)

@app.route('/selection/play')
@login_required
def play():

    mode = request.args.get('m')
    valid_mods = request.args.get('vM', '').split(',')
    categories = request.args.getlist('c')
    total_of_tracks = request.args.get('t', type=int)

    if not mode or not categories or total_of_tracks is None:
        return redirect(url_for('selection_mode', mode=mode or valid_mods[0]))

    # if mode in valid_mods:

    #     # fetch tracks data from db base on categories user selected



        # return render_template(f"{mode}.html", mode=mode, categories=categories,total=total_of_tracks)


    return redirect(url_for('selection'))







# @app.route("/api/playlist-images")
# def get_playlist_images():
#     if "refresh_token" in session:
#         refresh_access_token()

#     playlists = get_playlist_tracks()
#     if isinstance(playlists, tuple):
#         return playlists  
#     if not playlists:
#         return jsonify({"error": "No playlists found"}), 404  
#     playlists_img = [
#         playlist.get("images", [{}])[0].get("url", "")
#         for playlist in playlists
#         if playlist.get("images")
#     ]
#     if not playlists_img:
#         return jsonify({"error": "No playlist images available"}), 404
#     return jsonify({"images": playlists_img})


if __name__ == "__main__":
    app.run(debug=True)

