from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    print("Получено обновление:", update)  # Логируем в консоль/файл

    if 'message' in update and 'text' in update['message']:
        # ... логика отправки ответа
    else:
        print("Не текстовое сообщение:", update)  # Логируем неподдерживаемые типы

    return jsonify({'status': 'ok'}), 200

def send_message(chat_id: int, text: str):
    """Отправка сообщения через Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload, timeout=5)
        print("Ответ Telegram:", response.status_code, response.json())  # Логируем результат
    except Exception as e:
        print("Ошибка отправки сообщения:", e)

