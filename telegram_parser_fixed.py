import os
import sys
import logging
import asyncio
from datetime import datetime
from configparser import ConfigParser
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Путь к config.ini (в той же папке, где лежит этот скрипт)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, 'config.ini')

# Чтение конфига
config = ConfigParser()
config.optionxform = str
if not os.path.exists(CONFIG_PATH):
    logger.error(f"❌ config.ini не найден по пути: {CONFIG_PATH}")
    sys.exit(1)
config.read(CONFIG_PATH, encoding='utf-8')

# Загрузка параметров [Telegram]
try:
    api_id = int(config.get('Telegram', 'api_id', fallback='0'))
    api_hash = config.get('Telegram', 'api_hash', fallback='')
    phone_number = config.get('Telegram', 'phone', fallback='')

    if not all([api_id, api_hash, phone_number]):
        raise ValueError("Некоторые параметры в [Telegram] отсутствуют.")
except Exception as e:
    logger.error(f"❌ Ошибка при чтении [Telegram]: {e}")
    sys.exit(1)

# Каналы
target_channels = []
last_loaded = None

def load_channels():
    global target_channels, last_loaded
    try:
        raw = config.get('Parser', 'target_channels', fallback='')
        channels = [c.strip().lstrip('@') for c in raw.split(',') if c.strip()]
        target_channels[:] = channels
        last_loaded = datetime.now()
        logger.info(f"🔄 Каналы обновлены: {channels}")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки каналов: {e}")

async def monitor_channel_updates():
    while True:
        load_channels()
        await asyncio.sleep(60)

async def main():
    client = TelegramClient("parser_session", api_id, api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.info("🔐 Авторизация...")
            await client.send_code_request(phone_number)
            code = input("📩 Введите код из Telegram: ").strip()
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                password = input("🔐 Введите пароль 2FA: ").strip()
                await client.sign_in(password=password)

        me = await client.get_me()
        logger.info(f"👤 Авторизовались как: {me.first_name} (@{me.username or 'без username'})")
        load_channels()

        @client.on(events.NewMessage(pattern='/status'))
        async def status(event):
            await event.respond(
                f"✅ Бот работает\n📡 Каналов: {len(target_channels)}\n🕓 Обновлено: {last_loaded.strftime('%H:%M:%S')}"
            )

        @client.on(events.NewMessage(pattern='/list'))
        async def list_handler(event):
            if target_channels:
                listing = '\n'.join(f"@{ch}" for ch in target_channels)
                await event.respond(f"📋 Список каналов:\n{listing}")
            else:
                await event.respond("🔇 Каналы не заданы.")

        @client.on(events.NewMessage())
        async def handle(event):
            chat_username = getattr(event.chat, 'username', None)
            if not chat_username or chat_username not in target_channels:
                return

            text = event.message.text or ""
            date = event.message.date.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"📥 @{chat_username} → {text}")

            try:
                import db
                keywords = [w.strip("#") for w in text.split() if w.startswith("#")]
                db.save_vacancy(chat_username, date, text, keywords)
            except Exception as e:
                logger.error(f"💾 Ошибка сохранения: {e}")

        await asyncio.gather(
            client.run_until_disconnected(),
            monitor_channel_updates()
        )

    except Exception as e:
        logger.error(f"❗ Ошибка бота: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
