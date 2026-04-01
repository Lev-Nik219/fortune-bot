from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
from database import init_db, create_user, update_user_zodiac, save_prediction, get_user
from predictions import generate_prediction, generate_horoscope
from payment import crypto_pay
from zodiac import ZODIAC_SIGNS
from utils import logger
import asyncio
import traceback

# Состояния
ASK_NAME, ASK_GENDER, ASK_QUESTION, ASK_ZODIAC = range(4)

user_data_store = {}
pending_payments = {}

# === КЛАВИАТУРЫ ===
def get_gender_keyboard():
    keyboard = [
        [KeyboardButton("👨‍🦰 Мужской"), KeyboardButton("👩‍🦰 Женский")],
        [KeyboardButton("⚧️ Другой / Не указывать")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_question_keyboard():
    keyboard = [
        [KeyboardButton("💼 Работа и карьера"), KeyboardButton("💕 Отношения и любовь")],
        [KeyboardButton("🏃‍♂️ Здоровье и энергия"), KeyboardButton("🎯 Цели и мечты")],
        [KeyboardButton("❓ Не знаю / Просто так")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_keyboard():
    keyboard = [[KeyboardButton("🔮 Получить предсказание")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_start_menu_text(user_name):
    return (
        f"✨ *Добро пожаловать, {user_name}!* ✨\n\n"
        f"🌟 Я — *Бот-предсказатель* 🌟\n"
        f"🔮 Ваш личный проводник в мир тайн и вдохновения.\n\n"
        f"💎 *Что вы получите всего за 0.10 USDT?*\n"
        f"• 🎯 *Персональное предсказание* – ответ на ваш вопрос\n"
        f"• 🌙 *Юмористический гороскоп* – шутливый взгляд на день\n"
        f"• 💫 *Заряд позитива* – энергия на весь день\n\n"
        f"👇 *Нажмите кнопку, чтобы начать* 👇"
    )

def get_main_menu_text(user_name):
    return (
        f"🔙 *Главное меню*\n\n"
        f"✨ *Добро пожаловать обратно, {user_name}!* ✨\n\n"
        f"🌟 Я — *Бот-предсказатель* 🌟\n"
        f"🔮 Ваш личный проводник в мир тайн и вдохновения.\n\n"
        f"💎 *Что вы получите всего за 0.10 USDT?*\n"
        f"• 🎯 *Персональное предсказание* – ответ на ваш вопрос\n"
        f"• 🌙 *Юмористический гороскоп* – шутливый взгляд на день\n"
        f"• 💫 *Заряд позитива* – энергия на весь день\n\n"
        f"👇 *Нажмите кнопку, чтобы получить новое предсказание* 👇"
    )

def register_handlers(application):
    """Регистрация обработчиков"""
    logger.info("Registering handlers...")
    
    # Простой обработчик для команды /start
    async def simple_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        create_user(user.id, user.username, user.first_name, user.last_name)
        logger.info(f"Start command received from {user.id}")
        await update.message.reply_text(
            f"Привет, {user.first_name}! Бот работает. /help - помощь",
            parse_mode='Markdown'
        )
    
    # Простой обработчик для /help
    async def simple_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Доступные команды:\n/start - начать\n/predict - предсказание\n/help - помощь"
        )
    
    # Простой обработчик для /predict
    async def simple_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Функция предсказаний временно недоступна. Идет настройка.")
    
    # Простой обработчик для текстовых сообщений
    async def simple_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Вы написали: {update.message.text}\nИспользуйте /start или /help")
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler('start', simple_start))
    application.add_handler(CommandHandler('help', simple_help))
    application.add_handler(CommandHandler('predict', simple_predict))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, simple_echo))
    
    logger.info("Simple handlers registered")