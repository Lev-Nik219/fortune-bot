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
NAME, GENDER, QUESTION, ZODIAC = range(4)

user_data_store = {}
pending_payments = {}

# === КРАСИВЫЕ КЛАВИАТУРЫ ===
def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = [[KeyboardButton("🔮 Получить предсказание")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_gender_keyboard():
    """Клавиатура выбора пола"""
    keyboard = [
        [KeyboardButton("👨‍🦰 Мужской"), KeyboardButton("👩‍🦰 Женский")],
        [KeyboardButton("⚧️ Другой / Не указывать")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_question_keyboard():
    """Клавиатура выбора вопроса"""
    keyboard = [
        [KeyboardButton("💼 Работа и карьера"), KeyboardButton("💕 Отношения и любовь")],
        [KeyboardButton("🏃‍♂️ Здоровье и энергия"), KeyboardButton("🎯 Цели и мечты")],
        [KeyboardButton("❓ Не знаю / Просто так")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_start_menu_text(user_name):
    """Стартовое приветственное меню"""
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
    """Основное меню для возврата"""
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
    """Регистрация всех обработчиков"""
    logger.info("=" * 50)
    logger.info("REGISTERING HANDLERS")
    logger.info("=" * 50)
    
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
    
    logger.info("All handlers registered successfully")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    create_user(user.id, user.username, user.first_name, user.last_name)
    logger.info(f"Start command from user {user.id}")
    
    await update.message.reply_text(
        get_start_menu_text(user.first_name),
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса предсказания"""
    user_id = update.effective_user.id
    user_data_store[user_id] = {}
    logger.info(f"Predict started for user {user_id}")
    
    await update.message.reply_text(
        "✨ *Создаём ваше персональное предсказание* ✨\n\n"
        "📝 *Как вас зовут?* (можно указать имя или псевдоним)",
        parse_mode='Markdown'
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя пользователя"""
    user_id = update.effective_user.id
    name = update.message.text.strip()
    user_data_store[user_id]['name'] = name
    logger.info(f"User {user_id} entered name: {name}")
    
    await update.message.reply_text(
        f"🌟 *Приятно познакомиться, {name}!* 🌟\n\n"
        f"👤 *Укажите ваш пол* – это поможет сделать предсказание точнее.",
        parse_mode='Markdown',
        reply_markup=get_gender_keyboard()
    )
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем пол пользователя"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if "Мужской" in text:
        gender = "male"
        gender_emoji = "👨‍🦰"
    elif "Женский" in text:
        gender = "female"
        gender_emoji = "👩‍🦰"
    else:
        gender = "other"
        gender_emoji = "⚧️"
    
    user_data_store[user_id]['gender'] = gender
    user_data_store[user_id]['gender_emoji'] = gender_emoji
    logger.info(f"User {user_id} selected gender: {gender}")
    
    await update.message.reply_text(
        f"{gender_emoji} *Принято!*\n\n"
        f"💭 *Расскажите, что вас волнует?* Выберите вариант или напишите свой вопрос.",
        parse_mode='Markdown',
        reply_markup=get_question_keyboard()
    )
    return QUESTION

async def get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем вопрос пользователя"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Очищаем от эмодзи кнопок
    question = text.replace("💼 ", "").replace("💕 ", "").replace("🏃‍♂️ ", "").replace("🎯 ", "").replace("❓ ", "")
    user_data_store[user_id]['question'] = question
    logger.info(f"User {user_id} question: {question}")
    
    # Создаем красивую inline-клавиатуру со знаками зодиака
    keyboard = []
    for sign, info in ZODIAC_SIGNS.items():
        keyboard.append([InlineKeyboardButton(
            f"{info['emoji']} {info['name_ru']}",
            callback_data=f"zodiac_{sign}"
        )])
    
    await update.message.reply_text(
        "🔮 *Выберите свой знак зодиака* 🔮\n\n"
        "Это нужно для вашего персонального гороскопа.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ZODIAC

async def get_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем выбор знака зодиака и создаем инвойс"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        zodiac = query.data.replace('zodiac_', '')
        user_data_store[user_id]['zodiac'] = zodiac
        update_user_zodiac(user_id, zodiac)
        logger.info(f"User {user_id} selected zodiac: {zodiac}")
        
        user_data = user_data_store[user_id]
        
        # В ТЕСТОВОМ РЕЖИМЕ - показываем предсказание без оплаты
        if config.TEST_MODE:
            logger.info(f"TEST MODE: Generating prediction for user {user_id} (no payment)")
            
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
                f"{dear} *{user_data['name']}*, 💫 благодарю за доверие!\n"
                f"🔮 Если хотите узнать больше, нажмите кнопку ниже."
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_menu")]]
            
            await query.edit_message_text(
                result_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            del user_data_store[user_id]
            return ConversationHandler.END
        
        # РЕАЛЬНАЯ ОПЛАТА
        logger.info(f"Creating invoice for user {user_id}")
        invoice = crypto_pay.create_invoice(0.10, "USDT", "Предсказание")
        
        if invoice:
            invoice_id = invoice['invoice_id']
            user_data_store[user_id]['invoice_id'] = invoice_id
            pending_payments[invoice_id] = {
                'user_id': user_id,
                'status': 'pending',
                'created_at': asyncio.get_event_loop().time()
            }
            
            keyboard = [[InlineKeyboardButton(f"💳 Оплатить 0.10 USDT", url=invoice['pay_url'])]]
            
            await query.edit_message_text(
                f"🌟 *Готово!* 🌟\n\n"
                f"💰 *Сумма к оплате:* 0.10 USDT\n"
                f"🪙 *Валюта:* USDT (TRC20)\n\n"
                f"🔽 *Нажмите на кнопку для оплаты* 🔽\n\n"
                f"⏳ *После подтверждения оплаты предсказание придёт автоматически.*\n"
                f"Это займёт 1–2 минуты.\n\n"
                f"💫 *Спасибо, что выбираете нас!*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            asyncio.create_task(check_payment_background(user_id, invoice_id, context))
            return ConversationHandler.END
        else:
            await query.edit_message_text(
                "❌ *Ошибка создания счёта*\n\nПожалуйста, попробуйте позже.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error in get_zodiac: {e}")
        logger.error(traceback.format_exc())
        return ConversationHandler.END

async def check_payment_background(user_id, invoice_id, context):
    """Фоновая проверка оплаты"""
    max_attempts = 60  # 5 минут
    
    for attempt in range(max_attempts):
        await asyncio.sleep(5)
        
        if user_id not in user_data_store:
            return
        
        user_data = user_data_store.get(user_id)
        if not user_data or user_data.get('invoice_id') != invoice_id:
            return
        
        try:
            is_paid = crypto_pay.check_payment(invoice_id)
            
            if is_paid:
                logger.info(f"✅ Payment confirmed for user {user_id}")
                
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
                    'zodiac': user_data['zodiac']
                })
                
                horoscope = generate_horoscope(user_data['zodiac'])
                
                zodiac_emoji = ZODIAC_SIGNS[user_data['zodiac']]['emoji']
                zodiac_name = ZODIAC_SIGNS[user_data['zodiac']]['name_ru']
                
                save_prediction(user_id, 'prediction', prediction, user_data['zodiac'], 0.10)
                save_prediction(user_id, 'horoscope', horoscope, user_data['zodiac'], 0.10)
                
                result_text = (
                    f"✅ *ОПЛАТА ПОЛУЧЕНА!* ✅\n\n"
                    f"✨ *ВАШЕ ПРЕДСКАЗАНИЕ* ✨\n\n"
                    f"{prediction}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{zodiac_emoji} *ГОРОСКОП ДЛЯ {zodiac_name.upper()}* {zodiac_emoji}\n\n"
                    f"{horoscope}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{dear} *{user_data['name']}*, 💫 благодарю за доверие!\n"
                    f"🔮 Если хотите узнать больше, нажмите кнопку ниже."
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
                
        except Exception as e:
            logger.error(f"Error checking payment: {e}")
            continue
    
    # Таймаут
    logger.warning(f"Payment timeout for user {user_id}")
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="⏰ *Время ожидания оплаты истекло (5 минут)*\n\nПопробуйте заново, нажав /predict.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception:
        pass
    
    if user_id in user_data_store:
        del user_data_store[user_id]
    if invoice_id in pending_payments:
        del pending_payments[invoice_id]

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    if user:
        user_name = user[2]  # first_name
    else:
        user_name = query.from_user.first_name
    
    await context.bot.send_message(
        chat_id=user_id,
        text=get_main_menu_text(user_name),
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    user_id = update.effective_user.id
    if user_id in user_data_store:
        invoice_id = user_data_store[user_id].get('invoice_id')
        if invoice_id and invoice_id in pending_payments:
            del pending_payments[invoice_id]
        del user_data_store[user_id]
    
    user = get_user(user_id)
    if user:
        user_name = user[2]
    else:
        user_name = update.effective_user.first_name
    
    await update.message.reply_text(
        get_main_menu_text(user_name),
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = (
        "📚 *ПОМОЩЬ ПО БОТУ* 📚\n\n"
        "🔮 *Как получить предсказание:*\n\n"
        "1️⃣ Нажмите кнопку «🔮 Получить предсказание»\n"
        "2️⃣ Укажите имя и пол\n"
        "3️⃣ Расскажите, что вас волнует (или выберите вариант)\n"
        "4️⃣ Выберите знак зодиака\n"
        "5️⃣ Оплатите 0.10 USDT через CryptoPay\n"
        "6️⃣ Ждите автоматической доставки предсказания!\n\n"
        "💰 *Оплата:* USDT (сеть TRC20), сумма 0.10 USDT\n\n"
        "⚡ *Команды:*\n"
        "/start — начать работу\n"
        "/predict — получить предсказание\n"
        "/help — эта справка\n"
        "/cancel — отменить текущую операцию\n\n"
        "✨ *Приятного использования!*"
    )
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )