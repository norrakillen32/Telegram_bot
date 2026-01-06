import json
import os
import requests

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
    def send_message(self, chat_id, text):
        """Отправляет сообщение в Telegram"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return False

class KnowledgeBase:
    def __init__(self, file_path="knowledge_base.json"):
        self.file_path = file_path
        self.data = self._load_data()
    
    def _load_data(self):
        """Загружает базу знаний из JSON"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Файл {self.file_path} не найден")
            return []
        except json.JSONDecodeError:
            print(f"Ошибка чтения {self.file_path}")
            return []
    
    def find_answer(self, question):
        """Ищет ответ в локальной базе знаний"""
        question_lower = question.lower().strip()
        
        # Простой поиск по вхождению
        for item in self.data:
            if question_lower in item.get('question', '').lower():
                return item.get('answer')
        
        # Расширенный поиск (по словам)
        question_words = set(question_lower.split())
        best_match = None
        best_score = 0
        
        for item in self.data:
            item_question = item.get('question', '').lower()
            item_words = set(item_question.split())
            
            # Считаем совпадение слов
            common_words = question_words.intersection(item_words)
            score = len(common_words) / max(len(question_words), 1)
            
            if score > best_score and score > 0.3:  # Порог 30%
                best_score = score
                best_match = item.get('answer')
        
        return best_match

class DocSearch1C:
    """Поиск в документации 1С (заглушка)"""
    
    def search(self, question):
        # TODO: Реализовать реальный поиск
        # Вариант 1: RAG с векторной БД
        # Вариант 2: Запрос к API 1С
        return f"🔍 <b>Поиск в документации 1С:</b>\n\nПо запросу '{question}' я пока ничего не нашел.\n\nНужно настроить поиск в документации 1С."

class BotProcessor:
    """Основной процессор бота"""
    
    def __init__(self):
        self.bot = TelegramBot()
        self.kb = KnowledgeBase()
        self.doc_search = DocSearch1C()
    
    def handle_start(self, chat_id):
        """Обработка команды /start"""
        welcome_text = """👋 <b>Привет! Я бот-помощник по 1С</b>

Задайте вопрос, и я:
1️⃣ Сначала поищу в базе знаний
2️⃣ Если не найду — поищу в документации 1С

<b>Примеры вопросов:</b>
• Как создать накладную?
• Где отчет о прибылях?
• Как провести оплату поставщику?
• Как посмотреть остатки товаров?

Попробуйте задать вопрос!"""
        
        return self.bot.send_message(chat_id, welcome_text)
    
    def handle_message(self, chat_id, user_message):
        """Обработка обычного сообщения"""
        # Этап 1: Поиск в локальной базе
        answer = self.kb.find_answer(user_message)
        
        # Этап 2: Если не нашли, ищем в документации
        if not answer:
            answer = self.doc_search.search(user_message)
        
        # Отправляем ответ
        return self.bot.send_message(chat_id, answer)
    
    def process_update(self, update_data):
        """Обрабатывает входящее обновление от Telegram"""
        try:
            if 'message' not in update_data:
                return False
            
            message = update_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if not text:
                return False
            
            print(f"Обработка сообщения: chat_id={chat_id}, text='{text}'")
            
            # Определяем тип сообщения
            if text.startswith('/start'):
                return self.handle_start(chat_id)
            else:
                return self.handle_message(chat_id, text)
                
        except Exception as e:
            print(f"Ошибка в process_update: {e}")
            return False

# Создаем глобальный экземпляр процессора
processor = BotProcessor()
