from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Получаем данные от Telegram
    update = request.get_json()

    # Если пришло сообщение
    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        user_text = update['message']['text']

        # Отправляем ответ
        send_message(chat_id, f"Вы написали: {user_text}")

    return jsonify({'status': 'ok'}), 200

def send_message(chat_id: int, text: str):
    """Отправка сообщения через Telegram API"""
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

# Для локального тестирования (не для Vercel)
if __name__ == '__main__':
    app.run(port=5000)