import sqlite3
from config import DATABASE

### REMINDER TO ALWAYS CLOSE DB AFTER COMMITS ### 

def link_db():
  db = sqlite3.connect(DATABASE)
  db.row_factory = sqlite3.Row # Allows accessing columns by name e.g row["id"]
  return db


def insert_userID(spotify_id):
    db = link_db()
    cursor = db.cursor()

    try:
      cursor.execute("INSERT OR IGNORE INTO users (spotify_user_id) VALUES (?)", (spotify_id))
      db.commit()
      print("User data ID insert succesfuly")
      
    except Exception as e:
       db.rollback()
       print("rollback for user id insertion")

    finally:
       db.close()


def insert_tracks_artists(unique_items):
   try:
    db = link_db()
    cursor = db.cursor()

    for track_id, track in unique_items['T'].items():
        id = track_id
        name = track['name']

   except Exception as e:
      db.rollback()
      print(f"rollback for track insertion insertion {e}")





