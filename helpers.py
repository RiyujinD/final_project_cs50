from flask import url_for, redirect, session
from functools import wraps
import secrets
import string
import time
import requests
from config import SPOTIFY_TOKEN_HEADERS, TOKEN_URL



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
        return f"error: {response.status_code} - {response.text}"

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

    # Build parameters that gets query 
    fields = "total,items(tracks(items(track(id,name,duration_ms,artists(id,name),images)))),next"
    params = {
        "fields": fields
    }
    
    all_playlists_tracks = []
    first_page = True
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error when fetching response tracks: {response.status_code} - {response.text}")
        
        playlistsData = response.json()
        if first_page:
            session["total_playlist"] = playlistsData.get("total", 0)
            first_page = False
        all_playlists_tracks.extend(playlistsData.get("items", []))  # Add playlists from the current page
        url = playlistsData.get("next")  # Get the URL for the next page

    print(f"ALL PLAYLIST TRACKS AAAAAA: {all_playlists_tracks}")
    return all_playlists_tracks


def _liked_title():
    # Get users playlists (in multiple 'page' if user has many)
    url = "https://api.spotify.com/v1/me/tracks"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    # Query parameters 
    fields = "items(track(id,name,duration_ms,artist(id,name),album(images(url)))),next"
    params = {
        "fields": fields
    }
    
    all_liked_title = [] 
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error when fetching response tracks: {response.status_code} - {response.text}")
        tracksData = response.json()
        if 'error' in tracksData:
            return {"error": "Error in liked song response", "details": tracksData.error}

        all_liked_title.extend(tracksData.get("items", []))
        url = tracksData.get("next")  # next page if any
    
    print(f"ALL TRACKS IIIIIII: {all_liked_title}")
    return all_liked_title



def get_saved_albums_tracks():
    url = "https://api.spotify.com/v1/me/albums"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    # Query parameters
    fields = "items(name,tracks(items(track(id,name,duration_ms,artists(id,name)))),images(url)),next"
    params = {
        "fields": fields
    }

    all_album_tracks = []
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching albums: {response.status_code} - {response.text}")
        albumData = response.json()
        if 'error' in albumData:
            return {"error": "Error in liked song response", "details": albumData.error}

        all_album_tracks.extend(albumData.get("items", []))
        url = all_album_tracks.get("next")  # Pagination

    print(f"ALL ALBUM TRACKS OOOOO: {all_album_tracks}")
    return all_album_tracks




def unique_tracks_artists(playlists, liked_title, albums):
    unique_items = {
        "T": {},  # Using a dictionary for unique tracks (track_id -> track_item)
        "A": {}   # Using a dictionary for unique artists (artist_id -> artist_item)
    }

    for playlist in playlists:
        for item in playlist.get("items", []):
            track = item.get("track")
            if track:
                track_id = track.get("id")
                track_artists = track.get("artists", [])
                if track_id not in unique_items["T"]:
                    unique_items["T"][track_id] = item  

                for artist in track_artists:
                    artist_id = artist.get("id")
                    if artist_id not in unique_items["A"]:
                        unique_items["A"][artist_id] = artist  

    for item in liked_title:
        track = item.get("track")
        if track:
            track_id = track.get("id")
            track_artists = track.get("artists", [])
            if track_id not in unique_items["T"]:
                unique_items["T"][track_id] = item

            for artist in track_artists:
                artist_id = artist.get("id")
                if artist_id not in unique_items["A"]:
                    unique_items["A"][artist_id] = artist


    for item in albums:
        for track in item.get("tracks", []):  
            track_id = track.get("id")
            track_artists = track.get("artists", [])
            if track_id not in unique_items["T"]:
                unique_items["T"][track_id] = item 

            for artist in track_artists:
                artist_id = artist.get("id")
                if artist_id not in unique_items["A"]:
                    unique_items["A"][artist_id] = artist

    return {
        "T": list(unique_items["T"].values()), 
        "A": list(unique_items["A"].values())   
    }


        


# def get_playlists_tracks():
#     # Get all tracks from all playlists of the user
#     playlists = 

#     try:
#         headers = get_auth_headers()
#     except RuntimeError as e:
#         raise RuntimeError(f"Authentication error: {str(e)}")



#     all_PLtracks = []
#     for playlist in playlists:
#         tracks_url = playlist.get("tracks", {}).get("href")  # Get track endpoint
#         if not tracks_url:
#             continue  
        
#         while tracks_url:
#             response = requests.get(tracks_url, headers=headers)
#             if response.status_code != 200:
#                 raise Exception(f"Error fetching tracks: {response.status_code} - {response.text}")

#             data = response.json()


#             all_PLtracks.extend(data.get("items", []))  
#             tracks_url = data.get("next")  


#   #  cursor.execute("INSERT INTO user_tracks (spotify_user_id, track_id) VALUES ")

#     return all_PLtracks



# def store_tracks_in_db(db, tracks_data):
#     cursor = db.cursor()

#     for track in tracks_data:
#         track_id = track.get('track', {}).get('id')
#         track_name = track.get('track', {}).get('name')
#         artist_name = track.get('track', {}).get('artists', [{}])[0].get('name')  

#         cursor.execute("INSERT OR IGNORE INTO tracks (track_id, track_name, artist_name) VALUES (?, ?, ?)",
#                        (track_id, track_name, artist_name))

#     db.commit()

