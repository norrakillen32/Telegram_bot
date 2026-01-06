from flask import Flask, request, jsonify
from bot import application
import logging
import sys
from flask_cors import CORS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) 
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.before_request
def log_request_info():
    logger.info('Входящий запрос: %s %s', request.method, request.path)
    
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update_json = request.get_json()
        logger.info(f"Обновление: {update_json}")
        
        if update_json and 'message' in update_json:
            chat_id = update_json['message']['chat']['id']
            user_text = update_json['message'].get('text', '')
            
            # Отправляем ответ напрямую через API
            application.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Получил ваше сообщение: '{user_text}'\nНо обработчики пока не работают."
            )
            logger.info(f"Ответ отправлен в чат {chat_id}")
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.exception(f"Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    logger.info("Получен GET-запрос на / (health check)")
    return jsonify({'status': 'ok', 'service': 'Telegram 1C Bot'})

