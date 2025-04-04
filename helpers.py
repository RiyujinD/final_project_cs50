from flask import url_for, redirect, session
from functools import wraps
import secrets
import string
import time
from config import SPOTIFY_TOKEN_HEADERS, TOKEN_URL
import requests


# Decorator function to check if user login
def login_required(f):
  @wraps(f)                                         # Preserve original function metadata (name, docstrings ext..)
  def decorated_function(*args, **kwargs):          # Decorator function with any number of positional argument/ names arguments (1, 2 || brand=yamaha, model=ninja) 
    if "is_authenticated" not in session:
      return redirect(url_for("login"))      
    return f(*args, **kwargs)                       # if already login primary function is being call with it arguments if any
  return decorated_function

def generate_secure_secret(length=16):
    characters = string.ascii_letters + string.digits    
    return ''.join(secrets.choice(characters) for _ in range(length))

# Spotify Oauth token
def refresh_access_token(refresh_token):
    if not refresh_token:
        return {"error": "No refresh token found", "status": 401}

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    try: 
        response = requests.post(TOKEN_URL, data=data, headers=SPOTIFY_TOKEN_HEADERS)
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
    if not image:
        print("images not found")
    return profile



def store_user_profile():
    profile = get_user_spotifyMD()
    if profile and not profile.get("error"):
        session["spotify_id"] = profile.get("id")
        session["username"] = profile.get("display_name", "Unknown")
        images = profile.get("images", [])
        session["profile_image"] = images[0]["url"] if images else None
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

def calcul_unique_track_artist(tracks):
    track_ids = set()
    artist_ids = set()
    for item in tracks:
        track = item.get("track", {})
        track_id = track.get("id")
        if track_id:
            track_ids.add(track_id)
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if artist_id:
                artist_ids.add(artist_id)
    return track_ids, artist_ids


