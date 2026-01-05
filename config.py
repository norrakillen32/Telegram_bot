import os
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8572890476:AAHVRIrKb_8JuZI_gvjWputPWKNE78AxNvU")

# Настройки NLP
NLP_MODEL = "ru_core_news_sm"
CONFIDENCE_THRESHOLD = 0.3

# Настройки логирования
LOG_LEVEL = "INFO"
LOG_FILE = "bot_nlp.log"

# Настройки статистики
STATS_FILE = "bot_stats.json"
SAVE_STATS_INTERVAL = 100  # сообщений