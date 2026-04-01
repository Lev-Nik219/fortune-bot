import sqlite3
from datetime import datetime
from utils import logger

DB_PATH = 'bot_database.db'

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            zodiac_sign TEXT,
            reg_date TIMESTAMP,
            last_prediction_date TIMESTAMP,
            total_predictions INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prediction_type TEXT,
            prediction_text TEXT,
            zodiac_sign TEXT,
            price REAL,
            created_at TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database error: {e}")

def create_user(user_id, username, first_name, last_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, reg_date)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Create user error: {e}")

def update_user_zodiac(user_id, zodiac_sign):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET zodiac_sign = ? WHERE user_id = ?', (zodiac_sign, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Update zodiac error: {e}")

def save_prediction(user_id, pred_type, pred_text, zodiac_sign, price):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO predictions (user_id, prediction_type, prediction_text, zodiac_sign, price, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, pred_type, pred_text, zodiac_sign, price, datetime.now()))
        
        cursor.execute('''
        UPDATE users SET total_predictions = total_predictions + 1, last_prediction_date = ?
        WHERE user_id = ?
        ''', (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Save prediction error: {e}")