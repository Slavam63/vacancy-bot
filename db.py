import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'vacancies.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Проверяем существование таблицы
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vacancies'")
    table_exists = c.fetchone()
    
    if table_exists:
        # Проверяем наличие столбца processed
        c.execute("PRAGMA table_info(vacancies)")
        columns = [col[1] for col in c.fetchall()]
        if 'processed' not in columns:
            c.execute("ALTER TABLE vacancies ADD COLUMN processed INTEGER DEFAULT 0")
    else:
        # Создаем таблицу с новой структурой
        c.execute('''CREATE TABLE vacancies (
                    id INTEGER PRIMARY KEY,
                    channel TEXT,
                    date TEXT,
                    text TEXT,
                    keywords TEXT,
                    processed INTEGER DEFAULT 0
                    )''')
    
    conn.commit()
    conn.close()

def save_vacancy(channel, date, text, keywords):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO vacancies 
                (channel, date, text, keywords) 
                VALUES (?, ?, ?, ?)''',
                (channel, date, text, ','.join(keywords)))
    conn.commit()
    conn.close()

def get_unprocessed_vacancies():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    c = conn.cursor()
    c.execute("SELECT * FROM vacancies WHERE processed = 0")
    result = c.fetchall()
    conn.close()
    return result

def mark_as_processed(vacancy_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE vacancies SET processed = 1 WHERE id = ?", (vacancy_id,))
    conn.commit()
    conn.close()

# Инициализация БД при импорте
init_db()