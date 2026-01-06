from flask import Flask, request, jsonify
import os
import requests
import logging
from nlp_engine import NLPEngine

nlp = NLPEngine()
app = Flask(__name__)

# Настройка логирования для отладки кодировки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    logger.info("Получено обновление: %s", update)
    
    
@app.route('/ask', methods=['POST'])
def ask():
    """Обрабатывает запросы на поиск ответа."""
    query = request.json.get('query', '').strip()
    if not query:
        return jsonify({"error": "Пустой запрос"}), 400
    
    answer = nlp.find_best_answer(query)
    return jsonify({"answer": answer})

@app.route('/learn', methods=['POST'])
def learn():
    """Добавляет новый пример в базу знаний."""
    question = request.json.get('question', '').strip()
    answer = request.json.get('answer', '').strip()
    
    if not question or not answer:
        return jsonify({"error": "Не указаны question или answer"}), 400
    
    nlp.add_example(question, answer)
    return jsonify({"status": "success", "message": "Пример добавлен!"})

@app.route('/', methods=['GET'])
def health():
    """Проверка работоспособности."""
    return jsonify({"status": "ok", "service": "1C Help Bot"})

