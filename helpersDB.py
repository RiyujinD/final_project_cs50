import sqlite3
from flask import session
from config import DATABASE


class DatabaseError(Exception):
    pass

def link_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.row_factory = sqlite3.Row  # Allows accessing columns by name e.g., row["id"]
    return db

def insert_userID(spotify_id):
    try:
        with link_db() as db:
            db.execute("INSERT OR IGNORE INTO users (spotify_user_id) VALUES (?)", (spotify_id,))
    except sqlite3.Error as e:
        raise DatabaseError("Failed to insert user id") from e


def insert_tracks_artists(unique_items):
    
    spotify_id = session["spotify_id"]
    if not spotify_id:
      raise DatabaseError("Failed to find user id")


    for track_id, track in unique_items['T'].items():
        name = track['name']
        duration = track['duration_ms']

        # Collect artist names using a regular loop
        artist_names = []
        for artist in track['artists']:
            artist_names.append(artist['name'])
        artists = ', '.join(artist_names)

        try:
            with link_db() as db:
                db.execute("""
                    INSERT OR IGNORE INTO tracks (track_id, track_name, duration_ms, artist_name)
                    VALUES (?, ?, ?, ?)
                    """, (track_id, name, duration, artists))

                db.execute("""
                    INSERT OR IGNORE INTO user_tracks (spotify_user_id, track_id) 
                    VALUES (?, ?)
                    """, (spotify_id, track_id))
                
        except sqlite3.Error as e:
            raise DatabaseError("Failed to insert user id") from e



