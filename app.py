from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

import os

app = Flask(__name__)

#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
#Session(app)

#@app.after_request
#def after_request(response):
#   """Ensure responses is not cached"""
#    response.headers["Cache-Control"] = "no-cache, no store, must-revalidate"
#     response.headers["Expires"] = 0
#     response.headers["Pragma"] = "no-cache"
#     return response

@app.route("/")
# @login_required
def index():
    # if request == get
    return render_template("index.html")