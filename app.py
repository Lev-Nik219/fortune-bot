import os
import sys
import time
import threading
import asyncio
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
    class config:
        BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        CRYPTOPAY_TOKEN = os.getenv('CRYPTOPAY_TOKEN', '')
        HF_API_KEY = os.getenv('HF_API_KEY', '')
        TEST_MODE = False
        PRICE_USDT = 0.10

# Импортируем обработчики
try:
    from handlers import register_handlers
    TELEGRAM_AVAILABLE = True
    logger.info("Handlers imported successfully")
except Exception as e:
    logger.error(f"Handlers import error: {e}")
    TELEGRAM_AVAILABLE = False

# Создаем Flask приложение
flask_app = Flask(__name__)

# Создаем Telegram приложение
telegram_app = None
bot_thread = None
bot_running = False

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
        from telegram.ext import Application
        logger.info("Setting up Telegram bot...")
        telegram_app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Регистрируем все обработчики
        register_handlers(telegram_app)
        
        logger.info("Telegram bot configured successfully")
        return True
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return False

async def run_telegram_async():
    """Асинхронный запуск Telegram бота"""
    global telegram_app, bot_running
    
    if not telegram_app:
        logger.error("Telegram app not initialized")
        return
    
    try:
        logger.info("Starting Telegram polling...")
        bot_running = True
        
        # Запускаем polling
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("Telegram polling started successfully")
        
        # Держим бота запущенным
        while bot_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Polling error: {e}")
        bot_running = False
    finally:
        if telegram_app:
            try:
                await telegram_app.updater.stop()
                await telegram_app.stop()
                await telegram_app.shutdown()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

def run_telegram_thread():
    """Запуск Telegram бота в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_telegram_async())
    except Exception as e:
        logger.error(f"Thread error: {e}")
    finally:
        loop.close()

@flask_app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Fortune Bot is running!',
        'python_version': sys.version,
        'telegram_available': TELEGRAM_AVAILABLE,
        'bot_token_set': bool(config.BOT_TOKEN),
        'bot_running': bot_running
    })

@flask_app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

@flask_app.route('/status')
def status():
    return jsonify({
        'bot_configured': telegram_app is not None,
        'bot_token': bool(config.BOT_TOKEN),
        'telegram_module': TELEGRAM_AVAILABLE,
        'thread_running': bot_running,
        'bot_thread_alive': bot_thread is not None and bot_thread.is_alive() if bot_thread else False
    })

def start_bot():
    """Запуск бота"""
    global bot_thread, bot_running
    
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
            bot_thread = threading.Thread(target=run_telegram_thread, daemon=True)
            bot_thread.start()
            logger.info("Telegram bot thread started")
            print("✅ Telegram bot is running in background")
            time.sleep(3)
            return True
        else:
            logger.error("Failed to setup Telegram bot")
            print("❌ Failed to setup Telegram bot")
            return False
    else:
        logger.warning("Telegram bot not configured")
        print("⚠️ Telegram bot not configured - missing modules or token")
        return False

# Запускаем бота
start_bot()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    flask_app.run(host='0.0.0.0', port=port)