import os
import logging
import json
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# --- НАСТРОЙКА ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# 1. СОЗДАЕМ ПРИЛОЖЕНИЕ python-telegram-bot
application = Application.builder().token(TELEGRAM_TOKEN).build()

# --- ЭТАП 1: ЛОКАЛЬНАЯ БАЗА ЗНАНИЙ ---
class LocalKnowledgeBase:
    def __init__(self, file_path="knowledge_base.json"):
        self.qa_pairs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.qa_pairs = json.load(f)
        except FileNotFoundError:
            pass

    def find_answer(self, user_question: str) -> str | None:
        user_q = user_question.lower()
        for qa in self.qa_pairs:
            db_q = qa.get("question", "").lower()
            if db_q in user_q or user_q in db_q:
                return qa.get("answer")
        return None

knowledge_base = LocalKnowledgeBase()

# --- ЭТАП 2: ЗАГЛУШКА ПОИСКА В ДОКУМЕНТАЦИИ ---
def search_in_1c_docs(question: str) -> str:
    """Здесь потом будет поиск в документации 1С"""
    return f"📘 По документации 1С:\nПо запросу '{question}' я пока ничего не нашел. Нужно настроить поиск."

# --- ОБРАБОТЧИКИ ДЛЯ ТЕЛЕГРАМ-БОТА ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-помощник по 1С. Задайте вопрос — я поищу ответ в базе знаний, а затем в документации.\n\n"
        "Попробуйте спросить: 'Как создать накладную?'"
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logging.info(f"Обрабатываем сообщение: {user_text}")

    # ЭТАП 1: Поиск в локальной базе
    answer = knowledge_base.find_answer(user_text)
    
    if not answer:
        # ЭТАП 2: Если в базе нет, ищем в документации
        answer = search_in_1c_docs(user_text)
    
    await update.message.reply_text(answer)

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

# Важно: инициализируем приложение
application.initialize()

# --- FLASK ЭНДПОИНТЫ ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Точка входа для вебхука от Telegram"""
    try:
        # 1. Получаем данные от Telegram
        update_data = request.get_json()
        if not update_data:
            return jsonify({"status": "error", "message": "Нет данных"}), 400

        logging.info(f"Получен вебхук: {update_data}")

        # 2. Создаем объект Update
        update = Update.de_json(update_data, bot)

        # 3. ГЛАВНОЕ: синхронно обрабатываем обновление
        # Используем run_until_complete для синхронного вызова асинхронного кода
        application.run_until_complete(application.process_update(update))

        # 4. Отвечаем Telegram, что всё ок
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.error(f"Ошибка в /webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "Telegram 1C Bot"})
