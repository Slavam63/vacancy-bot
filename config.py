import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Используем значения по умолчанию только если переменные существуют
API_ID = os.getenv('TELEGRAM_API_ID', '28773930')
API_HASH = os.getenv('TELEGRAM_API_HASH', 'ba5be3a2acd3e1ce0d7fc301feff1d85')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7804369222:AAEWUaQd6pWzwKRSrmfg4MU17a-XQKlHdHw')

# Преобразуем API_ID в число только если он не пустой
if API_ID is not None and API_ID.isdigit():
    API_ID = int(API_ID)
else:
    raise ValueError("Invalid TELEGRAM_API_ID. Must be a number.")