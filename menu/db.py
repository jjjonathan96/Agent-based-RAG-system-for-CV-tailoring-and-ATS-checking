import sqlite3

DB_PATH = "profile.db"

def init_profile_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT,
                  phone TEXT,
                  linkedin TEXT,
                  github TEXT,
                  country TEXT
              )''')
    conn.commit()
    conn.close()

def save_profile_to_db(name, email, phone, linkedin, github, country):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM user_profile")  # single profile entry
    c.execute("INSERT INTO user_profile (name, email, phone, linkedin, github, country) VALUES (?, ?, ?, ?, ?, ?)",
              (name, email, phone, linkedin, github, country))
    conn.commit()
    conn.close()

def load_profile_from_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, email, phone, linkedin, github, country FROM user_profile LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return dict(zip(["name", "email", "phone", "linkedin", "github", "country"], row))
    return {}
