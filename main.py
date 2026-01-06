from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    print("Получено обновление:", update)  # Логируем в консоль/файл

    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        user_text = update['message']['text']
        send_message(chat_id, f"Вы написали: {user_text}")
    else:
        print("Не текстовое сообщение:", update)  # Логируем неподдерживаемые типы

    return jsonify({'status': 'ok'}), 200

def send_message(chat_id: int, text: str):
    try:
        # Исправленный URL
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("Сообщение отправлено успешно!", response.json())
        else:
            print(f"Ошибка API: {response.status_code}", response.text)
    except Exception as e:
        print("Ошибка отправки:", e)

