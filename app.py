import os
import secrets
import string
import base64
from flask import Flask, url_for, redirect, request, jsonify, session, render_template
from flask_session import Session
from dotenv import load_dotenv
from urllib.parse import urlencode
import requests
# from flask_cors import CORS
    
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

app_secret_key = os.getenv("APP_SECRET_KEY")

# Configure session to use filesystem
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# CORS(app)
#session['oauth_state'] = 


# Load credentials and URLs from .env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
AUTHORIZATION_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"


def generate_secure_secret(length=16):
    # Define the characters to use (A-Z, a-z, 0-9)
    characters = string.ascii_letters + string.digits
    # Randomly choose `length` characters from the pool
    return ''.join(secrets.choice(characters) for _ in range(length))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():

    state = generate_secure_secret() 
    session["oauth_state"] = state # Store the state generate above in the session 
    scope = "user-read-private, user-modify-playback-state"

    # Spotify auth URL build
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

    # Get the auth code and state from uri
    code = request.args.get("code")
    state = request.args.get("state")

    # Retrieve the stored state from the session
    stored_state = session.get("oauth_state")

    # Check if state match stored one and if state not NULL
    if not state or state != stored_state:
        return redirect(url_for("index") + "?" + urlencode({"error": "state_mismatch"})) # Build url and redirect to index page

    # Clear the stored state from the session
    session.pop("oauth_state", None)

    # Base64 encoding of the client ID and secret and decoding back in utf-8
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"  # Combine client_id and client_secret
    auth_bytes = auth_str.encode("utf-8")     # Convert to bytes
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")  # Base64 encode and decode to string

    # Request access token  
    url = "https://accounts.spotify.com/api/token"  
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
    response = requests.post(url, data=auth_data, headers=auth_headers)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch tokens", "details": response.json()})
    
    # Parse the response JSON
    token_data = response.json()

    # Store the tokens in the session or handle them as needed
    session["access_token"] = token_data.get("access_token")
    session["refresh_token"] = token_data.get("refresh_token")
    session["expires_in"] = token_data.get("expires_in")

    # Redirect to the main app or a success page
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)