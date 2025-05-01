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
    print(f'THIS IS THE SPOTIFY USER ID {spotify_user_id}')
    user_name = session.get("username", "")
    print(f'THIS IS THE SPOTIFY USERNAME {user_name}')

    if not spotify_user_id or not user_name:
        raise Exception("Id or username not found")
    

    with link_db() as db:
        db.execute("""
            INSERT INTO users (user_id, name, rank)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET name = excluded.name
        """, 
            (spotify_user_id, user_name, "F"))
    print("Succesfully insert user_id , name, and rank")


def insert_tracks(unique_items):
    user_id = session["spotify_id"]
    tracks = unique_items['T']
    if not user_id or not tracks:
      raise DatabaseError("Failed to find user id or tracks")
    
    tuple_albums = []
    tuples_tracks = []
    tuple_user_albums = []
    tuple_playlist = []
    tuple_user_playlist_tracks = []
    tuple_user_playlists = []
    tuple_liked = []

    for track_id, track in tracks.items():
        album_data = track["album"]
        tuple_albums.append((
            album_data['id'],
            album_data['name'],
            album_data['artists'],
            album_data['cover_url'],
            album_data['total_tracks']
        ))

        tuples_tracks.append((
            track_id,
            track["name"],
            track["artists"],
            track["duration_ms"],
            album_data['id'],
            track.get("popularity", 0)
        ))

        if track["source"]["is_liked"]:
            tuple_liked.append((
                user_id,
                track_id,
            ))

        if track["source"]["album_added"]:
            tuple_user_albums.append((
                user_id,
                album_data['id']
            ))

        for pi, p in track["source"]["playlists"].items():
            tuple_playlist.append((
                pi,
                p["name"],
                p["cover_url"],
                p["total_tracks"],
            ))

            tuple_user_playlists.append((
                user_id,
                pi,
            ))

            tuple_user_playlist_tracks.append((
                user_id,
                track_id,
                pi
            ))

    with link_db() as db:


        # 1. Inserting albums
        print("→ album rows to insert:", tuple_albums[0])
        db.executemany("""
            INSERT OR IGNORE INTO albums
                (album_id, name, artists, cover_url, total_tracks)
            VALUES (?, ?, ?, ?, ?)
        """, tuple_albums)
        print("→ALBUM INSERT SUCCESFULLY")


        # 2. Then inserting tracks (depends on albums)
        print("→ tracks row to insert:", tuples_tracks[0])
        db.executemany("""
            INSERT OR IGNORE INTO tracks
                (track_id, name, artists, duration_ms, album_id, popularity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tuples_tracks)
        print("→TRACKS INSERT SUCCESFULLY")

        # 3. Inserting user_albums link (depends on albums and tracks)
        print("→ user albumsrow to insert:", tuple_user_albums[0])
        if tuple_user_albums:
            db.executemany("""
                INSERT OR IGNORE INTO user_albums
                    (user_id, album_id)
                VALUES (?, ?)
            """, tuple_user_albums)
        print("USER ALBUM INSERT SUCCESFULLY")
        
        # 4. Insert playlists before user_playlists
        print("→ playlist row to insert:", tuple_playlist[0])
        if tuple_playlist:
            db.executemany("""
                INSERT OR IGNORE INTO playlists
                    (playlist_id, name, cover_url, total_tracks)
                VALUES (?, ?, ?, ?)
            """, tuple_playlist)
        print("→PLAYLIST INSERT SUCCESFULLY")

        # 5. Now is ok to insert user_playlists         
        print("→ user playlist row to insert:", tuple_user_playlists[0])
        if tuple_user_playlists:
            db.executemany("""
                INSERT OR IGNORE INTO user_playlists
                    (user_id, playlist_id)
                VALUES (?, ?)
            """, tuple_user_playlists)
        print("→USER PLAYLIST INSERT SUCCESFULLY")

        # 6. Inserting user playlists track (depends on playlist and user_playlist)      
        print("→ playlist user tracks rowS to insert:", tuple_user_playlist_tracks[0])
        if tuple_user_playlist_tracks:
            db.executemany("""
                INSERT OR IGNORE INTO user_playlist_tracks
                    (user_id, track_id, playlist_id)
                VALUES (?, ?, ?)
            """, tuple_user_playlist_tracks)
        print("→TRACK USER PLAYLIST INSERT SUCCESFULLY")

        # 6. Inserting user liked title (depend on tracks)
        print("→ liked title user row to insert:", tuple_liked[0])
        if tuple_liked:
            db.executemany("""
                INSERT OR IGNORE INTO user_likes
                    (user_id, track_id)
                VALUES (?, ?)
            """, tuple_liked)
        print("LIKED TRACK FROM USER INSERT SUCCESFULLY")


