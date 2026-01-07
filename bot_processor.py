import os
import json
import re
import difflib
import requests
from typing import Dict, Any, List, Optional, Tuple

# Импортируем NLPEngine из отдельного файла
from nlp_engine import NLPEngine

class TelegramBot:
    """Работа с Telegram API"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан!")
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML", 
                     reply_markup: Dict = None) -> bool:
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
    
    def send_chat_action(self, chat_id: int, action: str = "typing") -> bool:
        try:
            response = requests.post(
                f"{self.api_url}/sendChatAction",
                json={"chat_id": chat_id, "action": action},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

class ResponseFormatter:
    """Форматирование ответов и клавиатур"""
    
    @staticmethod
    def format_welcome_message() -> str:
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
    def create_main_keyboard() -> Dict:
        return {
            "keyboard": [
                [{"text": "📦 Накладные"}, {"text": "📊 Отчеты"}],
                [{"text": "💰 Платежи"}, {"text": "📋 Документы"}],
                [{"text": "📈 Финансы"}, {"text": "👥 Контрагенты"}],
                [{"text": "⚙️ Настройки"}, {"text": "🆘 Помощь"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
            "input_field_placeholder": "Выберите раздел или задайте вопрос..."
        }
    
    @staticmethod
    def create_invoices_keyboard() -> Dict:
        return {
            "keyboard": [
                [{"text": "📦 Новая накладная"}, {"text": "📋 Копировать накладную"}],
                [{"text": "🔄 Создать УПД"}, {"text": "🚚 ТТН для перевозки"}],
                [{"text": "🔍 Поиск накладной"}, {"text": "📊 Статистика накладных"}],
                [{"text": "⬅️ Назад"}, {"text": "🏠 В главное меню"}]
            ],
            "resize_keyboard": True
        }
    
    @staticmethod
    def create_reports_keyboard() -> Dict:
        return {
            "keyboard": [
                [{"text": "📈 Прибыль и убытки"}, {"text": "💰 Денежный поток"}],
                [{"text": "📦 Остатки товаров"}, {"text": "👥 Дебиторская задолженность"}],
                [{"text": "📊 Продажи по периодам"}, {"text": "📋 Товарооборот"}],
                [{"text": "⬅️ Назад"}, {"text": "🏠 В главное меню"}]
            ],
            "resize_keyboard": True
        }
    
    @staticmethod
    def create_payments_keyboard() -> Dict:
        return {
            "keyboard": [
                [{"text": "💳 Оплата поставщику"}, {"text": "💰 Поступление от клиента"}],
                [{"text": "💵 Выдача под отчет"}, {"text": "🏦 Банковские выписки"}],
                [{"text": "🧾 Авансовые отчеты"}, {"text": "📑 Кассовая книга"}],
                [{"text": "⬅️ Назад"}, {"text": "🏠 В главное меню"}]
            ],
            "resize_keyboard": True
        }

class BotProcessor:
    """Основной процессор бота"""
    
    def __init__(self):
        self.telegram = TelegramBot()
        self.formatter = ResponseFormatter()
        self.nlp_engine = NLPEngine()
        self.user_sessions = {}
        self.button_texts = [
            "📦", "📊", "💰", "📋", "📈", "👥", "⚙️", "🆘",
            "Накладные", "Отчеты", "Платежи", "Документы",
            "Финансы", "Контрагенты", "Настройки", "Помощь",
            "⬅️", "🏠", "накладные", "отчеты", "платежи", "документы",
            "⬅️ Назад", "🏠 В главное меню"
        ]
    
    def _get_user_session(self, user_id: int) -> Dict:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'message_count': 0,
                'last_activity': None,
                'current_menu': None,
                'waiting_for_clarification': False,
                'original_query': ''
            }
        return self.user_sessions[user_id]
    
    def _update_user_session(self, user_id: int, message: str = None):
        session = self._get_user_session(user_id)
        session['message_count'] += 1
        session['last_activity'] = 'сейчас'
        return session
    
    def _handle_start(self, chat_id: int, args: str) -> bool:
        session = self._get_user_session(chat_id)
        session['waiting_for_clarification'] = False
        
        keyboard = self.formatter.create_main_keyboard()
        return self.telegram.send_message(
            chat_id,
            self.formatter.format_welcome_message(),
            reply_markup=keyboard
        )
    
    def _handle_help(self, chat_id: int, args: str) -> bool:
        help_text = """🆘 <b>Помощь по использованию бота:</b>

