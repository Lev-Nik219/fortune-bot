import os
import sys
import time
import threading
import asyncio
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Импортируем настройки
try:
    import config
    from database import init_db
    from handlers import start, help_command
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Создаем заглушки
    config = type('obj', (object,), {'BOT_TOKEN': os.getenv('BOT_TOKEN', '')})()
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Bot is working!")

# Создаем Flask приложение
flask_app = Flask(__name__)

# Создаем Telegram приложение
telegram_app = None

def setup_telegram():
    """Настройка Telegram бота"""
    global telegram_app
    
    if not config.BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return False
    
    try:
        telegram_app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Добавляем обработчики
        telegram_app.add_handler(CommandHandler('start', start))
        telegram_app.add_handler(CommandHandler('help', help_command))
        
        print("✅ Telegram bot configured successfully")
        return True
    except Exception as e:
        print(f"❌ Error setting up Telegram bot: {e}")
        return False

def run_telegram():
    """Запуск Telegram бота"""
    try:
        print("Starting Telegram bot in polling mode...")
        telegram_app.run_polling()
    except Exception as e:
        print(f"Error in telegram polling: {e}")

@flask_app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Fortune Bot is running!',
        'bot_configured': telegram_app is not None,
        'python_version': sys.version
    })

@flask_app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

if __name__ == '__main__':
    # Инициализация базы данных
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Настройка Telegram
    if setup_telegram():
        # Запускаем Telegram бота в отдельном потоке
        bot_thread = threading.Thread(target=run_telegram)
        bot_thread.daemon = True
        bot_thread.start()
        print("✅ Telegram bot thread started")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask server on port {port}")
    flask_app.run(host='0.0.0.0', port=port)