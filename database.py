import sqlite3
import os

DB_PATH = "catalyst_user_pref.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create table for User Preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            verbosity TEXT DEFAULT 'Standard',
            tone TEXT DEFAULT 'Colleague',
            formatting TEXT DEFAULT 'Standard',
            custom_rules TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

def save_user_prefs(user_id, verbosity, tone, formatting, custom=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, verbosity, tone, formatting, custom_rules)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, verbosity, tone, formatting, custom))
    conn.commit()
    conn.close()

def get_user_prefs(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT verbosity, tone, formatting, custom_rules FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return f"Verbosity: {row[0]}, Tone: {row[1]}, Style: {row[2]}. Rules: {row[3]}"
    return "Standard, Colleague tone"