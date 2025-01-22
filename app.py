import os
import secrets
import string
import base64
from flask import Flask, url_for, redirect, request, jsonify, session, render_template
from dotenv import load_dotenv
from urllib.parse import urlencode
# import requests
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

if __name__ == "__main__":
    app.run(debug=True)