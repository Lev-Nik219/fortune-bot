from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
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
# Хранилище для отслеживания оплат
pending_payments = {}

# Клавиатуры
def get_gender_keyboard():
    """Клавиатура для выбора пола"""
    keyboard = [
        [KeyboardButton("👨 Мужской"), KeyboardButton("👩 Женский")],
        [KeyboardButton("⚧️ Другой / Не указывать")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_question_keyboard():
    """Клавиатура для быстрого выбора вопроса"""
    keyboard = [
        [KeyboardButton("💼 Работа и карьера"), KeyboardButton("💕 Отношения и любовь")],
        [KeyboardButton("🏃‍♂️ Здоровье и энергия"), KeyboardButton("🎯 Цели и мечты")],
        [KeyboardButton("❓ Не знаю / Просто так")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_main_keyboard():
    """Главная клавиатура с командами"""
    keyboard = [
        [KeyboardButton("🔮 Получить предсказание")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем пользователя в БД
    create_user(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )
    
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
    
    # Отправляем приветствие с главной клавиатурой
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def handle_main_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок главного меню"""
    text = update.message.text
    
    if text == "🔮 Получить предсказание":
        return await predict(update, context)
    elif text == "ℹ️ Помощь":
        return await help_command(update, context)

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса предсказания"""
    user_id = update.effective_user.id
    
    # Создаем временное хранилище для данных пользователя
    user_data_store[user_id] = {}
    
    await update.message.reply_text(
        "✨ *Давай создадим твое персональное предсказание!* ✨\n\n"
        "📝 *Как тебя зовут?*\n"
        "(Можно указать имя или псевдоним, который хочешь услышать в предсказании)",
        parse_mode='Markdown'
    )
    
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя пользователя"""
    user_id = update.effective_user.id
    user_name = update.message.text.strip()
    
    user_data_store[user_id]['name'] = user_name
    
    await update.message.reply_text(
        f"🌟 *Отлично, {user_name}!* 🌟\n\n"
        f"👤 *Укажи свой пол*\n"
        f"Это поможет сделать предсказание более точным",
        parse_mode='Markdown',
        reply_markup=get_gender_keyboard()
    )
    
    return ASK_GENDER

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем пол пользователя"""
    user_id = update.effective_user.id
    gender_text = update.message.text
    
    # Определяем пол
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
        f"💭 *Теперь расскажи, что тебя волнует?*\n\n"
        f"Выбери вариант из кнопок или напиши свой вопрос:",
        parse_mode='Markdown',
        reply_markup=get_question_keyboard()
    )
    
    return ASK_QUESTION

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем вопрос пользователя"""
    user_id = update.effective_user.id
    user_question = update.message.text.strip()
    
    # Очищаем эмодзи из вопроса если они есть
    question_clean = user_question.replace("💼 ", "").replace("💕 ", "").replace("🏃‍♂️ ", "").replace("🎯 ", "").replace("❓ ", "")
    
    user_data_store[user_id]['question'] = question_clean
    
    # Создаем inline клавиатуру с знаками зодиака
    keyboard = []
    for sign, info in ZODIAC_SIGNS.items():
        keyboard.append([InlineKeyboardButton(
            f"{info['emoji']} {info['name_ru']}",
            callback_data=f"zodiac_{sign}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔮 *Выбери свой знак зодиака* 🔮\n\n"
        "Это нужно для твоего персонального гороскопа!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return ASK_ZODIAC

async def ask_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем знак зодиака и создаем счет"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    zodiac_sign = query.data.replace('zodiac_', '')
    
    user_data_store[user_id]['zodiac'] = zodiac_sign
    
    # Сохраняем знак зодиака в БД
    update_user_zodiac(user_id, zodiac_sign)
    
    logger.info(f"User {user_id} selected zodiac: {zodiac_sign}")
    
    # Создаем счет на оплату в USDT
    amount = 0.10
    invoice = crypto_pay.create_invoice(amount, "USDT", "Предсказание")
    
    if invoice:
        invoice_id = invoice['invoice_id']
        user_data_store[user_id]['invoice_id'] = invoice_id
        
        # Сохраняем в pending payments для отслеживания
        pending_payments[invoice_id] = {
            'user_id': user_id,
            'status': 'pending',
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # Inline кнопка для оплаты
        keyboard = [[
            InlineKeyboardButton(
                f"💳 Оплатить {amount} USDT",
                url=invoice['pay_url']
            )
        ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение с информацией об оплате
        await query.edit_message_text(
            f"🌟 *Готово!* 🌟\n\n"
            f"✨ Я подготовил для тебя персональное предсказание и гороскоп.\n\n"
            f"💰 *Сумма:* 0.10 USDT\n"
            f"🪙 *Валюта:* USDT (TRC20)\n\n"
            f"🔽 *Нажми на кнопку ниже, чтобы оплатить* 🔽\n\n"
            f"⏳ *После оплаты предсказание появится автоматически!*\n"
            f"Это может занять 1-2 минуты.\n\n"
            f"💫 *Спасибо, что выбираешь нас!*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Возвращаем главную клавиатуру
        await context.bot.send_message(
            chat_id=user_id,
            text="🔙 *Главное меню*",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
        # Запускаем фоновую проверку оплаты
        asyncio.create_task(check_payment_background(user_id, invoice_id, context))
        
        # Завершаем диалог
        return ConversationHandler.END
    else:
        logger.error(f"Failed to create invoice for user {user_id}")
        await query.edit_message_text(
            "❌ *Извините, произошла ошибка*\n\n"
            "Не удалось создать счет для оплаты. Пожалуйста, попробуйте позже.\n\n"
            "Нажмите /start чтобы начать заново",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def check_payment_background(user_id, invoice_id, context):
    """
    Фоновая проверка оплаты
    """
    logger.info(f"Starting background payment check for user {user_id}, invoice {invoice_id}")
    
    # Проверяем каждые 5 секунд в течение 5 минут
    for attempt in range(60):
        await asyncio.sleep(5)
        
        # Проверяем, существует ли еще пользователь в хранилище
        if user_id not in user_data_store:
            logger.info(f"User {user_id} cancelled or completed operation")
            return
        
        # Проверяем статус оплаты
        try:
            if crypto_pay.check_payment(invoice_id):
                logger.info(f"Payment confirmed for user {user_id}, invoice {invoice_id}")
                
                # Получаем данные пользователя
                user_data = user_data_store.get(user_id)
                if user_data and user_data.get('invoice_id') == invoice_id:
                    # Генерируем предсказания
                    prediction = generate_prediction({
                        'name': user_data['name'],
                        'gender': user_data.get('gender', 'other'),  # Добавляем пол
                        'question': user_data['question'],
                        'zodiac': user_data['zodiac']
                    })
                    
                    horoscope = generate_horoscope(user_data['zodiac'])
                    
                    zodiac_emoji = ZODIAC_SIGNS[user_data['zodiac']]['emoji']
                    zodiac_name = ZODIAC_SIGNS[user_data['zodiac']]['name_ru']
                    
                    # Сохраняем в БД
                    save_prediction(
                        user_id,
                        'prediction',
                        prediction,
                        user_data['zodiac'],
                        0.10
                    )
                    
                    save_prediction(
                        user_id,
                        'horoscope',
                        horoscope,
                        user_data['zodiac'],
                        0.10
                    )
                    
                    # Формируем ответ с inline кнопкой для нового предсказания
                    result_text = (
                        f"✅ *ОПЛАТА ПОЛУЧЕНА!* ✅\n\n"
                        f"✨ *ВОТ ТВОЕ ПРЕДСКАЗАНИЕ* ✨\n\n"
                        f"{prediction}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"{zodiac_emoji} *ГОРОСКОП ДЛЯ {zodiac_name.upper()}* {zodiac_emoji}\n\n"
                        f"{horoscope}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"💫 *Спасибо, что доверился мне!*\n\n"
                        f"🌟 Хочешь узнать больше?"
                    )
                    
                    # Inline кнопка для нового предсказания
                    keyboard = [[InlineKeyboardButton("🔮 Новое предсказание", callback_data="new_prediction")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Отправляем сообщение с предсказанием
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=result_text,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                    except Exception as e:
                        logger.error(f"Error sending prediction to user {user_id}: {e}")
                    
                    # Очищаем временные данные
                    if user_id in user_data_store:
                        del user_data_store[user_id]
                    if invoice_id in pending_payments:
                        del pending_payments[invoice_id]
                    
                    return
        except Exception as e:
            logger.error(f"Error checking payment for user {user_id}: {e}")
    
    # Если оплата не получена за 5 минут
    logger.warning(f"Payment timeout for user {user_id}, invoice {invoice_id}")
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="⏰ *Время ожидания оплаты истекло*\n\n"
                 "Если вы оплатили, но предсказание не пришло, свяжитесь с поддержкой.\n\n"
                 "Попробуйте начать заново, нажав кнопку 🔮 Получить предсказание",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error sending timeout message: {e}")
    
    # Очищаем данные
    if user_id in user_data_store:
        del user_data_store[user_id]
    if invoice_id in pending_payments:
        del pending_payments[invoice_id]

async def new_prediction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки нового предсказания"""
    query = update.callback_query
    await query.answer()
    
    # Удаляем сообщение с кнопкой
    await query.message.delete()
    
    # Запускаем процесс предсказания
    return await predict(query, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    user_id = update.effective_user.id
    if user_id in user_data_store:
        # Отменяем ожидание оплаты
        invoice_id = user_data_store[user_id].get('invoice_id')
        if invoice_id and invoice_id in pending_payments:
            del pending_payments[invoice_id]
        del user_data_store[user_id]
    
    await update.message.reply_text(
        "❌ *Операция отменена*\n\n"
        "Если передумаешь, просто нажми кнопку 🔮 Получить предсказание\n"
        "✨ Удачи! ✨",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = (
        "📚 *ПОМОЩЬ ПО БОТУ* 📚\n\n"
        "🔮 *Как получить предсказание:*\n\n"
        "1️⃣ Нажми кнопку 🔮 Получить предсказание\n"
        "2️⃣ Укажи свое имя\n"
        "3️⃣ Выбери пол\n"
        "4️⃣ Расскажи, что тебя волнует\n"
        "5️⃣ Выбери свой знак зодиака\n"
        "6️⃣ Оплати 0.10 USDT\n"
        "7️⃣ Жди автоматического предсказания!\n\n"
        "💰 *Оплата:*\n"
        "• Валюта: USDT (TRC20)\n"
        "• Сумма: 0.10 USDT\n"
        "• Предсказание придет автоматически после оплаты\n\n"
        "⚡ *Команды:*\n"
        "/start — Начать работу\n"
        "/help — Показать эту справку\n"
        "/cancel — Отменить операцию\n\n"
        "✨ *Приятного использования!* ✨"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )