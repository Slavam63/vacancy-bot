import asyncio
import sys
import os

# 📍 Устанавливаем правильный путь к src/parser/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from parser import telegram_parser

if __name__ == '__main__':
    asyncio.run(telegram_parser.main())
