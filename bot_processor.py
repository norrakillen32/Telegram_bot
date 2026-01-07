        
        # Для остальных кнопок используем NLPEngine
        return self.handle_message(chat_id, button_text)
    
    def handle_message(self, chat_id: int, user_message: str) -> bool:
        self.telegram.send_chat_action(chat_id, "typing")
        session = self._update_user_session(chat_id, user_message)
        
        if session.get('waiting_for_clarification'):
            if user_message.isdigit():
                option_number = int(user_message)
                return self._handle_option_selection(chat_id, option_number)
            else:
                session['waiting_for_clarification'] = False
        
        final_answer = self.nlp_engine.get_final_answer(user_message)
        return self.telegram.send_message(chat_id, final_answer, parse_mode="HTML")
    
    def process_update(self, update_data: Dict[str, Any]) -> bool:
        try:
            if 'message' not in update_data:
                return False
            
            message = update_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if not text:
                return False
            
            print(f"📨 Сообщение от {chat_id}: {text}")
            
            if text.startswith('/'):
                return self.handle_command(chat_id, text)
            else:
                button_texts = [
                    "📦", "📊", "💰", "📋", "📈", "👥", "⚙️", "🆘",
                    "Накладные", "Отчеты", "Платежи", "Документы",
                    "Финансы", "Контрагенты", "Настройки", "Помощь",
                    "⬅️", "🏠", "накладные", "отчеты", "платежи", "документы"
                ]
                
                if any(btn in text.lower() for btn in [b.lower() for b in button_texts]):
                    return self.handle_button_click(chat_id, text)
                else:
                    return self.handle_message(chat_id, text)
            
        except Exception as e:
            print(f"❌ Ошибка в process_update: {e}")
            return False

# Создаем глобальный экземпляр процессора
bot_processor = BotProcessor()
