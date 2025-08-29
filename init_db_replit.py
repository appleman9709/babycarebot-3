#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт инициализации базы данных для Replit
Создает базу данных с тестовыми данными
"""

import sqlite3
import os
from datetime import datetime, timedelta

def init_database():
    """Инициализация базы данных"""
    print("🗄️ Инициализация базы данных...")
    
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Создание таблиц
    cur.execute("""
        CREATE TABLE IF NOT EXISTS families (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            family_id INTEGER,
            user_id INTEGER,
            role TEXT DEFAULT 'Родитель',
            name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedings (
            id INTEGER PRIMARY KEY,
            family_id INTEGER,
            author_id INTEGER,
            timestamp TEXT NOT NULL,
            author_role TEXT DEFAULT 'Родитель',
            author_name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS diapers (
            id INTEGER PRIMARY KEY,
            family_id INTEGER,
            author_id INTEGER,
            timestamp TEXT NOT NULL,
            author_role TEXT DEFAULT 'Родитель',
            author_name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            family_id INTEGER,
            feed_interval INTEGER DEFAULT 3,
            diaper_interval INTEGER DEFAULT 2,
            tips_enabled INTEGER DEFAULT 1,
            tips_time_hour INTEGER DEFAULT 9,
            tips_time_minute INTEGER DEFAULT 0,
            bath_interval INTEGER DEFAULT 1,
            bath_time_hour INTEGER DEFAULT 19,
            bath_time_minute INTEGER DEFAULT 0,
            bath_enabled INTEGER DEFAULT 1,
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS baby_info (
            family_id INTEGER PRIMARY KEY,
            name TEXT DEFAULT 'Малыш',
            birth_date TEXT,
            gender TEXT DEFAULT 'Не указан',
            weight REAL DEFAULT 0.0,
            height REAL DEFAULT 0.0,
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    # Создаем тестовую семью
    cur.execute("INSERT OR IGNORE INTO families (id, name) VALUES (1, 'Тестовая семья')")
    
    # Создаем тестового члена семьи
    cur.execute("INSERT OR IGNORE INTO family_members (family_id, user_id, role, name) VALUES (1, 123456789, 'Родитель', 'Тест')")
    
    # Создаем настройки по умолчанию
    cur.execute("INSERT OR IGNORE INTO settings (family_id, feed_interval, diaper_interval, tips_enabled, tips_time_hour, tips_time_minute, bath_interval, bath_time_hour, bath_time_minute, bath_enabled) VALUES (1, 3, 2, 1, 9, 0, 1, 19, 0, 1)")
    
    # Создаем тестовую информацию о малыше
    cur.execute("INSERT OR IGNORE INTO baby_info (family_id, name, birth_date, gender, weight, height) VALUES (1, 'Тестовый малыш', '01.01.2024', 'Не указан', 3.5, 50.0)")
    
    # Создаем тестовые записи кормлений
    now = datetime.now()
    for i in range(5):
        time = now - timedelta(hours=i*3)
        cur.execute("INSERT OR IGNORE INTO feedings (family_id, author_id, timestamp, author_role, author_name) VALUES (?, ?, ?, ?, ?)",
                   (1, 123456789, time.isoformat(), 'Родитель', 'Тест'))
    
    # Создаем тестовые записи смен подгузников
    for i in range(3):
        time = now - timedelta(hours=i*4)
        cur.execute("INSERT OR IGNORE INTO diapers (family_id, author_id, timestamp, author_role, author_name) VALUES (?, ?, ?, ?, ?)",
                   (1, 123456789, time.isoformat(), 'Родитель', 'Тест'))
    
    conn.commit()
    conn.close()
    
    print("✅ База данных инициализирована с тестовыми данными")
    print("📊 Создано:")
    print("   • 1 семья")
    print("   • 1 член семьи")
    print("   • Настройки по умолчанию")
    print("   • Информация о малыше")
    print("   • 5 записей кормлений")
    print("   • 3 записи смен подгузников")

if __name__ == "__main__":
    init_database()
