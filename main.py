from flask import Flask, request, jsonify
import os
from nlp_engine import NLPEngine
from dotenv import load_dotenv
load_dotenv()
# Загрузка переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

# Инициализация NLP
nlp_engine = NLPEngine(r"data\intents.json")

app = Flask(__name__)


@app.route('/webhook-endpoint', methods=['POST'])
def webhook():
    # Проверка секретного токена
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != SECRET_TOKEN:
        return jsonify({"error": "Invalid secret token"}), 403

    # Обработка обновления
    update = request.get_json()

    # Если пришло сообщение
    if 'message' in update and 'text' in update['message']:
        user_text = update['message']['text']
        chat_id = update['message']['chat']['id']

        # Распознаём намерение
        response = nlp_engine.classify_intent(user_text)

        # Отправляем ответ в Telegram
        send_message(chat_id, response)

    return jsonify({"status": "ok"}), 200


def send_message(chat_id: int, text: str):
    """Отправка сообщения через Telegram Bot API"""
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)


if __name__ == '__main__':
    # Настройка webhook при запуске
    import requests

    webhook_url = f"{WEBHOOK_URL}?secret_token={SECRET_TOKEN}"
    payload = {
        "url": webhook_url,
        "secret_token": SECRET_TOKEN,
        "allowed_updates": ["message"]
    }
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json=payload
    )
    print("setWebhook response:", response.json())