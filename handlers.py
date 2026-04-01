from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
from database import *
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

def get_main_keyboard():
    """Главная клавиатура — только кнопка предсказания"""
    keyboard = [[KeyboardButton("🔮 Получить предсказание")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def register_handlers(application):
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
    application.add_handler(CallbackQueryHandler(back_to_menu_callback, pattern='^back_to_menu$'))
    application.add_handler(MessageHandler(filters.Regex('^🔮 Получить предсказание$'), predict))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username, user.first_name, user.last_name)
    logger.info(f"User {user.id} started")

    welcome_text = (
        f"✨ *Добро пожаловать, {user.first_name}!* ✨\n\n"
        f"🌟 Я — *Бот-предсказатель* 🌟\n"
        f"🔮 Ваш личный проводник в мир тайн и вдохновения.\n\n"
        f"💎 *Что вы получите всего за 0.10 USDT?*\n"
        f"• 🎯 *Персональное предсказание* – ответ на ваш вопрос\n"
        f"• 🌙 *Юмористический гороскоп* – шутливый взгляд на день\n"
        f"• 💫 *Заряд позитива* – энергия на весь день\n\n"
        f"👇 *Нажмите кнопку, чтобы начать* 👇"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {}
    await update.message.reply_text(
        "✨ *Создаём ваше персональное предсказание* ✨\n\n"
        "📝 *Как вас зовут?* (можно указать имя или псевдоним)",
        parse_mode='Markdown'
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.message.text.strip()
    user_data_store[user_id]['name'] = user_name

    await update.message.reply_text(
        f"🌟 *Приятно познакомиться, {user_name}!* 🌟\n\n"
        f"👤 *Укажите ваш пол* – это поможет сделать предсказание точнее.",
        parse_mode='Markdown',
        reply_markup=get_gender_keyboard()
    )
    return ASK_GENDER

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    gender_text = update.message.text

    if "Мужской" in gender_text:
        gender = "male"
        gender_emoji = "👨‍🦰"
    elif "Женский" in gender_text:
        gender = "female"
        gender_emoji = "👩‍🦰"
    else:
        gender = "other"
        gender_emoji = "⚧️"

    user_data_store[user_id]['gender'] = gender
    user_data_store[user_id]['gender_emoji'] = gender_emoji

    await update.message.reply_text(
        f"{gender_emoji} *Принято!*\n\n"
        f"💭 *Расскажите, что вас волнует?* Выберите вариант или напишите свой вопрос.",
        parse_mode='Markdown',
        reply_markup=get_question_keyboard()
    )
    return ASK_QUESTION

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "🔮 *Выберите свой знак зодиака* 🔮\n\n"
        "Это нужно для вашего персонального гороскопа.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_ZODIAC

async def ask_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            f"Это займёт 1–2 минуты.",
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
            "❌ *Ошибка создания счёта*\n\nПожалуйста, попробуйте позже.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def check_payment_background(user_id, invoice_id, context):
    """Фоновая проверка оплаты"""
    max_attempts = 120  # 10 минут
    
    for attempt in range(max_attempts):
        await asyncio.sleep(5)
        
        if user_id not in user_data_store:
            logger.info(f"User {user_id} cancelled, stopping payment check")
            return
        
        user_data = user_data_store.get(user_id)
        if not user_data or user_data.get('invoice_id') != invoice_id:
            logger.info(f"Invoice {invoice_id} no longer pending for user {user_id}")
            return
        
        try:
            is_paid = crypto_pay.check_payment(invoice_id)
            
            if is_paid:
                logger.info(f"Payment confirmed for user {user_id}, invoice {invoice_id}")
                
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

                try:
                    save_prediction(user_id, 'prediction', prediction, user_data['zodiac'], 0.10)
                    save_prediction(user_id, 'horoscope', horoscope, user_data['zodiac'], 0.10)
                    logger.info(f"Predictions saved for user {user_id}")
                except Exception as e:
                    logger.error(f"Error saving predictions: {e}")

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

                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=result_text,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    logger.info(f"Prediction sent to user {user_id}")
                except Exception as e:
                    logger.error(f"Error sending prediction: {e}")
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=result_text,
                        parse_mode='Markdown'
                    )

                if user_id in user_data_store:
                    del user_data_store[user_id]
                if invoice_id in pending_payments:
                    del pending_payments[invoice_id]
                
                return
                
        except Exception as e:
            logger.error(f"Error checking payment for user {user_id}: {e}")
            logger.error(traceback.format_exc())
            continue
    
    logger.warning(f"Payment timeout for user {user_id}, invoice {invoice_id}")
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="⏰ *Время ожидания оплаты истекло (10 минут)*\n\nПопробуйте заново, нажав /predict.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error sending timeout message: {e}")
    
    if user_id in user_data_store:
        del user_data_store[user_id]
    if invoice_id in pending_payments:
        del pending_payments[invoice_id]

async def back_to_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка возврата в главное меню (сообщение с предсказанием не удаляется)"""
    query = update.callback_query
    await query.answer()
    
    # НЕ удаляем сообщение с предсказанием
    # Просто отправляем новое сообщение с главным меню
    
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="🔙 *Главное меню*\n\nНажмите кнопку, чтобы получить новое предсказание.",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data_store:
        invoice_id = user_data_store[user_id].get('invoice_id')
        if invoice_id and invoice_id in pending_payments:
            del pending_payments[invoice_id]
        del user_data_store[user_id]

    await update.message.reply_text(
        "❌ *Операция отменена*\n\nВы можете начать заново через главное меню.",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *ПОМОЩЬ ПО БОТУ* 📚\n\n"
        "🔮 *Как получить предсказание:*\n\n"
        "1️⃣ Нажмите кнопку «🔮 Получить предсказание»\n"
        "2️⃣ Укажите имя и пол\n"
        "3️⃣ Расскажите, что вас волнует (или выберите вариант)\n"
        "4️⃣ Выберите знак зодиака\n"
        "5️⃣ Оплатите 0.10 USDT через CryptoPay\n"
        "6️⃣ Ждите автоматической доставки предсказания!\n\n"
        "💰 *Оплата:*\n"
        "• Валюта: USDT (сеть TRC20)\n"
        "• Сумма: 0.10 USDT\n"
        "• Предсказание придёт автоматически после подтверждения\n\n"
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