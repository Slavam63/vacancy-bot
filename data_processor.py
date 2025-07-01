import asyncio
from db import get_unprocessed_vacancies, mark_as_processed
from generate_card import generate_vacancy_card
from excel_generator import generate_excel_from_vacancies
from aiogram import Bot
import configparser
import os
import re
import sys
import io

# Принудительная установка кодировки UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def parse_vacancy(text: str) -> dict:
    """Простой парсер вакансий - нужно адаптировать под ваш формат"""
    title_match = re.search(r"Должность:\s*(.+)", text)
    salary_match = re.search(r"Зарплата:\s*(.+)", text)
    location_match = re.search(r"Локация:\s*(.+)", text)
    
    return {
        'title': title_match.group(1) if title_match else "Не указано",
        'salary': salary_match.group(1) if salary_match else "Не указано",
        'location': location_match.group(1) if location_match else "Удалённо",
        'employer': "Работодатель",
        'conditions': "Полная занятость",
        'contact': "HR",
        'source': "Telegram"
    }

async def process_vacancies(bot: Bot):
    config = configparser.ConfigParser()
    config.read('config.ini')
    admin_id = config.get('Telegram', 'admin_id', fallback=None)
    
    if not admin_id:
        print("[ВНИМАНИЕ] Admin ID не указан в config.ini!")
        return
    
    while True:
        try:
            unprocessed = get_unprocessed_vacancies()
            if not unprocessed:
                print("[ЖДИТЕ] Нет новых вакансий для обработки")
                await asyncio.sleep(300)
                continue
            
            vacancies_data = []
            for vacancy in unprocessed:
                vacancy_info = parse_vacancy(vacancy['text'])
                vacancy_info['source'] = f"https://t.me/{vacancy['channel']}"
                
                # Создаем папку для карточек, если её нет
                os.makedirs('cards', exist_ok=True)
                card_path = f"cards/vacancy_{vacancy['id']}.png"
                generate_vacancy_card(vacancy_info, card_path)
                
                vacancies_data.append(vacancy_info)
                mark_as_processed(vacancy['id'])
            
            # Генерация Excel
            excel_path = "vacancies_report.xlsx"
            logo_path = "logo.png" if os.path.exists("logo.png") else None
            generate_excel_from_vacancies(vacancies_data, logo_path, excel_path)
            
            # Отправка отчета
            with open(excel_path, 'rb') as file:
                await bot.send_document(
                    chat_id=admin_id,
                    document=file,
                    caption=f"Отчет по вакансиям ({len(vacancies_data)} шт.)"
                )
            
            print(f"[УСПЕХ] Отправлен отчет с {len(vacancies_data)} вакансиями")
            await asyncio.sleep(300)
            
        except Exception as e:
            print(f"[ОШИБКА] Ошибка обработки вакансий: {e}")
            await asyncio.sleep(60)