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
    """
    Fetches all users liked tracks from Spotify, formatting each artists into
    a str separate by coma, and storing the first album images url into the the track object
    Return a list of track dicts 
    """

    url = "https://api.spotify.com/v1/me/tracks"
    headers = get_auth_headers()
    
    # Query parameters 
    fields = "total,next,items(track(id,name,duration_ms,popularity,artists(name),album(id,name,artists(name),images(url),total_tracks)))"
    params = {"fields": fields}
 
    all_liked_title = []
    total_liked_title = None

    while url:
        response = spotify_requests(url, "Error fetching liked tracks", "get", params=params, headers=headers)
        tracks_data = response.json()

        if total_liked_title is None:
            total_liked_title = tracks_data.get("total", 0)

        for item in tracks_data.get("items", []):
            track = item.get("track")
            if not track:
                continue
            
            # Extracting and re-formatting track artists
            track_artists = [t_a.get("name", "") for t_a in track.pop("artists", [])]
            track["artists"] = ",".join(track_artists)

            # Extracting album information
            album = track.pop("album", {})

            # Extracting and re-formatting album artists
            album_artists = [a_a.get("name", "") for a_a in album.pop("artists", [])]
            album["artists"] = ",".join(album_artists)

            # Extracting cover image URL
            images = album.pop("images", None)
            cover_url = images[0].get("url") if images else None
            album["cover_url"] = cover_url
            
            track["album"] = album

            all_liked_title.append(track)

        # Next page if available
        url = tracks_data.get("next")
        
    session["total_liked_tracks"] = total_liked_title
    return all_liked_title


def get_playlist_tracks():
    """
    Fetch all of the user's playlists and their tracks from Spotify.
    Formatting each track's artists into a comma-delimited string,
    and storing the first cover image into the track object.
    Returns a list of track dicts.
    """
    
    url = "https://api.spotify.com/v1/me/playlists"
    headers = get_auth_headers()

    # Fields for playlist endpoint
    playlist_fields = "total,next,items(id,name,images(url),tracks(href,total))"
    playlist_params = {"fields": playlist_fields}
    
    # Fields for track pagination
    track_fields = (
        "next,total,"
        "items(track(id,name,duration_ms,popularity,artists(name),"
        "album(id,name,artists(name),images(url),total_tracks)))"
    )

    all_playlists_tracks = []
    total_playlists = None

    # Page through all playlists
    while url:
        response = spotify_requests(url, "Error fetching playlists", "get", params=playlist_params, headers=headers)
        playlists_data = response.json()

        if total_playlists is None:
            total_playlists = playlists_data.get("total", 0)

        for playlist in playlists_data.get("items", []):
            playlist_id = playlist.get("id")
            playlist_name = playlist.get("name")
            playlist_total_tracks = playlist.get("tracks", {}).get("total", 0)

            # First cover image (if any)
            images = playlist.get("images", [])
            cover_url = images[0]["url"] if images else None

            # track resources
            track_url = playlist.get("tracks", {}).get("href")
            track_params = {"fields": track_fields}

            # Pagination through tracks of this playlist
            while track_url:
                resp = spotify_requests(track_url, "Error fetching playlist tracks", "get", params=track_params, headers=headers)
                track_data = resp.json()
                track_items = track_data.get("items", [])

                for item in track_items:
                    track = item.get("track", {})
                    if not track:
                        continue

                    # Artists separated by commas for track
                    track_artists = [a.get("name", "") for a in track.get("artists", [])]
                    track["artists"] = ",".join(track_artists)

                    # Extracting album data and reformat it
                    album_data = track.pop("album", {})

                    # Formated album artists
                    album_artists = [a_a.get("name", "") for a_a in album_data.pop("artists", [])]
                    album_data["artists"] = ",".join(album_artists)

                    # Keep first album image as cover
                    album_images = album_data.get("images", [])
                    album_data["cover_url"] = album_images[0]["url"] if album_images else None
                    album_data.pop("images", None)

                    track["album"] = album_data # Formatted album data

                    # Playlist metadata
                    track["playlist"] = {
                        "id":           playlist_id,
                        "name":         playlist_name,
                        "total_tracks": playlist_total_tracks,
                        "cover_url":        cover_url
                    }

                    all_playlists_tracks.append(track)

                # advance to next page 
                track_url = track_data.get("next")

        # advance to next page of playlists
        url = playlists_data.get("next")
        playlist_params = None  # only sending fields on the very first playlist request

    session["total_playlists"] = total_playlists
    return all_playlists_tracks



