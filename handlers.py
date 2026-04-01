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
SELECTING_ACTION, TYPING, SHOWING = range(3)
NAME, GENDER, QUESTION, ZODIAC = range(4)

user_data_store = {}
pending_payments = {}

# === КЛАВИАТУРЫ ===
def get_main_keyboard():
    keyboard = [[KeyboardButton("🔮 Получить предсказание")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_gender_keyboard():
    keyboard = [
        [KeyboardButton("👨 Мужской"), KeyboardButton("👩 Женский")],
        [KeyboardButton("⚧️ Другой")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_question_keyboard():
    keyboard = [
        [KeyboardButton("💼 Работа"), KeyboardButton("💕 Любовь")],
        [KeyboardButton("🏃 Здоровье"), KeyboardButton("🎯 Цели")],
        [KeyboardButton("❓ Не знаю")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_start_menu_text(user_name):
    return (
        f"✨ *Добро пожаловать, {user_name}!* ✨\n\n"
        f"🌟 Я — *Бот-предсказатель* 🌟\n"
        f"🔮 Ваш личный проводник в мир тайн и вдохновения.\n\n"
        f"💎 *Что вы получите всего за 0.10 USDT?*\n"
        f"• 🎯 *Персональное предсказание*\n"
        f"• 🌙 *Юмористический гороскоп*\n"
        f"• 💫 *Заряд позитива*\n\n"
        f"👇 *Нажмите кнопку, чтобы начать* 👇"
    )

def get_main_menu_text(user_name):
    return (
        f"🔙 *Главное меню*\n\n"
        f"✨ *{user_name}*, нажмите кнопку, чтобы получить предсказание 👇"
    )

def register_handlers(application):
    """Регистрация обработчиков"""
    logger.info("Registering handlers...")
    
    # Простые команды
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    
    # Conversation handler для предсказания
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('predict', predict),
            MessageHandler(filters.Regex('^🔮 Получить предсказание$'), predict),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_question)],
            ZODIAC: [CallbackQueryHandler(get_zodiac, pattern='^zodiac_')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    
    logger.info("Handlers registered")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username, user.first_name, user.last_name)
    logger.info(f"Start from {user.id}")
    
    await update.message.reply_text(
        get_start_menu_text(user.first_name),
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {}
    logger.info(f"Predict started for {user_id}")
    
    await update.message.reply_text(
        "✨ *Создаём предсказание* ✨\n\n"
        "📝 *Как вас зовут?*",
        parse_mode='Markdown'
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    user_data_store[user_id]['name'] = name
    logger.info(f"Name received: {name}")
    
    await update.message.reply_text(
        f"🌟 *Приятно познакомиться, {name}!* 🌟\n\n"
        f"👤 *Укажите ваш пол:*",
        parse_mode='Markdown',
        reply_markup=get_gender_keyboard()
    )
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if "Мужской" in text:
        gender = "male"
    elif "Женский" in text:
        gender = "female"
    else:
        gender = "other"
    
    user_data_store[user_id]['gender'] = gender
    logger.info(f"Gender received: {gender}")
    
    await update.message.reply_text(
        f"✅ *Принято!*\n\n"
        f"💭 *Что вас волнует?*",
        parse_mode='Markdown',
        reply_markup=get_question_keyboard()
    )
    return QUESTION

async def get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Очищаем от эмодзи
    question = text.replace("💼 ", "").replace("💕 ", "").replace("🏃 ", "").replace("🎯 ", "").replace("❓ ", "")
    user_data_store[user_id]['question'] = question
    logger.info(f"Question received: {question}")
    
    # Создаем клавиатуру со знаками зодиака
    keyboard = []
    for sign, info in ZODIAC_SIGNS.items():
        keyboard.append([InlineKeyboardButton(
            f"{info['emoji']} {info['name_ru']}",
            callback_data=f"zodiac_{sign}"
        )])
    
    await update.message.reply_text(
        "🔮 *Выберите знак зодиака* 🔮",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ZODIAC

async def get_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    zodiac = query.data.replace('zodiac_', '')
    user_data_store[user_id]['zodiac'] = zodiac
    update_user_zodiac(user_id, zodiac)
    logger.info(f"Zodiac received: {zodiac}")
    
    user_data = user_data_store[user_id]
    
    # В тестовом режиме или для демо показываем предсказание сразу
    if config.TEST_MODE:
        logger.info(f"TEST MODE: Generating prediction for {user_id}")
        
        gender = user_data.get('gender', 'other')
        if gender == 'male':
            dear = "Дорогой"
        elif gender == 'female':
            dear = "Дорогая"
        else:
            dear = "Дорогой(ая)"
        
        prediction = generate_prediction({
            'name': user_data['name'],
            'gender': gender,
            'question': user_data['question'],
            'zodiac': zodiac
        })
        horoscope = generate_horoscope(zodiac)
        
        zodiac_emoji = ZODIAC_SIGNS[zodiac]['emoji']
        zodiac_name = ZODIAC_SIGNS[zodiac]['name_ru']
        
        save_prediction(user_id, 'prediction', prediction, zodiac, 0.10)
        save_prediction(user_id, 'horoscope', horoscope, zodiac, 0.10)
        
        result_text = (
            f"✨ *ВАШЕ ПРЕДСКАЗАНИЕ* ✨\n\n"
            f"{prediction}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{zodiac_emoji} *ГОРОСКОП ДЛЯ {zodiac_name.upper()}* {zodiac_emoji}\n\n"
            f"{horoscope}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{dear} *{user_data['name']}*, 💫 благодарю за доверие!"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_menu")]]
        
        await query.edit_message_text(
            result_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        del user_data_store[user_id]
        return ConversationHandler.END
    
    # Реальная оплата
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
            f"🔽 *Нажмите для оплаты* 🔽\n\n"
            f"⏳ *После оплаты предсказание придёт автоматически*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        asyncio.create_task(check_payment(user_id, invoice_id, context))
        return ConversationHandler.END
    else:
        await query.edit_message_text(
            "❌ *Ошибка создания счёта*\nПопробуйте позже",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def check_payment(user_id, invoice_id, context):
    for _ in range(60):
        await asyncio.sleep(5)
        if user_id not in user_data_store:
            return
        
        if crypto_pay.check_payment(invoice_id):
            user_data = user_data_store.get(user_id)
            if user_data:
                gender = user_data.get('gender', 'other')
                if gender == 'male':
                    dear = "Дорогой"
                else:
                    dear = "Дорогая"
                
                prediction = generate_prediction({
                    'name': user_data['name'],
                    'gender': gender,
                    'question': user_data['question'],
                    'zodiac': user_data['zodiac']
                })
                horoscope = generate_horoscope(user_data['zodiac'])
                
                zodiac_emoji = ZODIAC_SIGNS[user_data['zodiac']]['emoji']
                zodiac_name = ZODIAC_SIGNS[user_data['zodiac']]['name_ru']
                
                result_text = (
                    f"✅ *ОПЛАТА ПОЛУЧЕНА!* ✅\n\n"
                    f"✨ *ПРЕДСКАЗАНИЕ* ✨\n\n"
                    f"{prediction}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{zodiac_emoji} *ГОРОСКОП ДЛЯ {zodiac_name.upper()}* {zodiac_emoji}\n\n"
                    f"{horoscope}"
                )
                
                keyboard = [[InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_menu")]]
                
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
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    if user_id in user_data_store:
        del user_data_store[user_id]

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    name = user[2] if user else query.from_user.first_name
    
    await context.bot.send_message(
        chat_id=user_id,
        text=get_main_menu_text(name),
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]
    
    user = get_user(user_id)
    name = user[2] if user else update.effective_user.first_name
    
    await update.message.reply_text(
        f"❌ *Отменено*\n\n{get_main_menu_text(name)}",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *ПОМОЩЬ* 📚\n\n"
        "🔮 *Как получить предсказание:*\n"
        "1️⃣ Нажмите кнопку «🔮 Получить предсказание»\n"
        "2️⃣ Укажите имя\n"
        "3️⃣ Выберите пол\n"
        "4️⃣ Напишите, что вас волнует\n"
        "5️⃣ Выберите знак зодиака\n"
        "6️⃣ Оплатите 0.10 USDT\n\n"
        "💰 *Оплата:* USDT (TRC20)\n\n"
        "⚡ *Команды:*\n"
        "/start — начать\n"
        "/predict — предсказание\n"
        "/help — помощь\n"
        "/cancel — отмена"
    )
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )