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
            "🌟 *Привет!* 🌟\n\n"
            "Я бот-предсказатель 🔮\n\n"
            "Я помогу тебе заглянуть в будущее и получить мудрый совет!\n\n"
            "💰 Стоимость предсказания: 0.10 USDT\n\n"
            "📝 *Чтобы начать, нажми:*\n"
            "/predict - получить предсказание\n"
            "/help - помощь",
            parse_mode='Markdown'
        )
    
    async def predict(update: Update, context):
        await update.message.reply_text(
            "🔮 *Скоро здесь будет магия!*\n\n"
            "Полная версия бота с предсказаниями и гороскопами уже готова!\n\n"
            "Сейчас бот настраивается. Загляните позже ✨",
            parse_mode='Markdown'
        )
    
    async def help_command(update: Update, context):
        await update.message.reply_text(
            "📚 *Помощь* 📚\n\n"
            "🔹 /start - начать работу\n"
            "🔹 /predict - получить предсказание\n"
            "🔹 /help - показать эту справку\n\n"
            "✨ Бот работает на нейросетях и генерирует уникальные предсказания!",
            parse_mode='Markdown'
        )
    
    async def echo(update: Update, context):
        await update.message.reply_text(
            "🤔 Я не понимаю эту команду.\n\n"
            "Попробуйте:\n"
            "/start - начать\n"
            "/predict - предсказание\n"
            "/help - помощь"
        )
        
except Exception as e:
    logger.error(f"Telegram import error: {e}")
    TELEGRAM_AVAILABLE = False
    
    async def start(update, context):
        pass
    async def predict(update, context):
        pass
    async def help_command(update, context):
        pass
    async def echo(update, context):
        pass

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
        logger.info(f"Setting up Telegram bot...")
        telegram_app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Добавляем обработчики
        telegram_app.add_handler(CommandHandler('start', start))
        telegram_app.add_handler(CommandHandler('predict', predict))
        telegram_app.add_handler(CommandHandler('help', help_command))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        logger.info("Telegram bot configured successfully")
        return True
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return False

def run_telegram():
    """Запуск Telegram бота"""
    global telegram_app
    
    if not telegram_app:
        logger.error("Telegram app not initialized")
        return
    
    try:
        logger.info("Starting Telegram polling...")
        # Запускаем polling
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
        'bot_token_set': bool(config.BOT_TOKEN),
        'bot_running': telegram_app is not None
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
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database error: {e}")
    
    # Настройка и запуск Telegram
    if TELEGRAM_AVAILABLE and config.BOT_TOKEN:
        if setup_telegram():
            # Запускаем Telegram бота в отдельном потоке
            bot_thread = threading.Thread(target=run_telegram, daemon=True)
            bot_thread.start()
            logger.info("Telegram bot thread started")
            print("✅ Telegram bot is running in background")
        else:
            logger.error("Failed to setup Telegram bot")
            print("❌ Failed to setup Telegram bot")
    else:
        logger.warning("Telegram bot not configured")
        print("⚠️ Telegram bot not configured - missing modules or token")
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    print(f"🚀 Flask server running on port {port}")
    print(f"🌐 Health check: https://fortune-bot-3j1x.onrender.com/health")
    print("=" * 60)
    
    flask_app.run(host='0.0.0.0', port=port)