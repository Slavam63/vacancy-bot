import os
import logging
import asyncio
import re
from configparser import ConfigParser
from telethon import TelegramClient, events
from aiogram import Bot, Dispatcher, types
from data_processor import process_vacancies

# Логирование (без переопределения stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("parser_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, 'config.ini')

config = ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logger.error(f"[ОШИБКА] config.ini не найден: {CONFIG_PATH}")
    raise SystemExit(1)
config.read(CONFIG_PATH, encoding='utf-8')

# Параметры Telegram
api_id_str = config.get('Telegram', 'api_id', fallback='0')
API_ID = int(''.join(filter(str.isdigit, api_id_str)))
API_HASH = config.get('Telegram', 'api_hash', fallback='')
PHONE_NUMBER = config.get('Telegram', 'phone', fallback='')
BOT_TOKEN = config.get('Telegram', 'bot_token', fallback='')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

def load_channels():
    try:
        raw = config.get('Parser', 'target_channels', fallback='')
        return [c.strip().lstrip('@') for c in raw.split(',') if c.strip()]
    except Exception as e:
        logger.exception("Ошибка загрузки каналов")
        return []

def parse_vacancy(text: str) -> dict:
    title_match = re.search(r"Должность:\s*(.+)", text)
    salary_match = re.search(r"Зарплата:\s*(.+)", text)
    return {
        'title': title_match.group(1) if title_match else "Не указано",
        'salary': salary_match.group(1) if salary_match else "Не указано",
        'location': "Удалённая работа",
        'employer': "Компания",
        'conditions': "Полная занятость",
        'contact': "HR",
        'source': "Telegram"
    }

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("[БОТ] Бот запущен. Используйте /parse для сбора вакансий.")

@dp.message_handler(commands=['parse'])
async def cmd_parse(message: types.Message):
    await message.answer("[ЖДИТЕ] Парсинг запущен...")
    asyncio.create_task(run_telethon_parser())
    await message.answer("[ГОТОВО] Результаты появятся позже.")

async def run_telethon_parser():
    client = TelegramClient("parser_session", API_ID, API_HASH)
    try:
        await client.start(PHONE_NUMBER)
        logger.info("Telethon клиент авторизован")

        target_channels = load_channels()
        if not target_channels:
            logger.warning("Список каналов пуст")
            return

        @client.on(events.NewMessage(chats=target_channels))
        async def handler(event):
            try:
                text = event.message.text or ""
                chat = await event.get_chat()
                logger.info(f"Вакансия от @{chat.username}: {text[:60]}...")

                keywords = [w.strip("#") for w in text.split() if w.startswith("#")]
                date = event.message.date.strftime('%Y-%m-%d %H:%M:%S')

                import db
                db.save_vacancy(chat.username, date, text, keywords)

            except Exception as e:
                logger.exception("Ошибка обработки сообщения")

        logger.info(f"Запуск мониторинга {len(target_channels)} каналов...")
        await client.run_until_disconnected()

    except Exception as e:
        logger.exception("Ошибка Telethon")
    finally:
        await client.disconnect()

async def main():
    try:
        logger.info("Запуск основного цикла...")
        asyncio.create_task(process_vacancies(bot))
        await dp.start_polling()
    except Exception as e:
        logger.exception("Ошибка при запуске бота")

if __name__ == '__main__':
    asyncio.run(main())
