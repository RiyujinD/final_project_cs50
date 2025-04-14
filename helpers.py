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


### SPOTIFY API ###
class NotAuthenticated(Exception):
    """Raised when the user is not authenticated (missing access token)."""
    pass

class TokenRefreshFailed(Exception):
    """Raised when the access token refresh process fails."""
    pass


def refresh_access_token(refresh_token):
    if refresh_token != session['refresh_token']:
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



class callError(Exception):

    # Custom exception for handling API errors with retries
    def __init__(self, message, status_code, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


# Helper function to retry the requests after sleep
def requests_method(url, headers, method, params):
    
    # Check if method pass is format get or post 
    if method == 'get':
        return requests.get(url, headers=headers, params=params)
    elif method == 'post':
        return requests.post(url, headers=headers, data=params)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


def spotify_requests(url, api_error, method, params, headers=None, rate_info=None):
    if rate_info is None:
        rate_info = {}

    method = method.strip().lower()

    # First request attempt, now using the passed params!
    response = requests_method(url, headers, method, params)

    # Handle rate limit (status code 429)
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))  # Default to 10 seconds if not provided
        print(f"Rate limit reached. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        
        # Retry the request after the specified delay
        response = requests_method(url, headers, method, params)
        
        # If still rate-limited after retry, raise an error
        if response.status_code == 429:
            raise callError("Spotify rate limit reached again", response.status_code, retry_after)

    # Handle rate limit information (X-RateLimit headers)
    if 'X-RateLimit-Limit' in response.headers:
        try:
            rate_info['limit_calls'] = int(response.headers.get("X-RateLimit-Limit", 0))
            rate_info['remaining_calls'] = int(response.headers.get("X-RateLimit-Remaining", 0))
            rate_info['reset'] = int(response.headers.get("X-RateLimit-Reset", 0))

            remaining = rate_info['remaining_calls']
            limit = rate_info['limit_calls']
            warning_threshold = (remaining / limit) * 100 if limit else 100
            current_time = time.time()
            reset_time = int(rate_info['reset'] - current_time)

            # Warning if remaining calls are less than 15% of limit
            if warning_threshold < 15:
                print(f"Warning: Only {remaining} requests remaining. Rate limit will reset in {reset_time}s.")

        except (ValueError, TypeError) as e:
            print(f"Rate limit header parse error: {e}")

    # Handle non-200 status codes
    if response.status_code != 200:
        raise callError(f"{api_error}: {response.status_code} - {response.text}", response.status_code)

    return response



def get_user_spotifyMD():

    if "spotify_id" in session:
        return

    url = "https://api.spotify.com/v1/me"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    response = spotify_requests(
        url,
        "error fetching user meta data: profile",
        'get',
        params=None,
        headers=headers
    )

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

    
def get_likedTitle_tracks():
    
    url = "https://api.spotify.com/v1/me/tracks"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401
    
    # Query parameters 
    fields = "total, next, items(track(id,name,duration_ms,artists,album(images(url))))"
    params = {"fields": fields}
 
    all_liked_title = []
    total_liked_title = None

    while url:
        response = spotify_requests(
            url,
            "error fetching liked title tracks",
            'get',
            params=params,
            headers=headers
        )

        tracksData = response.json()

        if total_liked_title is None:
            total_liked_title = tracksData.get('total', 0)

        track_items = tracksData.get("items", [])
        if track_items:
            for i in track_items:
                if 'track' in i:
                    i['track']['category'] = ('liked title',)
                all_liked_title.append(i)

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
    fs = "next, total, items(id, name, track(id, name, duration_ms, artists))"
    par = {"fields": fs}

    all_playlists_tracks = []
    all_tracks_url = []
    total_playlists = None

    # Pagination track url
    while url:

        response = spotify_requests(
            url,
            "Error fetching playlists",
            'get',
            params=params,
            headers=headers
        )

        playlists_data = response.json()

        if total_playlists is None:
            total_playlists = playlists_data.get('total', 0)

        for playlist in playlists_data.get('items', []):
            tracks_url = playlist.get('tracks', {}).get('href')
            if tracks_url:
                all_tracks_url.append(tracks_url)

        url = playlists_data.get('next')  # Next page of playlists

    # Fetch tracks from each playlist URL
    for track_url in all_tracks_url:
        while track_url:
            resp = spotify_requests(
                track_url,
                "Error fetching playlists tracks",
                'get',
                params=par,
                headers=headers
            )

            track_data_json = resp.json()
            track_items = track_data_json.get('items', [])

            for item in track_items:
                track = item.get('track')
                if track:
                    track['category'] = ('Playlists',)
                    all_playlists_tracks.append(track)

            track_url = track_data_json.get('next')  # Next page of tracks, if any

    return all_playlists_tracks, total_playlists



def get_albums_tracks():
    url = "https://api.spotify.com/v1/me/albums"
    try:
        headers = get_auth_headers()
    except RuntimeError as e:
        return {"error": str(e)}, 401

    fields = "total,next,items(album(id,name,tracks(href,next,previous,items(id,name,duration_ms,artists)),images(url)))"
    params = {"fields": fields}

    all_album_tracks = []
    total_albums = 0

    # Paginate through albums
    while url:
        response = spotify_requests(url, "Error fetching albums", 'get', params=params, headers=headers)
        album_data = response.json()

        if total_albums is None:
            total_albums = album_data.get('total', 0)

        album_items = album_data.get('items', [])

        # Loop all albums
        for album_item in album_items:
            album = album_item.get("album", {})
            tracks = album.get("tracks", {})
            track_items = tracks.get("items", [])

            # Loop all tracks of albums
            for track in track_items:
                track['category'] = ('Albums',)
            all_album_tracks.extend(track_items)

            # Handleling pagination if any
            tracks_url = tracks.get('next')
            while tracks_url:
                track_response = spotify_requests(
                    tracks_url,
                    "Error fetching albums",
                    'get', 
                    params=None,
                    headers=headers,
                ) # new request on new page

                json_tracks = track_response.json()
                tracks_i = json_tracks.get('items', [])
                if tracks_i:
                    for track in tracks_i:
                        track['category'] = ('Albums',)
                        all_album_tracks.append(track)
                tracks_url = json_tracks.get('next')

        url = album_data.get('next')  # Next page of albums

    total_albums = album_data.get('total', 0)
    return all_album_tracks, total_albums

# Helper to remove duplicate logic on next function 
def uniqueTA_insertion(unique_dict, query):
    for item in query:

        # Check struct, object -> list of dict items or object -> list of track 
        if 'track' in item:
            track = item.get('track')
        else:
            track = item

        # Get the category and track ID
        track_category = track.get('category', ())
        track_id = track.get("id")

        if track_id:
            if track_id not in unique_dict['T']:
                unique_dict["T"][track_id] = track
            else:
                existing_category = unique_dict['T'][track_id].get('category', ())

                if track_category not in existing_category:
                    unique_dict['T'][track_id]['category'] = existing_category + track_category # Add the new category to the existing categories tuple

        # Handle artists for this track
        track_artists = track.get('artists', [])
        for artist in track_artists:
            artist_id = artist.get('id')
            if artist_id and artist_id not in unique_dict['A']:
                # Add artist to the 'A' dict if not already present
                unique_dict["A"][artist_id] = artist



def tracks_and_artists(playlists, liked_title, albums):
    unique_items = {"T": {}, "A": {}}

    # Liked title insertion
    uniqueTA_insertion(unique_items, liked_title)

    # Album insertion: 
    uniqueTA_insertion(unique_items, albums)

    # Playlists insertion: 
    uniqueTA_insertion(unique_items, playlists)

    total_tracks = len(unique_items['T'])
    total_artists = len(unique_items['A'])

    return unique_items, total_tracks, total_artists


def generate_secure_secret(length=16):
    characters = string.ascii_letters + string.digits    
    return ''.join(secrets.choice(characters) for _ in range(length))



# To do in helpersDB 
# def store_tracks_in_db(db, tracks_data):
#     cursor = db.cursor()

#     for track in tracks_data:
#         track_id = track.get('track', {}).get('id')
#         track_name = track.get('track', {}).get('name')
#         artist_name = track.get('track', {}).get('artists', [{}])[0].get('name')  

#         cursor.execute("INSERT OR IGNORE INTO tracks (track_id, track_name, artist_name) VALUES (?, ?, ?)",
#                        (track_id, track_name, artist_name))

#     db.commit()

 