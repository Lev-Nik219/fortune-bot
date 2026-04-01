from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
from database import *
from predictions import generate_prediction, generate_horoscope
from payment import crypto_pay
from zodiac import ZODIAC_SIGNS
from utils import logger
import asyncio

# Состояния для ConversationHandler
ASK_NAME, ASK_GENDER, ASK_QUESTION, ASK_ZODIAC = range(4)

# Хранилище временных данных пользователей
user_data_store = {}
pending_payments = {}

# Клавиатуры
def get_gender_keyboard():
    keyboard = [
        [KeyboardButton("👨 Мужской"), KeyboardButton("👩 Женский")],
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

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🔮 Получить предсказание")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def register_handlers(application):
    """Регистрация всех обработчиков"""
    
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
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(new_prediction_callback, pattern='^new_prediction$'))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ Помощь$'), help_command))
    application.add_handler(MessageHandler(filters.Regex('^🔮 Получить предсказание$'), predict))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    create_user(user.id, user.username, user.first_name, user.last_name)
    logger.info(f"User {user.id} started the bot")
    
    welcome_text = (
        f"🌟 *Привет, {user.first_name}!*\n\n"
        f"✨ Я — *Бот-предсказатель* ✨\n\n"
        f"🔮 Я помогу тебе заглянуть в будущее,\n"
        f"получить мудрый совет и вдохновение!\n\n"
        f"💰 *Стоимость:* 0.10 USDT\n\n"
        f"🎁 *Что ты получишь:*\n"
        f"• 🎯 Персональное предсказание\n"
        f"• 🌟 Юмористический гороскоп\n"
        f"• 💫 Заряд позитива и уверенности\n\n"
        f"👇 *Нажми кнопку ниже, чтобы начать* 👇"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса предсказания"""
    user_id = update.effective_user.id
    user_data_store[user_id] = {}
    
    await update.message.reply_text(
        "✨ *Давай создадим твое персональное предсказание!* ✨\n\n"
        "📝 *Как тебя зовут?*",
        parse_mode='Markdown'
    )
    
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя"""
    user_id = update.effective_user.id
    user_name = update.message.text.strip()
    user_data_store[user_id]['name'] = user_name
    
    await update.message.reply_text(
        f"🌟 *Отлично, {user_name}!* 🌟\n\n"
        f"👤 *Укажи свой пол*",
        parse_mode='Markdown',
        reply_markup=get_gender_keyboard()
    )
    
    return ASK_GENDER

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем пол"""
    user_id = update.effective_user.id
    gender_text = update.message.text
    
    if "Мужской" in gender_text:
        gender = "male"
        gender_emoji = "👨"
    elif "Женский" in gender_text:
        gender = "female"
        gender_emoji = "👩"
    else:
        gender = "other"
        gender_emoji = "⚧️"
    
    user_data_store[user_id]['gender'] = gender
    user_data_store[user_id]['gender_emoji'] = gender_emoji
    
    await update.message.reply_text(
        f"{gender_emoji} *Принято!*\n\n"
        f"💭 *Что тебя волнует?*",
        parse_mode='Markdown',
        reply_markup=get_question_keyboard()
    )
    
    return ASK_QUESTION

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем вопрос"""
    user_id = update.effective_user.id
    user_question = update.message.text.strip()
    
    question_clean = user_question.replace("💼 ", "").replace("💕 ", "").replace("🏃‍♂️ ", "").replace("🎯 ", "").replace("❓ ", "")
    user_data_store[user_id]['question'] = question_clean
    
    keyboard = []
    for sign, info in ZODIAC_SIGNS.items():
        keyboard.append([InlineKeyboardButton(
            f"{info['emoji']} {info['name_ru']}",
            callback_data=f"zodiac_{sign}"
        )])
    
    await update.message.reply_text(
        "🔮 *Выбери свой знак зодиака* 🔮",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ASK_ZODIAC

async def ask_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем знак зодиака и создаем счет"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    zodiac_sign = query.data.replace('zodiac_', '')
    user_data_store[user_id]['zodiac'] = zodiac_sign
    update_user_zodiac(user_id, zodiac_sign)
    
    invoice = crypto_pay.create_invoice(0.10, "USDT", "Предсказание")
    
    if invoice:
        invoice_id = invoice['invoice_id']
        user_data_store[user_id]['invoice_id'] = invoice_id
        pending_payments[invoice_id] = {'user_id': user_id, 'status': 'pending'}
        
        keyboard = [[InlineKeyboardButton(f"💳 Оплатить 0.10 USDT", url=invoice['pay_url'])]]
        
        await query.edit_message_text(
            f"🌟 *Готово!* 🌟\n\n"
            f"💰 *Сумма:* 0.10 USDT\n"
            f"🪙 *Валюта:* USDT (TRC20)\n\n"
            f"🔽 *Нажми на кнопку для оплаты* 🔽\n\n"
            f"⏳ *После оплаты предсказание придет автоматически!*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await context.bot.send_message(
            chat_id=user_id,
            text="🔙 *Главное меню*",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
        asyncio.create_task(check_payment_background(user_id, invoice_id, context))
        return ConversationHandler.END
    else:
        await query.edit_message_text(
            "❌ *Ошибка создания счета*\nПопробуйте позже",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def check_payment_background(user_id, invoice_id, context):
    """Фоновая проверка оплаты"""
    for _ in range(60):  # 5 минут
        await asyncio.sleep(5)
        
        if user_id not in user_data_store:
            return
        
        if crypto_pay.check_payment(invoice_id):
            user_data = user_data_store.get(user_id)
            if user_data and user_data.get('invoice_id') == invoice_id:
                prediction = generate_prediction({
                    'name': user_data['name'],
                    'gender': user_data.get('gender', 'other'),
                    'question': user_data['question'],
                    'zodiac': user_data['zodiac']
                })
                
                horoscope = generate_horoscope(user_data['zodiac'])
                zodiac_emoji = ZODIAC_SIGNS[user_data['zodiac']]['emoji']
                zodiac_name = ZODIAC_SIGNS[user_data['zodiac']]['name_ru']
                
                save_prediction(user_id, 'prediction', prediction, user_data['zodiac'], 0.10)
                save_prediction(user_id, 'horoscope', horoscope, user_data['zodiac'], 0.10)
                
                result_text = (
                    f"✅ *ОПЛАТА ПОЛУЧЕНА!* ✅\n\n"
                    f"✨ *ВОТ ТВОЕ ПРЕДСКАЗАНИЕ* ✨\n\n"
                    f"{prediction}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{zodiac_emoji} *ГОРОСКОП ДЛЯ {zodiac_name.upper()}* {zodiac_emoji}\n\n"
                    f"{horoscope}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💫 *Спасибо, что доверился мне!*"
                )
                
                keyboard = [[InlineKeyboardButton("🔮 Новое предсказание", callback_data="new_prediction")]]
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=result_text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                del user_data_store[user_id]
                del pending_payments[invoice_id]
                return
    
    await context.bot.send_message(
        chat_id=user_id,
        text="⏰ *Время ожидания оплаты истекло*\nПопробуйте заново: /predict",
        parse_mode='Markdown'
    )
    
    if user_id in user_data_store:
        del user_data_store[user_id]
    if invoice_id in pending_payments:
        del pending_payments[invoice_id]

async def new_prediction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка нового предсказания"""
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    return await predict(query, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    user_id = update.effective_user.id
    if user_id in user_data_store:
        invoice_id = user_data_store[user_id].get('invoice_id')
        if invoice_id and invoice_id in pending_payments:
            del pending_payments[invoice_id]
        del user_data_store[user_id]
    
    await update.message.reply_text(
        "❌ *Операция отменена*",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = (
        "📚 *ПОМОЩЬ ПО БОТУ* 📚\n\n"
        "🔮 *Как получить предсказание:*\n\n"
        "1️⃣ Нажми 🔮 Получить предсказание\n"
        "2️⃣ Укажи имя и пол\n"
        "3️⃣ Расскажи, что тебя волнует\n"
        "4️⃣ Выбери знак зодиака\n"
        "5️⃣ Оплати 0.10 USDT\n"
        "6️⃣ Жди автоматического предсказания!\n\n"
        "💰 *Оплата:* USDT (TRC20)\n\n"
        "⚡ *Команды:*\n"
        "/start — Начать\n"
        "/predict — Предсказание\n"
        "/help — Помощь\n"
        "/cancel — Отмена"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())