from flask import Flask, request, jsonify
import os
import requests
import logging

app = Flask(__name__)

# Настройка логирования для отладки кодировки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    logger.info("Получено обновление: %s", update)

    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        user_text = update['message']['text']
        
        # Явная проверка кодировки текста (отладка)
        try:
            user_text.encode('utf-8')
            logger.info("Текст в UTF-8: %s", user_text)
        except UnicodeEncodeError as e:
            logger.error("Ошибка кодировки: %s", e)
            return jsonify({'status': 'error', 'message': 'Invalid encoding'}), 400

        # Отправляем ответ
        send_message(chat_id, f"Вы написали: {user_text}")
    else:
        logger.info("Не текстовое сообщение: %s", update)

    return jsonify({'status': 'ok'}), 200

def send_message(chat_id: int, text: str):
    """Отправка сообщения через Telegram API с явным указанием UTF-8"""
    try:
        # Формируем URL (убедимся, что токен не содержит не-ASCII символов)
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не задан!")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Явно кодируем текст в UTF-8 перед отправкой
        payload = {
            "chat_id": chat_id,
            "text": text.encode('utf-8').decode('utf-8')  # Гарантируем UTF-8
        }
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info("Сообщение отправлено успешно: %s", response.json())
        else:
            logger.error(
                "Ошибка API: %d %s", 
                response.status_code,
                response.text
            )
            
    except Exception as e:
        logger.exception("Ошибка отправки сообщения: %s", e)

