import sqlite3
from datetime import datetime
from utils import logger

DB_PATH = 'bot_database.db'

def init_db():
    """Инициализация базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Таблица пользователей
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
        
        # Таблица предсказаний
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prediction_type TEXT,
            prediction_text TEXT,
            zodiac_sign TEXT,
            price INTEGER,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def get_user(user_id):
    """Получение информации о пользователе"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None

def create_user(user_id, username, first_name, last_name):
    """Создание нового пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, reg_date)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now()))
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} created")
    except Exception as e:
        logger.error(f"Error creating user {user_id}: {e}")

def update_user_zodiac(user_id, zodiac_sign):
    """Обновление знака зодиака пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE users SET zodiac_sign = ? WHERE user_id = ?
        ''', (zodiac_sign, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating zodiac for user {user_id}: {e}")

def save_prediction(user_id, prediction_type, prediction_text, zodiac_sign, price):
    """Сохранение предсказания в базу"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO predictions (user_id, prediction_type, prediction_text, zodiac_sign, price, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, prediction_type, prediction_text, zodiac_sign, float(price), datetime.now()))
        
        # Обновляем статистику пользователя
        cursor.execute('''
        UPDATE users 
        SET total_predictions = total_predictions + 1,
            last_prediction_date = ?
        WHERE user_id = ?
        ''', (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Prediction saved for user {user_id}")
    except Exception as e:
        logger.error(f"Error saving prediction: {e}")