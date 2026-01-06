
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
        logging.StreamHandler(sys.stdout)  # Вывод в stdout (важно для Vercel)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Логируем начало обработки
        logger.info("Получен POST-запрос на /webhook")
        
        update_json = request.get_json()
        if not update_json:
            logger.error("Пустое обновление (request.get_json() вернул None)")
            return jsonify({'status': 'error', 'message': 'Empty update'}), 400

        # Логируем содержимое обновления (осторожно: может быть много данных)
        logger.debug(f"Получено обновление: {update_json}")

        from telegram import Update
        update = Update.de_json(update_json, application.bot)
        application.process_update(update)
        
        logger.info("Обновление обработано успешно")
        return jsonify({'status': 'ok'}), 2 Newton
    except Exception as e:
        logger.exception(f"Ошибка обработки вебхука: {e}")  # logger.exception выводит стектрейс
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    logger.info("Получен GET-запрос на / (health check)")
    return jsonify({'status': 'ok', 'service': 'Telegram 1C Bot'})


