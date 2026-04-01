import os
import sys
import time
import threading
from flask import Flask, jsonify
import config
from database import init_db

# Импортируем обработчики Telegram
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
    from handlers import *
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    print(f"Telegram import error: {e}")
    TELEGRAM_AVAILABLE = False

# Создаем Flask приложение
flask_app = Flask(__name__)

# Создаем Telegram приложение
telegram_app = None

def setup_handlers():
    """Настройка всех обработчиков"""
    if not TELEGRAM_AVAILABLE:
        return
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('predict', predict),
            MessageHandler(filters.Regex('^🔮 Получить предсказание$'), predict),
        ],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question)],
            ASK_ZODIAC: [CallbackQueryHandler(ask_zodiac, pattern='^zodiac_')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    telegram_app.add_handler(CommandHandler('start', start))
    telegram_app.add_handler(CommandHandler('help', help_command))
    telegram_app.add_handler(conv_handler)
    telegram_app.add_handler(CallbackQueryHandler(new_prediction_callback, pattern='^new_prediction$'))
    telegram_app.add_handler(MessageHandler(filters.Regex('^ℹ️ Помощь$'), help_command))
    telegram_app.add_handler(MessageHandler(filters.Regex('^🔮 Получить предсказание$'), predict))

def run_telegram_polling():
    """Запуск Telegram бота в режиме polling"""
    try:
        logger.info("Starting Telegram bot in polling mode...")
        telegram_app.run_polling()
    except Exception as e:
        logger.error(f"Error in telegram polling: {e}")

@flask_app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Fortune Bot is running!',
        'bot_configured': telegram_app is not None,
        'telegram_available': TELEGRAM_AVAILABLE,
        'python_version': sys.version
    })

@flask_app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'bot_running': True,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print("=" * 50)
    
    # Инициализация базы данных
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        print(f"Database error: {e}")
    
    # Настройка Telegram
    if TELEGRAM_AVAILABLE and config.BOT_TOKEN:
        telegram_app = Application.builder().token(config.BOT_TOKEN).build()
        setup_handlers()
        
        # Запускаем Telegram бота в отдельном потоке
        bot_thread = threading.Thread(target=run_telegram_polling)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Telegram bot thread started")
    else:
        logger.warning("Telegram bot not configured")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    flask_app.run(host='0.0.0.0', port=port)