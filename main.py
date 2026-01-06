import os
import json
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# --- БАЗА ЗНАНИЙ ---
class LocalKnowledgeBase:
    def __init__(self, file_path="knowledge_base.json"):
        self.qa_pairs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.qa_pairs = json.load(f)
        except FileNotFoundError:
            logging.warning(f"Файл {file_path} не найден")

    def find_answer(self, user_question: str) -> str | None:
        user_q = user_question.lower()
        for qa in self.qa_pairs:
            db_q = qa.get("question", "").lower()
            if db_q in user_q or user_q in db_q:
                return qa.get("answer")
        return None

knowledge_base = LocalKnowledgeBase()

# --- ПОИСК В ДОКУМЕНТАЦИИ 1С (заглушка) ---
def search_in_1c_docs(question: str) -> str:
    return f"📘 По документации 1С:\nПо запросу '{question}' я пока ничего не нашел. Реализуйте поиск в документации."

# --- ОТПРАВКА СООБЩЕНИЙ В TELEGRAM ---
def send_telegram_message(chat_id: int, text: str):
    """Отправляет сообщение в Telegram чат."""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка отправки в Telegram: {e}")
        return False

# --- ОБРАБОТКА КОМАНД И СООБЩЕНИЙ ---
def handle_telegram_update(update_data: dict):
    """
    Обрабатывает входящее обновление от Telegram.
    """
    if "message" not in update_data:
        return
    
    message = update_data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    
    if not text:
        return
    
    logging.info(f"Обработка: chat_id={chat_id}, text='{text}'")
    
    # Обработка команды /start
    if text.startswith("/start"):
        welcome_text = (
            "Привет! Я бот-помощник по 1С.\n\n"
            "Задайте вопрос, и я:\n"
            "1. Сначала поищу ответ в своей базе знаний\n"
            "2. Если не найду — обращусь к документации 1С\n\n"
            "Попробуйте: 'Как создать накладную?' или 'Где отчет о прибылях?'"
        )
        send_telegram_message(chat_id, welcome_text)
        return
    
    # ЭТАП 1: Поиск в локальной базе знаний
    answer = knowledge_base.find_answer(text)
    
    # ЭТАП 2: Если не нашли, ищем в документации
    if not answer:
        answer = search_in_1c_docs(text)
    
    # Отправляем ответ
    send_telegram_message(chat_id, answer)

# --- FLASK ЭНДПОИНТЫ ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Точка входа для вебхука от Telegram."""
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({"status": "error", "message": "Нет данных"}), 400
        
        logging.info(f"Получен вебхук: {update_data}")
        
        # Обрабатываем обновление
        handle_telegram_update(update_data)
        
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        logging.error(f"Ошибка в /webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "Telegram 1C Bot"})

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "Telegram 1C Bot"})