def get_albums_tracks():
    """
    Fetch all of the user's saved albums and their tracks from Spotify.
    Returns a flat list of track dicts with attached album info.
    """

    url = "https://api.spotify.com/v1/me/albums"
    headers = get_auth_headers()

    album_fields = "total,next,items(album(id,name,artists(name),images(url),total_tracks))"
    album_params = {"fields": album_fields}

    track_fields = "items(id,name,duration_ms,popularity,artists(name)),next"
    all_album_tracks = []
    total_albums = None

    while url:
        response = spotify_requests(url, "Error fetching albums", "get", params=album_params, headers=headers)
        album_data = response.json()

        if total_albums is None:
            total_albums = album_data.get("total", 0)

        for item in album_data.get("items", []):
            album = item.get("album", {})
            album_id = album.get("id")

            # Formated album artists coma separated value
            album_artists = [a.get("name", "") for a in album.pop("artists", [])]
            album["artists"] = ",".join(album_artists)

            # Album cover
            images = album.pop("images", [])
            album["cover_url"] = images[0]["url"] if images else None

            # Fetch full tracklist via /albums/{id}/tracks
            track_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
            params = {"fields": track_fields}

            while track_url:
                track_response = spotify_requests(track_url, "Error fetching album tracks", "get", params=params, headers=headers)
                track_data = track_response.json()
                track_items = track_data.get("items", [])

                for track in track_items:
                    track_artists = [a.get("name", "") for a in track.pop("artists", [])]
                    track["artists"] = ",".join(track_artists)
                    track["album"] = album
                    all_album_tracks.append(track)

                track_url = track_data.get("next")
                params = None

        url = album_data.get("next")
        album_params = None  # Only include fields on first request

    session["total_albums"] = total_albums
    return all_album_tracks


# Helper to next function: Adding unique tracks and they're source
def unique_track_insertion(unique_dict, tracks, source_type):
    """
    - unique_dict: {"T": {}}
    - tracks:   List[track_dict]
    - source_type: "liked_title", "albums", "playlists"
    """
    for track in tracks:
        track_id = track.get("id")
        if not track_id:
            raise ValueError(f"Track {track}: missing id in uniqueTA insertion.")

        # If track is not store yet
        if track_id not in unique_dict["T"]:

            # Initializing source dict
            track["source"] = {
                "playlists": {},
                "is_liked": False,
                "album_added": False
            }

            if source_type == "liked_title":
                track["source"]["is_liked"] = True

            elif source_type == "albums":
                track["source"]["album_added"] = True

            elif source_type == "playlists":
                playlist_info = track.pop("playlist", None)
                if not playlist_info or "id" not in playlist_info:
                    raise ValueError(f"Track {track_id}: missing or invalid playlist")
                playlist_id = playlist_info.pop("id")
                track["source"]["playlists"][playlist_id] = playlist_info
            else:
                raise ValueError("Wrong source_type: not in [playlists, liked_title, albums]")

            # Insert the reformatted track into the dict
            unique_dict["T"][track_id] = track

        # Track already stored, update source
        else:
            stored_track = unique_dict["T"][track_id]

            if source_type == "liked_title":
                stored_track["source"]["is_liked"] = True

            elif source_type == "albums":
                stored_track["source"]["album_added"] = True

            elif source_type == "playlists":
                playlist_info = track.pop("playlist", None)
                if not playlist_info or "id" not in playlist_info:
                    raise ValueError(f"Track {track_id!r}: missing or invalid 'playlist'")
                playlist_id = playlist_info.pop("id")
                stored_track["source"]["playlists"].setdefault(playlist_id, playlist_info) # Auto check if id already exist if not insert it
            else:
                raise ValueError("Wrong source_type: not in [playlists, liked_title, albums]")


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


