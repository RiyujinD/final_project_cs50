from flask import Flask, make_response, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

#import os

app = Flask(__name__)

app.jinja_env.cache = {}

# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
#Session(app)


#@app.after_request
#def after_request(response):
#    """Ensure responses aren't cached"""
#    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#    response.headers["Expires"] = 0
#    response.headers["Pragma"] = "no-cache"
#    return response


@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

app.config['TEMPLATES_AUTO_RELOAD'] = True

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


if __name__ == "__main__":
    app.run(debug=True)