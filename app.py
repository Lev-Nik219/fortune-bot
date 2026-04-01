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

# Импортируем Telegram
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
    logger.info("Telegram imported")
    
    # Обработчики команд
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"🌟 *Привет, {user.first_name}!* 🌟\n\n"
            f"Я бот-предсказатель 🔮\n\n"
            f"Я помогу тебе заглянуть в будущее и получить мудрый совет!\n\n"
            f"💰 Стоимость предсказания: 0.10 USDT\n\n"
            f"📝 *Доступные команды:*\n"
            f"/start - начать работу\n"
            f"/predict - получить предсказание\n"
            f"/help - помощь",
            parse_mode='Markdown'
        )
    
    async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /predict"""
        await update.message.reply_text(
            "🔮 *Скоро здесь будет магия!* 🔮\n\n"
            "Бот готов к работе, но требует настройки.\n\n"
            "Сейчас добавляются все функции предсказаний и гороскопов.\n\n"
            "Загляните позже - уже скоро! ✨\n\n"
            "А пока можете попробовать:\n"
            "/start - приветствие\n"
            "/help - справка",
            parse_mode='Markdown'
        )
    
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        await update.message.reply_text(
            "📚 *Помощь* 📚\n\n"
            "🔹 /start - начать работу с ботом\n"
            "🔹 /predict - получить персональное предсказание\n"
            "🔹 /help - показать эту справку\n\n"
            "✨ *Особенности:*\n"
            "• Предсказания генерируются нейросетью\n"
            "• Гороскопы для всех знаков зодиака\n"
            "• Оплата в USDT через CryptoPay\n\n"
            "🚀 Полная версия скоро будет доступна!",
            parse_mode='Markdown'
        )
    
    async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        await update.message.reply_text(
            "🤔 *Я не понимаю эту команду*\n\n"
            "Попробуйте использовать:\n"
            "/start - начать\n"
            "/predict - предсказание\n"
            "/help - помощь",
            parse_mode='Markdown'
        )
        
except Exception as e:
    logger.error(f"Telegram import error: {e}")
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
        logger.info("Setting up Telegram bot...")
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

async def run_telegram_async():
    """Асинхронный запуск Telegram бота"""
    global telegram_app, bot_running
    
    if not telegram_app:
        logger.error("Telegram app not initialized")
        return
    
    try:
        logger.info("Starting Telegram polling...")
        bot_running = True
        # Запускаем polling с обработкой ошибок
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        
        # Держим бота запущенным
        while bot_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Polling error: {e}")
        bot_running = False
    finally:
        if telegram_app:
            await telegram_app.stop()
            await telegram_app.shutdown()

def run_telegram_thread():
    """Запуск Telegram бота в отдельном потоке с event loop"""
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
    """Детальный статус бота"""
    return jsonify({
        'bot_configured': telegram_app is not None,
        'bot_token': bool(config.BOT_TOKEN),
        'telegram_module': TELEGRAM_AVAILABLE,
        'thread_running': bot_running,
        'bot_thread_alive': bot_thread is not None and bot_thread.is_alive() if bot_thread else False
    })

def start_bot():
    """Функция для запуска бота при импорте"""
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
            # Запускаем Telegram бота в отдельном потоке с правильным event loop
            bot_thread = threading.Thread(target=run_telegram_thread, daemon=True)
            bot_thread.start()
            logger.info("Telegram bot thread started")
            print("✅ Telegram bot is running in background")
            
            # Ждем немного, чтобы убедиться, что бот запустился
            time.sleep(2)
            return True
        else:
            logger.error("Failed to setup Telegram bot")
            print("❌ Failed to setup Telegram bot")
            return False
    else:
        logger.warning("Telegram bot not configured")
        print("⚠️ Telegram bot not configured - missing modules or token")
        return False

# Запускаем бота при загрузке модуля
bot_started = start_bot()

if __name__ == '__main__':
    # Запуск Flask
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    print(f"🚀 Flask server running on port {port}")
    print(f"🌐 Health check: https://fortune-bot-3j1x.onrender.com/health")
    print("=" * 60)
    
    flask_app.run(host='0.0.0.0', port=port)