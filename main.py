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
    return jsonify({"status": "ok"})
    
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Telegram 1C Bot"})

