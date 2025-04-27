import os
from dotenv import load_dotenv
import base64
from googleapiclient.discovery import build


# Absolute path to database
APP_DIR = os.path.abspath(os.path.dirname(__file__)) # Absulute path for app
DATABASE = os.path.join(APP_DIR, "database.db")

load_dotenv()

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

# For tokens
SPOTIFY_TOKEN_HEADERS = {
    "Authorization": "Basic " + auth_base64,
    "Content-Type": "application/x-www-form-urlencoded"
}

# Load YouTube API Key from environment variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY) # Initialize YouTube API client