from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
import config
from handlers import *
from database import init_db
from utils import logger
import threading
import time
import os

# Создаем Flask приложение
flask_app = Flask(__name__)

# Создаем Telegram приложение
telegram_app = Application.builder().token(config.BOT_TOKEN).build()

def setup_handlers():
    """Настройка всех обработчиков"""
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
        # Используем run_polling без параметра allowed_updates для совместимости
        telegram_app.run_polling()
    except Exception as e:
        logger.error(f"Error in telegram polling: {e}")

@flask_app.route('/')
def index():
    """Главная страница для проверки работы"""
    return jsonify({
        'status': 'ok',
        'message': 'Fortune Bot is running!',
        'bot_username': '@ln_Fortune_Bot'
    })

@flask_app.route('/health')
def health():
    """Эндпоинт для проверки здоровья"""
    return jsonify({
        'status': 'healthy',
        'bot_running': True,
        'timestamp': time.time()
    })

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook для Telegram"""
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        telegram_app.update_queue.put(update)
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Инициализация базы данных
    init_db()
    
    # Настройка обработчиков
    setup_handlers()
    
    # Запускаем Telegram бота в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    flask_app.run(host='0.0.0.0', port=port)