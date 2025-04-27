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


# Custom exception for handling API errors with retries
class callError(Exception):
    def __init__(self, message, status_code, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

# inheritance exception class to handle auhentification and token refresh status
class NotAuthenticated(Exception):
    pass
class TokenRefreshFailed(Exception):
    pass

# Handle spotify refresh tokens
def refresh_access_token(refresh_token):
    if refresh_token != session["refresh_token"]:
        raise NotAuthenticated("User not authenticated, error on refresh_access_token")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    try: 
        response = requests.post(TOKEN_URL, data=data, headers=SPOTIFY_TOKEN_HEADERS)
    except requests.RequestException as e:
        return {"error": "Request exception", "details": str(e), "status": 500}
    if response.status_code != 200:
        raise TokenRefreshFailed("Failed to refresh token")

    
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
        raise NotAuthenticated("User not authenticated, error on refresh_access_token")
    
    access_token = session.get("access_token")

    if time.time() > session.get("token_expiry", 0) - 20:  # Check if token need to be refresh
        token_data = refresh_access_token(session.get("refresh_token")) 
        if "error" in token_data:
            raise RuntimeError("Failed to refresh access token.")
        access_token = session.get("access_token")

    return {"Authorization": f"Bearer {access_token}"}

# Helper for next function to check method value
def requests_method(url, headers, method, params):
    if method == "get":
        return requests.get(url, headers=headers, params=params)
    elif method == "post":
        return requests.post(url, headers=headers, data=params)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


# Handle spotify api calls
def spotify_requests(url, api_error, method, params, headers=None, rate_info=None):
    if rate_info is None:
        rate_info = {}

    method = method.strip().lower()

    try:
        response = requests_method(url, headers, method, params)
    except requests.RequestException as network_error:
        raise callError(f"{api_error}: network error: {network_error}", status_code=503) from network_error # Converting into my own error handler but keeping it in network_code class

    # Handle rate limit (status code 429)
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))  # Default to 10 seconds if not provided
        print(f"Rate limit reached. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        

        try:
            response = requests_method(url, headers, method, params)
        except requests.RequestException as network_error:
            raise callError(f"{api_error}: network error: {network_error}", status_code=503) from network_error # Converting into my own error handler but keeping it in network_code class
        
        # If still rate-limited after retry, raise an error
        if response.status_code == 429:
            raise callError("Spotify rate limit reached again", response.status_code, retry_after)

    # Handle rate limit information (X-RateLimit headers)
    if "X-RateLimit-Limit" in response.headers:
        try:
            rate_info["limit_calls"] = int(response.headers.get("X-RateLimit-Limit", 0))
            rate_info["remaining_calls"] = int(response.headers.get("X-RateLimit-Remaining", 0))
            rate_info["reset"] = int(response.headers.get("X-RateLimit-Reset", 0))

            remaining = rate_info["remaining_calls"]
            limit = rate_info["limit_calls"]
            warning_threshold = (remaining / limit) * 100 if limit else 100
            current_time = time.time()
            reset_time = int(rate_info["reset"] - current_time)

            # Warning if remaining calls are less than 15% of limit
            if warning_threshold < 15:
                print(f"Warning: Only {remaining} requests remaining. Rate limit will reset in {reset_time}s.")

        except (ValueError, TypeError) as e:
            print(f"Rate limit header error: {e}")

    # Handle non-200 status codes
    if response.status_code != 200:
        raise callError(f"{api_error}: {response.status_code} - {response.text}", response.status_code)

    return response

def get_user_spotifyMD():
    if "spotify_id" in session:
        return

    url = "https://api.spotify.com/v1/me"
    headers = get_auth_headers()
    response = spotify_requests(url, "error fetching user meta data: profile",  "get", params=None, headers=headers)


    profile = response.json()
    if not profile: 
        return "No profile Meta Data found"
    
    # Store user data in the session
    session["spotify_id"] = profile.get("id")
    if session["spotify_id"] is None:
        raise ValueError("Spotify Id not found in profile MD response")

    username = profile.get("display_name")
    if username:
        session["username"] = username
    else:
        session["username"] = "Unknown"

    images = profile.get("images", [])
    if images:
        session["profile_image"] = images[0]["url"]
    else:
         session["profile_image"] = None # Too change with a set of default img 

    return

    
def get_saved_tracks():
    
    url = "https://api.spotify.com/v1/me/tracks"
    headers = get_auth_headers()
    
    # Query parameters 
    fields = "total, next, items(track(id,name,duration_ms,artists,album(images(url))))"
    params = {"fields": fields}
 
    all_liked_title = []
    total_liked_title = None

    while url:
        response = spotify_requests(url, "error fetching liked title tracks" ,"get", params=params, headers=headers)
        tracksData = response.json()

        if total_liked_title is None:
            total_liked_title = tracksData.get("total", 0)

        track_items = tracksData.get("items", [])
        for item in track_items:

            track = item.get("track")
            if not track:
                continue

            all_liked_title.append(track)

        url = tracksData.get("next")  # next page if any
    
    session["total_liked_tracks"] = total_liked_title
    return all_liked_title


def get_playlist_tracks():
    url = "https://api.spotify.com/v1/me/playlists"
    headers = get_auth_headers()

    # Fields for playlist endpoint
    fields = "total, next, items(id, name, tracks(href,total))"
    params = {"fields": fields}

    # Fields for playlists items endpoint  
    fs = "next, total, items(track(id, name, duration_ms, artists))"
    par = {"fields": fs}

    all_playlists_tracks = []
    total_playlists = None

    # Page through all playlists
    while url:
        response = spotify_requests(url, "Error fetching playlists", "get", params=params, headers=headers)
        playlists_data = response.json()

        if total_playlists is None:
            total_playlists = playlists_data.get("total", 0)

        for playlist in playlists_data.get("items", []):
            playlist_id = playlist.get("id")
            playlist_name = playlist.get("name")
            track_url = playlist.get("tracks", {}).get("href")

            # Page through tracks of this playlist
            while track_url:
                resp = spotify_requests(track_url, "Error fetching playlist tracks", "get", params=par, headers=headers)
                track_data_json = resp.json()
                track_items = track_data_json.get("items", [])

                for item in track_items:
                    track = item.get("track")
                    if not track:
                        continue
                    
                    track["playlist_id"] = playlist_id
                    track["playlist_name"] = playlist_name

                    all_playlists_tracks.append(track)

                track_url = track_data_json.get("next")

        # Move to next page of playlists
        url = playlists_data.get("next")

    session["total_playlists"] = total_playlists
    return all_playlists_tracks


def get_albums_tracks():
    url = "https://api.spotify.com/v1/me/albums"
    headers = get_auth_headers()

    fields = "total,next,items(album(id,name,tracks(href,next,previous,items(id,name,duration_ms,artists)),images(url)))"
    params = {"fields": fields}

    all_album_tracks = []
    total_albums = None

    # Paginate through albums
    while url:
        response = spotify_requests(url, "Error fetching albums", "get", params=params, headers=headers)
        album_data = response.json()

        if total_albums is None:
            total_albums = album_data.get("total", 0)

        for album_item in album_data.get("items", []):
            album = album_item.get("album", {})
            album_id = album.get("id")
            album_name = album.get("name")
            tracks = album.get("tracks", {})
            track_items = tracks.get("items", [])

            # Loop all tracks of albums (first page)
            for track in track_items:
                track["album_id"] = album_id
                track["album_name"] = album_name

            all_album_tracks.extend(track_items)

            # Paginate through additional track pages
            next_tracks_url = tracks.get("next")
            while next_tracks_url:
                track_response = spotify_requests(next_tracks_url, "Error fetching album tracks", "get", headers=headers)
                json_tracks = track_response.json()
                page_items = json_tracks.get("items", [])

                for track in page_items:
                    track["album_id"] = album_id
                    track["album_name"] = album_name

                    track.setdefault(
                        "categories",
                        {"playlists": [], "albums": [], "is_liked": False}
                    )
                    track["categories"]["albums"].append({
                        "id": track["album_id"],
                        "name": track["album_name"]
                    })

                    all_album_tracks.append(track)

                next_tracks_url = json_tracks.get("next")

        # Next page of albums
        url = album_data.get("next")

    session["total_albums"] = total_albums
    return all_album_tracks


# Helper to next function: Adding unique tracks and they're source
def unique_track_insertion(unique_dict, tracks, source_type):
    """
    - unique_dict: {"T": {}}
    - tracks:   List[track_dict]
    - source_type:   one of "liked_title", "albums", "playlists"
    """
    for track in tracks:
        track_id = track.get("id")
        if not track_id:
            raise ValueError(f"Track {track!r}: missing id in uniqueTA insertion.")

        if track_id not in unique_dict["T"]:

            # Create source dict if not exists
            track.setdefault("source", {
                "playlists": {},
                "albums": {},
                "is_liked": False,
            })
            unique_dict["T"][track_id] = track  # Insert track with key being the track id

        # Get the stored track and its source dict
        stored_track = unique_dict["T"][track_id]
        stored_track_source = stored_track["source"]

        if source_type == "liked_title":
            stored_track_source["is_liked"] = True

        elif source_type == "playlists":
            playlist_id = track.get("playlist_id")
            playlist_name = track.get("playlist_name")
            if not playlist_id or not playlist_name:
                raise ValueError(f"Track {track_id!r}: missing playlist_id or playlist_name")

            # Add playlist if not already present
            if playlist_id not in stored_track_source["playlists"]:
                stored_track_source["playlists"][playlist_id] = playlist_name

        elif source_type == "albums":
            album_id = track.get("album_id")
            album_name = track.get("album_name")
            if not album_id or not album_name:
                raise ValueError(f"Track {track_id!r}: missing album_id or album_name")

            # Add album if not already present
            if album_id not in stored_track_source["albums"]:
                stored_track_source["albums"][album_id] = album_name


# Storing unique tracks with o(n) time complexity, n being the total tracks amoung all source
def unique_tracks():
    unique_items = {"T": {}}

    # Playlists insertion: 
    unique_track_insertion(unique_items, get_playlist_tracks(), "playlists")  # Passing info of data-source pass to function e.g: is_liked

    # Liked title insertion
    unique_track_insertion(unique_items, get_saved_tracks(), "liked_title")

    # Album insertion: 
    unique_track_insertion(unique_items, get_albums_tracks(), "albums")

    session["total_tracks"] = len(unique_items["T"])

    return unique_items


def generate_secure_secret(length=16):
    characters = string.ascii_letters + string.digits    
    return "".join(secrets.choice(characters) for _ in range(length))


