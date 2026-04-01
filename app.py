import os
import sys
import time
import threading
import logging
from flask import Flask, jsonify

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Starting Fortune Bot...")
print("=" * 60)

# Импортируем настройки
try:
    import config
    from database import init_db
    logger.info("Config and database imported successfully")
except Exception as e:
    logger.error(f"Error importing config: {e}")
    # Создаем заглушку
    class config:
        BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        CRYPTOPAY_TOKEN = os.getenv('CRYPTOPAY_TOKEN', '')
        HF_API_KEY = os.getenv('HF_API_KEY', '')
        TEST_MODE = False
        PRICE_USDT = 0.10

# Импортируем Telegram
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
    from handlers import *
    TELEGRAM_AVAILABLE = True
    logger.info("Telegram modules imported successfully")
except Exception as e:
    logger.error(f"Error importing telegram: {e}")
    TELEGRAM_AVAILABLE = False
    
    # Создаем заглушки для handlers
    async def start(update, context):
        await update.message.reply_text("Bot is starting...")
    
    async def help_command(update, context):
        await update.message.reply_text("Help message")
    
    async def predict(update, context):
        return 0
    
    async def cancel(update, context):
        return -1
    
    # Создаем заглушки для состояний
    ASK_NAME, ASK_GENDER, ASK_QUESTION, ASK_ZODIAC = range(4)

# Создаем Flask приложение
flask_app = Flask(__name__)

# Создаем Telegram приложение
telegram_app = None
bot_thread = None

def setup_telegram():
    """Настройка Telegram бота"""
    global telegram_app
    
    if not TELEGRAM_AVAILABLE:
        logger.error("Telegram modules not available")
        return False
    
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return False
    
    try:
        logger.info(f"Setting up Telegram bot with token: {config.BOT_TOKEN[:10]}...")
        telegram_app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Добавляем базовые обработчики
        telegram_app.add_handler(CommandHandler('start', start))
        telegram_app.add_handler(CommandHandler('help', help_command))
        telegram_app.add_handler(CommandHandler('cancel', cancel))
        
        # Добавляем обработчик предсказаний
        try:
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
            telegram_app.add_handler(conv_handler)
            logger.info("Conversation handler added")
        except Exception as e:
            logger.error(f"Error adding conversation handler: {e}")
        
        logger.info("Telegram bot configured successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up Telegram bot: {e}")
        return False

def run_telegram_polling():
    """Запуск Telegram бота в режиме polling"""
    global telegram_app
    
    if not telegram_app:
        logger.error("Telegram app not initialized")
        return
    
    try:
        logger.info("Starting Telegram bot polling...")
        # Запускаем polling
        telegram_app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error in telegram polling: {e}")

@flask_app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Fortune Bot is running!',
        'python_version': sys.version,
        'telegram_available': TELEGRAM_AVAILABLE,
        'bot_token_set': bool(config.BOT_TOKEN),
        'bot_configured': telegram_app is not None
    })

@flask_app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'bot_running': telegram_app is not None,
        'timestamp': time.time()
    })

@flask_app.route('/test')
def test():
    """Тестовый эндпоинт"""
    return jsonify({
        'status': 'ok',
        'message': 'Test endpoint works'
    })

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Fortune Bot...")
    print(f"Python: {sys.version}")
    print(f"Telegram available: {TELEGRAM_AVAILABLE}")
    print(f"Bot token set: {bool(config.BOT_TOKEN)}")
    print("=" * 60)
    
    # Инициализация базы данных
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Настройка Telegram
    if TELEGRAM_AVAILABLE and config.BOT_TOKEN:
        if setup_telegram():
            # Запускаем Telegram бота в отдельном потоке
            bot_thread = threading.Thread(target=run_telegram_polling, daemon=True)
            bot_thread.start()
            logger.info("Telegram bot thread started")
            print("✅ Telegram bot is running in background")
        else:
            logger.error("Failed to setup Telegram bot")
            print("❌ Failed to setup Telegram bot")
    else:
        logger.warning("Telegram bot not configured")
        print("⚠️ Telegram bot not configured - missing modules or token")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    print(f"🚀 Flask server running on port {port}")
    print(f"🌐 Health check: http://localhost:{port}/health")
    print("=" * 60)
    
    flask_app.run(host='0.0.0.0', port=port, debug=False)