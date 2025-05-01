import sqlite3
from flask import session
from config import DATABASE

ALLOWED_RANKS = ['F','E','D','C','B','A','S','S+']

class DatabaseError(Exception):
    pass

def link_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON") # Foreing key activation
    db.row_factory = sqlite3.Row  # Allows accessing columns by name e.g., row["id"]
    return db

def insert_user():
    spotify_user_id = session["spotify_id"]
    user_name = session.get("username", "")

    with link_db() as db:
        db.execute("""
            INSERT INTO users (user_id, name, rank)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET name = excluded.name
        """, 
            (spotify_user_id, user_name, "F"))
    print("Succesfully insert user_id , name, and rank")


def insert_tracks(unique_items):

    spotify_id = session["spotify_id"]
    tracks = unique_items['T']
    
    if not spotify_id:
      raise DatabaseError("Failed to find user id")
    
    tuples_tracks_data = []
    user_tracks_tuple = []

    for track_id, track in tracks.items():
        tuples_tracks_data.append((
            track_id,
            track["name"],
            track["artists"],
            track["duration_ms"],
            track["album"]["id"],
            track["album"]["name"],
            track["album"]["cover"],
            track["album"]["total_tracks"],
            track.get("popularity", 0)
        ))

        
        if track["source"]["is_liked"]:
            user_tracks_tuple.append((
                spotify_id,
                track_id,
                1,    # Bool is_liked 
                None, # playlist_id
                None, # playlist_name
                None, # total_tracks in playlist
                None  # cover playlist
            ))

        # Check source
        if track["source"]["album_added"]:
            user_tracks_tuple.append((
                spotify_id,
                track_id,
                0,     # Bool is_liked 
                None,  # playlist_id
                None,  # playlist_name
                None,  # total_tracks in playlist
                None   # cover playlist
            ))
        
        for pi, p in track["source"]["playlists"].items():
            user_tracks_tuple.append((
                spotify_id,
                track_id,
                int(track["source"]["is_liked"]),
                pi, 
                p["name"],
                p["total_tracks"],
                p["cover"]
            ))
        

    if not tuples_tracks_data or not user_tracks_tuple:
        raise DatabaseError("Failed to turn track data to list of tuples")
    
    with link_db() as db:
        db.executemany("""
            INSERT OR IGNORE INTO tracks
                (track_id, name, artists, duration_ms, album_id, album_name, album_cover_url, tracks_in_album, popularity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuples_tracks_data)

        db.executemany("""
            INSERT OR IGNORE INTO user_tracks
                (user_id, track_id, is_liked, playlist_id, playlist_name, total_tracks_in_playlist, playlist_cover_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, user_tracks_tuple)



    