import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from nlp_engine import NLPEngine
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация NLP‑ядра
nlp = NLPEngine()


# ID администратора (замените на свой Telegram ID)
ADMIN_ID = 123456789


# Токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")


application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Как создать накладную?"), KeyboardButton("Где отчёт о прибыли?")],
        [KeyboardButton("Как провести оплату поставщику?")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Здравствуйте! Я бот помощи по 1С.\n"
        "Задайте вопрос или выберите пример ниже.",
        reply_markup=reply_markup
    )

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return

    text = update.message.text.replace("/learn", "", 1).strip()
    if "|" not in text:
        await update.message.reply_text(
            "Формат: /learn вопрос | ответ\n"
            "Пример: /learn Как обновить 1С? | 1. Сделайте копию базы..."
        )
        return

    question, answer = map(str.strip, text.split("|", 1))
    nlp.add_example(question, answer)
    await update.message.reply_text(
        f"✅ Пример добавлен:\n\n**Вопрос:** {question}\n**Ответ:** {answer}",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    answer = nlp.find_best_answer(query)
    await update.message.reply_text(answer, parse_mode="Markdown")

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("learn", learn))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
