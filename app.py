import os
import sys
import time
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
print("Starting Fortune Bot...")
print("=" * 60)

# Импортируем настройки
try:
    import config
    from database import init_db
    logger.info("Config and database imported")
except Exception as e:
    logger.error(f"Import error: {e}")
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
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    TELEGRAM_AVAILABLE = True
    logger.info("Telegram imported")
    
    # Простые обработчики
    async def start(update: Update, context):
        await update.message.reply_text(
            "🌟 *Привет!*\n\nЯ бот-предсказатель.\n"
            "Нажми /predict чтобы начать",
            parse_mode='Markdown'
        )
    
    async def help_command(update: Update, context):
        await update.message.reply_text(
            "📚 *Помощь*\n\n"
            "/start - начать\n"
            "/predict - получить предсказание\n"
            "/help - помощь",
            parse_mode='Markdown'
        )
    
    async def echo(update: Update, context):
        await update.message.reply_text(
            "Я пока не понимаю эту команду.\n"
            "Используйте /start или /help"
        )
        
except Exception as e:
    logger.error(f"Telegram import error: {e}")
    TELEGRAM_AVAILABLE = False
    
    async def start(update, context):
        pass
    async def help_command(update, context):
        pass
    async def echo(update, context):
        pass

# Создаем Flask приложение
flask_app = Flask(__name__)

# Создаем Telegram приложение
telegram_app = None

def setup_telegram():
    """Настройка Telegram бота"""
    global telegram_app
    
    if not TELEGRAM_AVAILABLE:
        logger.error("Telegram not available")
        return False
    
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not set")
        return False
    
    try:
        logger.info("Setting up Telegram bot...")
        telegram_app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Добавляем обработчики
        telegram_app.add_handler(CommandHandler('start', start))
        telegram_app.add_handler(CommandHandler('help', help_command))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        logger.info("Telegram bot configured")
        return True
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return False

def run_telegram():
    """Запуск Telegram бота"""
    global telegram_app
    
    if not telegram_app:
        return
    
    try:
        logger.info("Starting Telegram polling...")
        telegram_app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Polling error: {e}")

@flask_app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Fortune Bot is running!',
        'python_version': sys.version,
        'telegram_available': TELEGRAM_AVAILABLE,
        'bot_token_set': bool(config.BOT_TOKEN)
    })

@flask_app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

if __name__ == '__main__':
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Telegram available: {TELEGRAM_AVAILABLE}")
    print(f"Bot token: {'✅ Set' if config.BOT_TOKEN else '❌ Missing'}")
    print("=" * 60)
    
    # Инициализация базы данных
    try:
        init_db()
        logger.info("Database OK")
    except Exception as e:
        logger.error(f"DB error: {e}")
    
    # Настройка Telegram
    if TELEGRAM_AVAILABLE and config.BOT_TOKEN:
        if setup_telegram():
            import threading
            bot_thread = threading.Thread(target=run_telegram, daemon=True)
            bot_thread.start()
            logger.info("Bot thread started")
            print("✅ Telegram bot is running")
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Flask on port {port}")
    flask_app.run(host='0.0.0.0', port=port)