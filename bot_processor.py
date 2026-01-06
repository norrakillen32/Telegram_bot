import os
import requests
from typing import Dict, Any
from nlp_engine import nlp_engine

class TelegramAPI:
    """Работа с Telegram Bot API"""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан!")
        
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str, 
                    parse_mode: str = "HTML",
                    reply_markup: Dict = None) -> bool:
        """Отправка сообщения в Telegram"""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return False
    
    def send_typing_action(self, chat_id: int) -> bool:
        """Отправка индикатора 'печатает'"""
        try:
            response = requests.post(
                f"{self.api_url}/sendChatAction",
                json={
                    "chat_id": chat_id,
                    "action": "typing"
                },
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

class ResponseFormatter:
    """Форматирование ответов"""
    
    @staticmethod
    def format_welcome_message() -> str:
        """Форматирование приветственного сообщения"""
        return """👋 <b>Добро пожаловать в бот-помощник по 1С!</b>

🤖 <i>Я использую искусственный интеллект для поиска ответов:</i>

<b>📚 Мои возможности:</b>
1. <b>База знаний</b> — быстрые ответы на частые вопросы
2. <b>Поиск в документации 1С</b> — ответы по официальной документации
3. <b>Анализ контекста</b> — понимаю ваши намерения

<b>💡 Примеры вопросов:</b>
• Как создать накладную на отгрузку?
• Где найти отчет о продажах за месяц?
• Как провести оплату от клиента?
• Как настроить пользователя в системе?

<b>⚡ Просто задайте ваш вопрос!</b>"""
    
    @staticmethod
    def format_help_message() -> str:
        """Форматирование справки"""
        return """<b>🆘 Справка по использованию бота:</b>

<b>Основные команды:</b>
/start — начать работу с ботом
/help — показать эту справку
/knowledge — показать доступные темы в базе знаний
/feedback — оставить отзыв

<b>Как задавать вопросы:</b>
1. <i>Конкретно</i>: "Как создать накладную в 1С?"
2. <i>С контекстом</i>: "Мне нужно провести оплату поставщику"
3. <i>По шагам</i>: "Какие этапы создания отчета?"

<b>📊 Статистика вашего диалога</b> доступна по команде /stats

<b>🔧 Техническая поддержка:</b> @ваш_логин_поддержки"""
    
    @staticmethod
    def format_knowledge_topics(kb_data: list) -> str:
        """Форматирование списка тем из базы знаний"""
        if not kb_data:
            return "📚 <b>База знаний пуста.</b>\n\nАдминистратор еще не добавил вопросы и ответы."
        
        topics = []
        for i, item in enumerate(kb_data[:15], 1):  # Ограничиваем 15 темами
            question = item.get('question', 'Без названия')
            if len(question) > 50:
                question = question[:47] + "..."
            topics.append(f"{i}. {question}")
        
        return f"""📚 <b>Доступные темы в базе знаний ({len(kb_data)}):</b>

{chr(10).join(topics)}

<i>Задайте вопрос по одной из этих тем для получения подробного ответа.</i>"""
    
    @staticmethod
    def create_keyboard_markup(buttons: list) -> Dict:
        """Создание клавиатуры для Telegram"""
        keyboard = []
        
        for i in range(0, len(buttons), 2):
            row = buttons[i:i+2]
            keyboard.append([{"text": btn} for btn in row])
        
        return {
            "keyboard": keyboard,
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

class BotProcessor:
    """Основной процессор бота"""
    
    def __init__(self):
        self.telegram = TelegramAPI()
        self.formatter = ResponseFormatter()
        self.user_sessions = {}  # Простое хранение сессий
    
    def _get_user_session(self, user_id: int) -> Dict:
        """Получение или создание сессии пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'message_count': 0,
                'first_seen': None,
                'last_activity': None,
                'questions_history': []
            }
        return self.user_sessions[user_id]
    
    def _update_user_session(self, user_id: int, question: str):
        """Обновление сессии пользователя"""
        session = self._get_user_session(user_id)
        session['message_count'] += 1
        session['last_activity'] = 'now'
        
        # Сохраняем историю вопросов (последние 10)
        session['questions_history'].append(question)
        if len(session['questions_history']) > 10:
            session['questions_history'].pop(0)
    
    def handle_command(self, chat_id: int, command: str, args: str = "") -> bool:
        """Обработка команд"""
        commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/knowledge': self._handle_knowledge,
            '/stats': self._handle_stats,
            '/feedback': self._handle_feedback
        }
        handler = commands.get(command.split('@')[0])  # Убираем username бота если есть
        if handler:
            return handler(chat_id, args)
        
        return self._handle_unknown_command(chat_id, command)
    
    def _handle_start(self, chat_id: int, args: str) -> bool:
        """Обработка команды /start"""
        # Приветственная клавиатура
        keyboard = self.formatter.create_keyboard_markup([
            "📦 Накладные",
            "📊 Отчеты",
            "💰 Платежи",
            "🆘 Помощь"
        ])
        
        return self.telegram.send_message(
            chat_id,
            self.formatter.format_welcome_message(),
            reply_markup=keyboard
        )
    
    def _handle_help(self, chat_id: int, args: str) -> bool:
        """Обработка команды /help"""
        return self.telegram.send_message(
            chat_id,
            self.formatter.format_help_message()
        )
    
    def _handle_knowledge(self, chat_id: int, args: str) -> bool:
        """Обработка команды /knowledge"""
        # Загружаем базу знаний для показа тем
        try:
            import json
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
        except:
            kb_data = []
        
        return self.telegram.send_message(
            chat_id,
            self.formatter.format_knowledge_topics(kb_data)
        )
    
    def _handle_stats(self, chat_id: int, args: str) -> bool:
        """Обработка команды /stats"""
        session = self._get_user_session(chat_id)
        
        stats_text = f"""📊 <b>Ваша статистика:</b>

• <b>Всего сообщений:</b> {session['message_count']}
• <b>История вопросов:</b> {len(session['questions_history'])}
• <b>Последняя активность:</b> {session.get('last_activity', 'неизвестно')}

<b>Последние вопросы:</b>
"""
        
        for i, question in enumerate(session['questions_history'][-5:], 1):
            if len(question) > 30:
                question = question[:27] + "..."
            stats_text += f"{i}. {question}\n"
        
        return self.telegram.send_message(chat_id, stats_text)
    
    def _handle_feedback(self, chat_id: int, args: str) -> bool:
        """Обработка команды /feedback"""
        feedback_text = """📝 <b>Оставить отзыв:</b>

Пожалуйста, напишите ваш отзыв или предложение по улучшению бота.

Ваше мнение поможет сделать бота лучше! 💪

<i>Просто напишите ваше сообщение, и оно будет отправлено разработчикам.</i>"""
        
        return self.telegram.send_message(chat_id, feedback_text)
    
    def _handle_unknown_command(self, chat_id: int, command: str) -> bool:
        """Обработка неизвестной команды"""
        return self.telegram.send_message(
            chat_id,
            f"🤔 <b>Неизвестная команда:</b> {command}\n\n"
            f"Используйте /help для просмотра доступных команд."
        )
    
    def handle_message(self, chat_id: int, user_message: str) -> bool:
        """Обработка обычного сообщения"""
        # Обновляем сессию пользователя
        self._update_user_session(chat_id, user_message)
        
        # Показываем индикатор "печатает"
        self.telegram.send_typing_action(chat_id)
        
        # Обрабатываем сообщение через NLP-движок
        final_answer = nlp_engine.get_final_answer(user_message)
        
        # Отправляем ответ
        return self.telegram.send_message(chat_id, final_answer)
    
    def process_update(self, update_data: Dict[str, Any]) -> bool:
        """Обработка входящего обновления от Telegram"""
        try:
            # Извлекаем данные из обновления
            if 'message' not in update_data:
                return False
            
            message = update_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if not text:
                return False
            
            print(f"Обработка: chat_id={chat_id}, text='{text}'")
            
            # Определяем, команда это или обычное сообщение
            if text.startswith('/'):
                return self.handle_command(chat_id, text)
            else:
                return self.handle_message(chat_id, text)
            
        except Exception as e:
            print(f"Ошибка в process_update: {e}")
            return False

# Создаем глобальный экземпляр процессора
bot_processor = BotProcessor()      
