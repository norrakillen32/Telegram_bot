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
