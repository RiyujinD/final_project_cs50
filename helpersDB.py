import sqlite3
from config import DATABASE

### REMINDER TO ALWAYS CLOSE DB AFTER COMMITS ### 

def link_db():
  db = sqlite3.connect(DATABASE)
  db.row_factory = sqlite3.Row # Allows accessing columns by name e.g row["id"]

  return db


def insert_userID_database(spotify_id):
    
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