<b>Основные команды:</b>
/start — начать работу с ботом
/help — показать эту справку

<b>Как задавать вопросы:</b>
1. <i>Конкретно</i>: «Как создать накладную в 1С?»
2. <i>С контекстом</i>: «Мне нужно провести оплату поставщику»
3. <i>По шагам</i>: «Какие этапы создания отчета?»

<b>Используйте кнопки меню</b> для быстрого доступа к разделам.

<b>📊 Статистика вашего диалога</b> доступна по команде /stats

<b>🔧 Техническая поддержка:</b> @Howl89"""
        
        return self.telegram.send_message(chat_id, help_text)
    
    def _handle_stats(self, chat_id: int, args: str) -> bool:
        session = self._get_user_session(chat_id)
        
        stats_text = f"""📊 <b>Ваша статистика:</b>

• <b>Всего сообщений:</b> {session['message_count']}
• <b>Последняя активность:</b> {session.get('last_activity', 'неизвестно')}
• <b>Текущее меню:</b> {session.get('current_menu', 'главное')}
• <b>Ожидание уточнения:</b> {'Да' if session.get('waiting_for_clarification') else 'Нет'}

<b>База знаний бота:</b>
• Используется NLP-движок с интеллектуальным поиском
• Поддержка контекстного анализа"""
        
        return self.telegram.send_message(chat_id, stats_text)
    
    def _handle_option_selection(self, chat_id: int, option_number: int) -> bool:
        """Обработка выбора номера варианта из уточнения"""
        response = self.nlp_engine.get_option_selection(chat_id, option_number)
        
        if response:
            session = self._get_user_session(chat_id)
            session['waiting_for_clarification'] = False
            return self.telegram.send_message(chat_id, response, parse_mode="HTML")
        else:
            return self.telegram.send_message(
                chat_id,
                f"❌ <b>Неверный номер варианта:</b> {option_number}\n\n"
                f"Пожалуйста, выберите номер из предложенного списка."
            )
    
    def handle_command(self, chat_id: int, command: str, args: str = "") -> bool:
        """Обработка команд бота"""
        commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/stats': self._handle_stats,
        }
        
        # Убираем возможный username бота из команды
        clean_command = command.split('@')[0]
        handler = commands.get(clean_command)
        
        if handler:
            return handler(chat_id, args)
        
        # Если команда не найдена
        return self.telegram.send_message(
            chat_id,
            f"🤔 <b>Неизвестная команда:</b> {command}\n\nИспользуйте /help для просмотра доступных команд."
        )
    
    def handle_button_click(self, chat_id: int, button_text: str) -> bool:
        """Обработка нажатия кнопок"""
        session = self._update_user_session(chat_id)
        session['waiting_for_clarification'] = False
        
        button_lower = button_text.lower()
        
        if button_lower == "⬅️ назад" or button_lower == "назад":
            session['current_menu'] = 'main'
            keyboard = self.formatter.create_main_keyboard()
            return self.telegram.send_message(
                chat_id,
                "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
                reply_markup=keyboard
            )
        
        elif button_lower == "🏠 в главное меню" or button_lower == "главное меню":
            session['current_menu'] = 'main'
            keyboard = self.formatter.create_main_keyboard()
            return self.telegram.send_message(
                chat_id,
                "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
                reply_markup=keyboard
            )
        
        elif "накладные" in button_lower or button_text == "📦 Накладные":
            session['current_menu'] = 'invoices'
            keyboard = self.formatter.create_invoices_keyboard()
            return self.telegram.send_message(
                chat_id,
                "📦 <b>Раздел «Накладные»</b>\n\nВыберите действие или задайте вопрос:",
                reply_markup=keyboard
            )
        
        elif "отчеты" in button_lower or button_text == "📊 Отчеты":
            session['current_menu'] = 'reports'
            keyboard = self.formatter.create_reports_keyboard()
            return self.telegram.send_message(
                chat_id,
                "📊 <b>Раздел «Отчеты»</b>\n\nВыберите тип отчета:",
                reply_markup=keyboard
            )
        
        elif "платежи" in button_lower or button_text == "💰 Платежи":
            session['current_menu'] = 'payments'
            keyboard = self.formatter.create_payments_keyboard()
            return self.telegram.send_message(
                chat_id,
                "💰 <b>Раздел «Платежи»</b>\n\nВыберите действие:",
                reply_markup=keyboard
            )
        
        elif button_text == "📋 Документы" or button_lower == "документы":
            # Обработка кнопки "Документы" как обычного запроса
            session['current_menu'] = 'documents'
            return self.handle_message(chat_id, "📋 Документы")
        
        elif button_text == "🆘 Помощь" or button_lower == "помощь":
            # Обработка кнопки "Помощь" как команды
            return self._handle_help(chat_id, "")
        
        elif button_text == "📋 Счета" or "счета" in button_lower:
            return self.handle_message(chat_id, "📋 Счета")
        
        elif button_text == "📑 Акта" or "акт" in button_lower:
            return self.handle_message(chat_id, "📑 Акта")
        
        elif button_text == "📝 Договоры" or "договоры" in button_lower:
            return self.handle_message(chat_id, "📝 Договоры")
        
        elif button_text == "🏢 Организации" or "организации" in button_lower:
            return self.handle_message(chat_id, "🏢 Организации")
        
        elif button_text == "⚙️ Настройки" or "настройки" in button_lower:
            return self.handle_message(chat_id, "⚙️ Настройки")
        
        # Для остальных кнопок используем NLPEngine
        return self.handle_message(chat_id, button_text)
    
    def handle_message(self, chat_id: int, user_message: str) -> bool:
        """Обработка текстовых сообщений"""
        self.telegram.send_chat_action(chat_id, "typing")
        session = self._update_user_session(chat_id, user_message)
        
        if session.get('waiting_for_clarification'):
            if user_message.isdigit():
                option_number = int(user_message)
                return self._handle_option_selection(chat_id, option_number)
            else:
                session['waiting_for_clarification'] = False
        
        final_answer = self.nlp_engine.get_final_answer(chat_id, user_message)
        
        # Проверяем, является ли ответ уточняющим вопросом
        if "Выберите номер варианта" in final_answer:
            session['waiting_for_clarification'] = True
            print(f"📝 Установлен waiting_for_clarification для пользователя {chat_id}")
        
        return self.telegram.send_message(chat_id, final_answer, parse_mode="HTML")
    
    def process_update(self, update_data: Dict[str, Any]) -> bool:
        """Обработка обновления от Telegram"""
        try:
            if 'message' not in update_data:
                return False
            
            message = update_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if not text:
                return False
            
            print(f"📨 Сообщение от {chat_id}: {text}")
            
            # Обработка команд
            if text.startswith('/'):
                return self.handle_command(chat_id, text)
            else:
                # Проверяем, является ли текст кнопкой
                text_lower = text.lower()
                is_button = False
                
                for button in self.button_texts:
                    button_lower = button.lower()
                    # Проверяем полное совпадение или частичное для длинных строк
                    if button_lower == text_lower or button_lower in text_lower:
                        is_button = True
                        break
                
                if is_button:
                    return self.handle_button_click(chat_id, text)
                else:
                    return self.handle_message(chat_id, text)
            
        except Exception as e:
            print(f"❌ Ошибка в process_update: {e}")
            import traceback
            traceback.print_exc()
            return False

# Создаем глобальный экземпляр процессора
bot_processor = BotProcessor()
