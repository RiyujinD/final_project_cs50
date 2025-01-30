import os
import secrets
import string
import base64
import time
from flask import Flask, url_for, redirect, request, jsonify, session, render_template
from flask_session import Session
from dotenv import load_dotenv
from urllib.parse import urlencode
import requests
# from flask_cors import CORS
    
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# CORS(app)

# Configure session
app.config["SESSION_TYPE"] = "filesystem"  # Store session data in a folder on the server  
app.config["SESSION_PERMANENT"] = False  # Session data expire when browser is closed
app.config["SESSION_FILE_DIR"] = "./.flask_session/"  # Folder to store session data
app.permanent_session_lifetime = 0 # Force browser to delete cache when browser is closed
app.secret_key = os.getenv("APP_STATE", secrets.token_hex(32))  # Secret key for session data
Session(app) 

app.config.update({
    "TEMPLATES_AUTO_RELOAD": True,  # Reload templates when they are changed
})

# Load storedcredentials and URLs from .env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
AUTHORIZATION_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Base64 encoding of the client ID and secret
auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"                   # Combine client_id and client_secret
auth_bytes = auth_str.encode("utf-8")                       # Convert to bytes
auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")  # Base64 encode and decode to string


def generate_secure_secret(length=16):
    """ Generate a random state string for security """
    # Define the characters to use (A-Z, a-z, 0-9)
    characters = string.ascii_letters + string.digits
    # Randomly choose char to use
    return ''.join(secrets.choice(characters) for _ in range(length))

def refresh_access_token():
    """ Refresh the access token when it has expired """
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return {"error": "No refresh token found", "status": 401}

    auth_headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    auth_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(TOKEN_URL, data=auth_data, headers=auth_headers)
    if response.status_code != 200:
        return {"error": "Failed to refresh token", "details": response.json(), "status": 500}
    
    token_data = response.json()
    session["access_token"] = token_data.get("access_token")
    session["expires_in"] = token_data.get("expires_in")
    session["token_expiry"] = time.time() + token_data.get("expires_in") # time.time() give 'the current time' + the expiry time of token, later we check if the current time has pass this time
    return {"access_token": session["access_token"], "expires_in": session["expires_in"], "refreshed": True}

        

def get_auth_headers():
    """ Build the headers for API calls (spotify)"""

    # Check if token need to be refresh before making the call
    if time.time() > session.get("token_expiry", 0):
        token_data = refresh_access_token() # Token has expired
        if "error" in token_data:
            raise RuntimeError("Failed to refresh access token.")
        
    access_token = session.get("access_token")
    if not access_token:
        raise RuntimeError("Access token not available.")

    return {
        "Authorization": f"Bearer {access_token}"
    }


def get_user_playlist():
    """ Get users playlists (in multiple 'page' if user has many)"""
    
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


@app.route("/")
def main():    
    # Check  if user is authenticated if so redirect to selection page directly
    if session.get("is_authenticated", False): 
        return redirect(url_for("selection"))
    else:
        return redirect(url_for("index"))
    
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/logout")
def logout():
    """ Clear session """
    session.clear()  # Clear the entire session
    session["is_authenticated"] = False # Set the user as not authenticated
    return redirect(url_for("index"))  # Redirect to the homepage


@app.route("/login")
def login():
    """Initiate Spotify OAuth flow."""
    
    state = generate_secure_secret() 
    session["oauth_state"] = state # Store the state generate above in the session 
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
    """Handle the Spotify OAuth callback."""

    # Get the auth code and state from uri
    code = request.args.get("code")
    state = request.args.get("state")
    stored_state = session.get("oauth_state")

    # Check if state match stored one and if state not NULL
    if not state or state != stored_state:
        return redirect(url_for("index", error="state_mismatch"))

    # Clear the stored state from the session
    session.pop("oauth_state", None)
    
    auth_headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    auth_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    # Make the request for a token to spotify's token endpoint
    response = requests.post(TOKEN_URL, data=auth_data, headers=auth_headers)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch tokens", "details": response.json()})
    
    token_data = response.json()
    session["access_token"] = token_data.get("access_token")
    session["refresh_token"] = token_data.get("refresh_token")
    session["expires_in"] = token_data.get("expires_in")
    session["token_expiry"] = time.time() + token_data.get("expires_in") # Current time + expiry token time

    # Set the user as authenticated
    session["is_authenticated"] = True

    return redirect(url_for("selection"))


@app.route("/selection")
def selection():
    """ Return playlists/songs of the user for selection """

    playlists = get_user_playlist()
    if isinstance(playlists, tuple):  
        return playlists

    if not playlists:
        return {"error": "No playlists found"}
    
    # Extract all playlist images
    playlist_images = []
    for playlist in playlists:
        images = playlist.get("images", [])
        if images:
            # Append the URL of the first image for each playlist
            playlist_images.append(images[0].get("url", ""))

    if not playlist_images:
        return {"error": "No playlist images available"}

    # Pass all playlist images to the template
    return render_template("selection.html", playlist_images=playlist_images)


if __name__ == "__main__":
    app.run(debug=True)