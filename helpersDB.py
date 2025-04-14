import sqlite3
from config import DATABASE
from flask import session

### REMINDER TO ALWAYS CLOSE DB AFTER COMMITS ### 

def link_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.row_factory = sqlite3.Row  # Allows accessing columns by name e.g., row["id"]
    return db


def insert_userID(spotify_id):
    db = link_db()
    cursor = db.cursor()

    try:
        cursor.execute("INSERT OR IGNORE INTO users (spotify_user_id) VALUES (?)", (spotify_id,))
        db.commit()
        print("User data ID inserted successfully")
    except Exception as e:
        db.rollback()
        print(f"Rollback for user id insertion: {e}")
    finally:
        cursor.close()  
        db.close()


def insert_tracks_artists(unique_items):
    
    spotify_id = session["spotify_id"]
    if not spotify_id:
      print("No user ID found in session")
      return

    try:
        db = link_db()
        cursor = db.cursor()

        for track_id, track in unique_items['T'].items():
            name = track['name']
            duration = track['duration_ms']

            # Collect artist names using a regular loop
            artist_names = []
            for artist in track['artists']:
                artist_names.append(artist['name'])
            artists = ', '.join(artist_names)

            cursor.execute("""
                INSERT OR IGNORE INTO tracks (track_id, track_name, duration_ms, artist_name)
                VALUES (?, ?, ?, ?)
                """, (track_id, name, duration, artists))

            cursor.execute("""
                INSERT OR IGNORE INTO user_tracks (spotify_user_id, track_id) 
                VALUES (?, ?)
                """, (spotify_id, track_id))

        db.commit()

    except Exception as e:
        print(f"Error inserting tracks and artists: {e}")
        db.rollback()

    finally:
        cursor.close()  
        db.close()
