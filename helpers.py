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
    if response.status_code != 200:
        return {f"error fetching user meta data: profile {response.status_code} - {response.text}"}
    
    profile = response.json()
    if not profile: 
        return "No profile Meta Data found"
    

    session["spotify_id"] = profile.get("id")
    if session["spotify_id"] is None:
        raise ValueError("Spotify Id not found in profile MD response")

    username = profile.get("display_name")
    if username:
        session["username"] = profile.get("display_name")
    else:
        session["username"] = "Unknown"

    images = profile.get("images", [])
    if images:
        session["profile_image"] = images[0]["url"]
    else:
         session["profile_image"] = None # Too change with a set of default img 

    return profile


def get_likedTitle_tracks():
    
    url = "https://api.spotify.com/v1/me/tracks"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    # Query parameters 
    fields = "total, next, items(track(id,name,duration_ms,artists(id,name),album(images(url))))"
    params = {
        "fields": fields
    }
    
    all_liked_title = []
    total_liked_title = None

    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("error fetching liked title")
            raise Exception(f"Error fetching liked title: {response.status_code} - {response.text}")
        
        tracksData = response.json()

        if total_liked_title is None:
            total_liked_title = tracksData.get('total', 0)

        track_item = tracksData.get("items", [])
        if track_item:
            all_liked_title.extend(track_item)

        url = tracksData.get("next")  # next page if any
    
    return all_liked_title, total_liked_title


def get_playlist_tracks():

    url = "https://api.spotify.com/v1/me/playlists"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    # Fields for playlist endpoint
    fields = "total, next, items(tracks(href,total))"
    params = {"fields": fields}

    # Fields for playlists items endpoint  
    fs = "next, total, items(id, name, track(id, name, duration_ms, artists(id, name)))"    
    par = {"fields": fs}

    all_playlists_tracks = []
    all_tracks_url = []
    total_playlists = None

    # Paginate of playlists
    while url:
        response = requests.get(url=url, headers=headers, params=params)
        if response.status_code != 200:
#           print("error in fetching playlists")
            raise Exception(f"Error fetching playlists: {response.status_code} - {response.text}")
        
        playlists_data = response.json()

        if total_playlists is None:
            total_playlists = playlists_data.get('total', 0)

        for playlist in playlists_data.get('items', []):
            tracks_url = playlist.get('tracks', {}).get('href')
            if tracks_url:
                all_tracks_url.append(tracks_url)

        url = playlists_data.get('next') # Next page of playlist

    # Loop all tracks_url playlists and store track data
    for track_url in all_tracks_url:

        # Loop for track pages
        while track_url: 
            resp = requests.get(track_url, headers=headers, params=par)
            if resp.status_code != 200:
                print("Error fetching tracks")
                raise Exception(f"Error fetching tracks: {resp.status_code} - {resp.text}")

            track_data_json = resp.json()
            track_items = track_data_json.get('items', [])
            if track_items:
                all_playlists_tracks.extend(track_items)

            track_url = track_data_json.get('next') # Next page page of tracks if any
    
    return all_playlists_tracks, total_playlists


def get_albums_tracks():
    url = "https://api.spotify.com/v1/me/albums"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    fields = "total,next,items(album(id,name,tracks(href,next,previous,items(id,name,duration_ms,artists(id,name))),images(url)))"
    params = {"fields": fields}

    all_album_tracks = []
    total_albums = 0

    # Album URL
    while url:
        response = requests.get(url=url, headers=headers, params=params)
        if response.status_code != 200:
            print("error in spotify album response")
            raise Exception(f"Error fetching albums: {response.status_code} - {response.text}")
        
        album_data = response.json()
        album_items = album_data.get('items', [])


        for album in album_items:
            album = album.get("album", {})  
            tracks = album.get("tracks", {})
            track_items = tracks.get("items", [])
            if track_items:
                all_album_tracks.extend(track_items)

                tracks_url = tracks.get('next')
                while tracks_url:
                    track_response = requests.get(tracks_url, headers=headers)
                    if track_response.status_code != 200:
                        print("error in spotify album response")
                        raise Exception(f"Error fetching albums: {track_response.status_code} - {track_response.text}")
                    
                    json_tracks = track_response.json()
                    tracks_i = json_tracks.get('items', [])
                    if tracks_i:
                        all_album_tracks.extend(tracks_i)

                    tracks_url = json_tracks.get('next')

        url = album_data.get('next') # Next page 

    total_albums = album_data.get('total', 0)
    return all_album_tracks, total_albums




#   fields = "total,next,items(album(id,name,tracks(href,next,previous,items(id,name,duration_ms,artists(id,name))),images(url)))"

# Helper to remove duplicate logic on next function 
def uniqueTA_insertion(unique_dict, query):
    for item in query:

        # Check for correct type: Dict || List
        track = None

        if "track" in item:
            track = item.get('track')
        else:
            track = item

        track_id = track.get("id")
        if track_id and track_id not in unique_dict['T']:
            unique_dict.get("T")[track_id] = track

        track_artists = track.get('artists', [])
        for artist in track_artists:
            artist_id = artist.get('id')
            if artist_id and artist_id not in unique_dict['A']:
                unique_dict.get("A")[artist_id] = artist


def unique_tracks_artists(playlists, liked_title, albums):
    unique_items = {"T": {}, "A": {}}

    # Liked title insertion
    uniqueTA_insertion(unique_items, liked_title)

    # Album insertion: 
    uniqueTA_insertion(unique_items, albums)

    # Playlists insertion: 
    uniqueTA_insertion(unique_items, playlists)
        
    return {
        "T": list(unique_items["T"].values()), 
        "A": list(unique_items["A"].values())   
    }


#  fields = items(id,name,duration_ms,artists(id,name))),images(url)))"


# def database_TA_insertion(unique_dict):

#     """ Insert the unique track / artist into database  """


#     db = get_db()
#     cursor = db.cursor()

    # print(f"Total items: {len(items)}")
    # print(f"Unique tracks: {len(unique_items.get('T', {}))}")
    # print(f"Unique artists: {len(unique_items.get('A', {}))}")   


# def store_tracks_in_db(db, tracks_data):
#     cursor = db.cursor()

#     for track in tracks_data:
#         track_id = track.get('track', {}).get('id')
#         track_name = track.get('track', {}).get('name')
#         artist_name = track.get('track', {}).get('artists', [{}])[0].get('name')  

#         cursor.execute("INSERT OR IGNORE INTO tracks (track_id, track_name, artist_name) VALUES (?, ?, ?)",
#                        (track_id, track_name, artist_name))

#     db.commit()

