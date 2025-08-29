#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BabyCareBot - Telegram бот для помощи родителям (Replit версия)
"""

import os
import sqlite3
from telethon import TelegramClient, events, Button
from telethon.tl.types import User
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
import asyncio
import json

# Загружаем переменные окружения
from dotenv import load_dotenv

# Пробуем загрузить из разных источников
load_dotenv('config.env')  # Локальный файл
load_dotenv()  # Переменные окружения системы

# Настройки бота
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Проверяем наличие переменных окружения
if not API_ID or not API_HASH or not BOT_TOKEN:
    print("❌ Ошибка: Не найдены переменные окружения!")
    print("Убедитесь, что в Replit добавлены следующие Secrets:")
    print("- API_ID")
    print("- API_HASH") 
    print("- BOT_TOKEN")
    print("\nКак добавить Secrets в Replit:")
    print("1. Перейдите в раздел 'Secrets' (слева)")
    print("2. Добавьте переменные с вашими значениями")
    print("3. Перезапустите проект")
    exit(1)

print(f"✅ API_ID: {API_ID}")
print(f"✅ API_HASH: {API_HASH[:10]}...")
print(f"✅ BOT_TOKEN: {BOT_TOKEN[:10]}...")

# Путь к базе данных на Replit
DB_PATH = os.path.join(os.getcwd(), 'babybot.db')

# Инициализация клиента
client = TelegramClient('babybot_session', API_ID, API_HASH)

# Планировщик задач
scheduler = AsyncIOScheduler()

# Словари для отслеживания состояния
manual_feeding_pending = {}
baby_edit_pending = {}

# Тайский часовой пояс
thai_tz = pytz.timezone('Asia/Bangkok')

def get_thai_time():
    """Получить текущее время в тайском часовом поясе"""
    return datetime.now(thai_tz)

def get_thai_date():
    """Получить текущую дату в тайском часовом поясе"""
    return get_thai_time().date()

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
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
    
    # Добавляем новые колонки в settings, если их нет
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_interval INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Колонка уже существует
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_time_hour INTEGER DEFAULT 19")
    except sqlite3.OperationalError:
        pass
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_time_minute INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_enabled INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def get_family_id(user_id):
    """Получить ID семьи пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT family_id FROM family_members WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def create_family(name):
    """Создать новую семью"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO families (name) VALUES (?)", (name,))
    family_id = cur.lastrowid
    
    # Создаем запись в baby_info
    cur.execute("""
        INSERT INTO baby_info (family_id, name, birth_date, gender, weight, height)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (family_id, 'Малыш', None, 'Не указан', 0.0, 0.0))
    
    conn.commit()
    conn.close()
    return family_id

def add_family_member(family_id, user_id, role, name):
    """Добавить члена семьи"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO family_members (family_id, user_id, role, name)
        VALUES (?, ?, ?, ?)
    """, (family_id, user_id, role, name))
    conn.commit()
    conn.close()

def record_feeding(family_id, user_id, author_role, author_name):
    """Записать кормление"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO feedings (family_id, author_id, timestamp, author_role, author_name)
        VALUES (?, ?, ?, ?, ?)
    """, (family_id, user_id, get_thai_time().isoformat(), author_role, author_name))
    conn.commit()
    conn.close()

def record_diaper(family_id, user_id, author_role, author_name):
    """Записать смену подгузника"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO diapers (family_id, author_id, timestamp, author_role, author_name)
        VALUES (?, ?, ?, ?, ?)
    """, (family_id, user_id, get_thai_time().isoformat(), author_role, author_name))
    conn.commit()
    conn.close()

def get_settings(family_id):
    """Получить настройки семьи"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT feed_interval, diaper_interval, tips_enabled, tips_time_hour, tips_time_minute,
               bath_interval, bath_time_hour, bath_time_minute, bath_enabled
        FROM settings WHERE family_id = ?
    """, (family_id,))
    result = cur.fetchone()
    conn.close()
    
    if result:
        return {
            'feed_interval': result[0],
            'diaper_interval': result[1],
            'tips_enabled': result[2],
            'tips_time_hour': result[3],
            'tips_time_minute': result[4],
            'bath_interval': result[5],
            'bath_time_hour': result[6],
            'bath_time_minute': result[7],
            'bath_enabled': result[8]
        }
    return None

def set_feed_interval(family_id, interval):
    """Установить интервал кормления"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (family_id, feed_interval)
        VALUES (?, ?)
    """, (family_id, interval))
    conn.commit()
    conn.close()

def set_diaper_interval(family_id, interval):
    """Установить интервал смены подгузника"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (family_id, diaper_interval)
        VALUES (?, ?)
    """, (family_id, interval))
    conn.commit()
    conn.close()

def toggle_tips(family_id):
    """Переключить советы"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (family_id, tips_enabled)
        VALUES (?, ?)
    """, (family_id, 1))
    conn.commit()
    conn.close()

def set_tips_time(family_id, hour, minute):
    """Установить время советов"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (family_id, tips_time_hour, tips_time_minute)
        VALUES (?, ?, ?)
    """, (family_id, hour, minute))
    conn.commit()
    conn.close()

def get_bath_settings(family_id):
    """Получить настройки купания"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT bath_interval, bath_time_hour, bath_time_minute, bath_enabled
        FROM settings WHERE family_id = ?
    """, (family_id,))
    result = cur.fetchone()
    conn.close()
    
    if result:
        return {
            'interval': result[0],
            'hour': result[1],
            'minute': result[2],
            'enabled': result[3]
        }
    return {'interval': 1, 'hour': 19, 'minute': 0, 'enabled': 1}

def set_bath_interval(family_id, interval):
    """Установить интервал купания"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (family_id, bath_interval)
        VALUES (?, ?)
    """, (family_id, interval))
    conn.commit()
    conn.close()

def set_bath_time(family_id, hour, minute):
    """Установить время купания"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (family_id, bath_time_hour, bath_time_minute)
        VALUES (?, ?, ?)
    """, (family_id, hour, minute))
    conn.commit()
    conn.close()

def toggle_bath_reminders(family_id):
    """Переключить напоминания о купании"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (family_id, bath_enabled)
        VALUES (?, ?)
    """, (family_id, 1))
    conn.commit()
    conn.close()

def get_baby_info(family_id):
    """Получить информацию о малыше"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT name, birth_date, gender, weight, height 
        FROM baby_info WHERE family_id = ?
    """, (family_id,))
    result = cur.fetchone()
    conn.close()
    
    if result:
        return {
            'name': result[0],
            'birth_date': result[1],
            'gender': result[2],
            'weight': result[3],
            'height': result[4]
        }
    return {
        'name': 'Малыш',
        'birth_date': None,
        'gender': 'Не указан',
        'weight': 0.0,
        'height': 0.0
    }

def update_baby_info(family_id, name=None, birth_date=None, gender=None, weight=None, height=None):
    """Обновить информацию о малыше"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Получаем текущие данные
    cur.execute("SELECT name, birth_date, gender, weight, height FROM baby_info WHERE family_id = ?", (family_id,))
    current = cur.fetchone()
    
    if current:
        # Обновляем только указанные поля
        new_name = name if name is not None else current[0]
        new_birth_date = birth_date if birth_date is not None else current[1]
        new_gender = gender if gender is not None else current[2]
        new_weight = weight if weight is not None else current[3]
        new_height = height if height is not None else current[4]
        
        cur.execute("""
            UPDATE baby_info 
            SET name = ?, birth_date = ?, gender = ?, weight = ?, height = ?
            WHERE family_id = ?
        """, (new_name, new_birth_date, new_gender, new_weight, new_height, family_id))
    else:
        # Создаем новую запись
        cur.execute("""
            INSERT INTO baby_info (family_id, name, birth_date, gender, weight, height)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (family_id, name or 'Малыш', birth_date, gender or 'Не указан', weight or 0.0, height or 0.0))
    
    conn.commit()
    conn.close()

def get_last_feeding(family_id):
    """Получить последнее кормление"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp FROM feedings 
        WHERE family_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (family_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_last_diaper(family_id):
    """Получить последнюю смену подгузника"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp FROM diapers 
        WHERE family_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (family_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_family_members(family_id):
    """Получить членов семьи"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, role, name FROM family_members WHERE family_id = ?", (family_id,))
    members = cur.fetchall()
    conn.close()
    return [{'user_id': m[0], 'role': m[1], 'name': m[2]} for m in members]

async def send_reminder(family_id, message):
    """Отправить напоминание всем членам семьи"""
    members = get_family_members(family_id)
    for member in members:
        try:
            await client.send_message(member['user_id'], message)
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {member['user_id']}: {e}")

async def check_feeding_reminder():
    """Проверить напоминания о кормлении"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT family_id FROM families")
    families = cur.fetchall()
    conn.close()
    
    for (family_id,) in families:
        settings = get_settings(family_id)
        if not settings:
            continue
            
        last_feeding = get_last_feeding(family_id)
        if not last_feeding:
            continue
            
        try:
            last_time = datetime.fromisoformat(last_feeding)
            now = get_thai_time()
            hours_passed = (now - last_time).total_seconds() / 3600
            
            if hours_passed >= settings['feed_interval']:
                await send_reminder(family_id, f"🍼 Время кормить малыша! Прошло {int(hours_passed)} часов с последнего кормления.")
        except Exception as e:
            print(f"Ошибка проверки напоминания о кормлении для семьи {family_id}: {e}")

async def check_diaper_reminder():
    """Проверить напоминания о смене подгузника"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT family_id FROM families")
    families = cur.fetchall()
    conn.close()
    
    for (family_id,) in families:
        settings = get_settings(family_id)
        if not settings:
            continue
            
        last_diaper = get_last_diaper(family_id)
        if not last_diaper:
            continue
            
        try:
            last_time = datetime.fromisoformat(last_diaper)
            now = get_thai_time()
            hours_passed = (now - last_time).total_seconds() / 3600
            
            if hours_passed >= settings['diaper_interval']:
                await send_reminder(family_id, f"👶 Время сменить подгузник! Прошло {int(hours_passed)} часов с последней смены.")
        except Exception as e:
            print(f"Ошибка проверки напоминания о подгузнике для семьи {family_id}: {e}")

async def send_tips():
    """Отправить советы"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT family_id FROM families")
    families = cur.fetchall()
    conn.close()
    
    tips = [
        "💡 Совет: Регулярное кормление помогает установить режим дня малыша",
        "💡 Совет: Не забывайте про массаж - он полезен для развития ребенка",
        "💡 Совет: Следите за температурой в комнате малыша (20-22°C)",
        "💡 Совет: Регулярные прогулки укрепляют иммунитет ребенка",
        "💡 Совет: Читайте малышу книги - это развивает речь и воображение"
    ]
    
    for (family_id,) in families:
        settings = get_settings(family_id)
        if settings and settings['tips_enabled']:
            tip = tips[get_thai_date().day % len(tips)]
            await send_reminder(family_id, tip)

async def check_bath_reminder():
    """Проверить напоминания о купании"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT family_id FROM families")
    families = cur.fetchall()
    conn.close()
    
    for (family_id,) in families:
        bath_settings = get_bath_settings(family_id)
        if not bath_settings['enabled']:
            continue
            
        now = get_thai_time()
        bath_time = now.replace(hour=bath_settings['hour'], minute=bath_settings['minute'], second=0, microsecond=0)
        
        # Проверяем, нужно ли напомнить за час до купания
        reminder_time = bath_time - timedelta(hours=1)
        
        if now.hour == reminder_time.hour and now.minute == reminder_time.minute:
            await send_reminder(family_id, f"🛁 Напоминание: через час время купания малыша! ({bath_time.strftime('%H:%M')})")

@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Обработка команды /start"""
    user_id = event.sender_id
    
    # Проверяем, есть ли пользователь в семье
    family_id = get_family_id(user_id)
    
    if family_id:
        # Пользователь уже в семье
        buttons = [
            [Button.inline("🍼 Кормление", b"feeding")],
            [Button.inline("👶 Смена подгузника", b"diaper")],
            [Button.inline("📊 Статистика", b"stats")],
            [Button.inline("⚙️ Настройки", b"settings")]
        ]
        
        await event.respond(
            "👋 Добро пожаловать в BabyCareBot!\n\n"
            "Выберите действие:",
            buttons=buttons
        )
    else:
        # Новый пользователь
        buttons = [
            [Button.inline("👨‍👩‍👧 Создать семью", b"create_family")],
            [Button.inline("🔗 Присоединиться к семье", b"join_family")]
        ]
        
        await event.respond(
            "👋 Добро пожаловать в BabyCareBot!\n\n"
            "Для начала работы нужно создать или присоединиться к семье:",
            buttons=buttons
        )

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """Обработка callback запросов"""
    data = event.data.decode()
    user_id = event.sender_id
    
    if data == "feeding":
        family_id = get_family_id(user_id)
        if family_id:
            # Получаем информацию о пользователе
            user = await client.get_entity(user_id)
            user_name = user.first_name if user.first_name else "Неизвестно"
            
            # Записываем кормление
            record_feeding(family_id, user_id, "Родитель", user_name)
            
            await event.respond("✅ Кормление записано!")
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    elif data == "diaper":
        family_id = get_family_id(user_id)
        if family_id:
            # Получаем информацию о пользователе
            user = await client.get_entity(user_id)
            user_name = user.first_name if user.first_name else "Неизвестно"
            
            # Записываем смену подгузника
            record_diaper(family_id, user_id, "Родитель", user_name)
            
            await event.respond("✅ Смена подгузника записана!")
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    elif data == "stats":
        family_id = get_family_id(user_id)
        if family_id:
            await show_stats(event, family_id)
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    elif data == "settings":
        family_id = get_family_id(user_id)
        if family_id:
            await settings_menu(event, family_id)
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    elif data == "create_family":
        await event.respond(
            "Введите название семьи:",
            buttons=[[Button.inline("🔙 Назад", b"back_to_start")]]
        )
        manual_feeding_pending[user_id] = "create_family"
    
    elif data == "join_family":
        await event.respond(
            "Для присоединения к семье попросите администратора семьи добавить вас.",
            buttons=[[Button.inline("🔙 Назад", b"back_to_start")]]
        )
    
    elif data == "back_to_start":
        await start_command(event)
    
    elif data == "baby_info":
        family_id = get_family_id(user_id)
        if family_id:
            await baby_info_menu(event, family_id)
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    elif data.startswith("edit_baby_"):
        field = data.replace("edit_baby_", "")
        family_id = get_family_id(user_id)
        if family_id:
            baby_edit_pending[user_id] = field
            if field == "name":
                await event.respond("Введите имя малыша:")
            elif field == "birth":
                await event.respond("Введите дату рождения малыша (формат: ДД.ММ.ГГГГ):")
            elif field == "gender":
                buttons = [
                    [Button.inline("👶 Мальчик", b"set_baby_gender_m")],
                    [Button.inline("👧 Девочка", b"set_baby_gender_f")]
                ]
                await event.respond("Выберите пол малыша:", buttons=buttons)
            elif field == "weight":
                await event.respond("Введите вес малыша в кг (например: 7.5):")
            elif field == "height":
                await event.respond("Введите рост малыша в см (например: 68.5):")
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    elif data.startswith("set_baby_gender_"):
        gender = "Мальчик" if data.endswith("_m") else "Девочка"
        family_id = get_family_id(user_id)
        if family_id:
            update_baby_info(family_id, gender=gender)
            await event.respond(f"✅ Пол малыша обновлен: {gender}")
            await baby_info_menu(event, family_id)
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    elif data == "back_to_settings":
        family_id = get_family_id(user_id)
        if family_id:
            await settings_menu(event, family_id)
        else:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
    
    # Обработка настроек кормления
    elif data.startswith("feed_interval_"):
        interval = int(data.replace("feed_interval_", ""))
        family_id = get_family_id(user_id)
        if family_id:
            set_feed_interval(family_id, interval)
            await event.respond(f"✅ Интервал кормления установлен: {interval} часа")
            await settings_menu(event, family_id)
    
    # Обработка настроек подгузников
    elif data.startswith("diaper_interval_"):
        interval = int(data.replace("diaper_interval_", ""))
        family_id = get_family_id(user_id)
        if family_id:
            set_diaper_interval(family_id, interval)
            await event.respond(f"✅ Интервал смены подгузника установлен: {interval} часа")
            await settings_menu(event, family_id)
    
    # Обработка настроек советов
    elif data == "toggle_tips":
        family_id = get_family_id(user_id)
        if family_id:
            settings = get_settings(family_id)
            new_status = not settings.get('tips_enabled', True) if settings else False
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO settings (family_id, tips_enabled)
                VALUES (?, ?)
            """, (family_id, 1 if new_status else 0))
            conn.commit()
            conn.close()
            
            status_text = "включены" if new_status else "отключены"
            await event.respond(f"✅ Советы {status_text}")
            await settings_menu(event, family_id)
    
    elif data.startswith("tips_time_"):
        time_parts = data.replace("tips_time_", "").split("_")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        family_id = get_family_id(user_id)
        if family_id:
            set_tips_time(family_id, hour, minute)
            await event.respond(f"✅ Время советов установлено: {hour:02d}:{minute:02d}")
            await settings_menu(event, family_id)
    
    # Обработка настроек купания
    elif data.startswith("bath_interval_"):
        interval = int(data.replace("bath_interval_", ""))
        family_id = get_family_id(user_id)
        if family_id:
            set_bath_interval(family_id, interval)
            await event.respond(f"✅ Интервал купания установлен: {interval} день(дней)")
            await settings_menu(event, family_id)
    
    elif data.startswith("bath_time_"):
        time_parts = data.replace("bath_time_", "").split("_")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        family_id = get_family_id(user_id)
        if family_id:
            set_bath_time(family_id, hour, minute)
            await event.respond(f"✅ Время купания установлено: {hour:02d}:{minute:02d}")
            await settings_menu(event, family_id)
    
    elif data == "toggle_bath":
        family_id = get_family_id(user_id)
        if family_id:
            bath_settings = get_bath_settings(family_id)
            new_status = not bath_settings['enabled']
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO settings (family_id, bath_enabled)
                VALUES (?, ?)
            """, (family_id, 1 if new_status else 0))
            conn.commit()
            conn.close()
            
            status_text = "включены" if new_status else "отключены"
            await event.respond(f"✅ Напоминания о купании {status_text}")
            await settings_menu(event, family_id)

async def show_stats(event, family_id):
    """Показать статистику"""
    # Получаем последние записи
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Последние кормления
    cur.execute("""
        SELECT timestamp, author_name FROM feedings 
        WHERE family_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 5
    """, (family_id,))
    feedings = cur.fetchall()
    
    # Последние смены подгузников
    cur.execute("""
        SELECT timestamp, author_name FROM diapers 
        WHERE family_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 5
    """, (family_id,))
    diapers = cur.fetchall()
    
    conn.close()
    
    # Формируем сообщение
    message = "📊 **Статистика за последние записи:**\n\n"
    
    message += "🍼 **Последние кормления:**\n"
    for timestamp, author in feedings:
        try:
            dt = datetime.fromisoformat(timestamp)
            message += f"• {dt.strftime('%d.%m %H:%M')} - {author}\n"
        except:
            continue
    
    message += "\n👶 **Последние смены подгузников:**\n"
    for timestamp, author in diapers:
        try:
            dt = datetime.fromisoformat(timestamp)
            message += f"• {dt.strftime('%d.%m %H:%M')} - {author}\n"
        except:
            continue
    
    buttons = [[Button.inline("🔙 Назад", b"back_to_start")]]
    await event.respond(message, buttons=buttons)

async def settings_menu(event, family_id):
    """Меню настроек"""
    settings = get_settings(family_id)
    bath_settings = get_bath_settings(family_id)
    
    # Определяем статус советов
    tips_enabled = settings.get('tips_enabled', True) if settings else True
    tips_label = "🔔 Советы: ВКЛ" if tips_enabled else "🔕 Советы: ВЫКЛ"
    
    # Определяем время советов
    tips_hour = settings.get('tips_time_hour', 9) if settings else 9
    tips_minute = settings.get('tips_time_minute', 0) if settings else 0
    
    # Определяем статус купания
    bath_enabled = bath_settings.get('enabled', True)
    bath_label = "🛁 Купание: ВКЛ" if bath_enabled else "🛁 Купание: ВЫКЛ"
    
    # Определяем время купания
    bath_hour = bath_settings.get('hour', 19)
    bath_minute = bath_settings.get('minute', 0)
    
    buttons = [
        [Button.inline(f"🍼 Интервал кормления: {settings.get('feed_interval', 3)}ч", b"feed_interval_menu")],
        [Button.inline(f"👶 Интервал подгузника: {settings.get('diaper_interval', 2)}ч", b"diaper_interval_menu")],
        [Button.inline(tips_label, b"toggle_tips")],
        [Button.inline(f"🕐 Время советов: {tips_hour:02d}:{tips_minute:02d}", b"tips_time_menu")],
        [Button.inline("👶 Информация о малыше", b"baby_info")],
        [Button.inline("👤 Моя роль", b"my_role")],
        [Button.inline("👨‍👩‍👧 Управление семьей", b"family_management")]
    ]
    
    await event.respond(
        "⚙️ **Настройки:**\n\n"
        "Выберите, что хотите настроить:",
        buttons=buttons
    )

async def baby_info_menu(event, family_id):
    """Меню для настройки информации о малыше"""
    baby_info = get_baby_info(family_id)
    
    text = f"👶 **Информация о малыше:**\n\n"
    text += f"**Имя:** {baby_info['name']}\n"
    text += f"**Дата рождения:** {baby_info['birth_date'] or 'Не указана'}\n"
    text += f"**Пол:** {baby_info['gender']}\n"
    text += f"**Вес:** {baby_info['weight']} кг\n"
    text += f"**Рост:** {baby_info['height']} см\n\n"
    text += "Выберите, что хотите изменить:"
    
    buttons = [
        [Button.inline("✏️ Изменить имя", b"edit_baby_name")],
        [Button.inline("📅 Изменить дату рождения", b"edit_baby_birth")],
        [Button.inline("👶 Изменить пол", b"edit_baby_gender")],
        [Button.inline("⚖️ Изменить вес", b"edit_baby_weight")],
        [Button.inline("📏 Изменить рост", b"edit_baby_height")],
        [Button.inline("🔙 Назад к настройкам", b"back_to_settings")]
    ]
    
    await event.respond(text, buttons=buttons)

@client.on(events.NewMessage)
async def handle_text(event):
    """Обработка текстовых сообщений"""
    user_id = event.sender_id
    text = event.text
    
    if user_id in manual_feeding_pending:
        action = manual_feeding_pending[user_id]
        
        if action == "create_family":
            if len(text) > 50:
                await event.respond("❌ Название семьи слишком длинное. Максимум 50 символов.")
                return
            
            # Создаем семью
            family_id = create_family(text)
            
            # Добавляем пользователя как администратора
            user = await client.get_entity(user_id)
            user_name = user.first_name if user.first_name else "Неизвестно"
            add_family_member(family_id, user_id, "Администратор", user_name)
            
            del manual_feeding_pending[user_id]
            
            await event.respond(
                f"✅ Семья '{text}' создана!\n"
                f"Вы добавлены как администратор.\n\n"
                f"Теперь вы можете использовать бота для записи кормлений и смен подгузников.",
                buttons=[[Button.inline("🔙 В главное меню", b"back_to_start")]]
            )
    
    elif user_id in baby_edit_pending:
        field = baby_edit_pending[user_id]
        family_id = get_family_id(user_id)
        
        if not family_id:
            await event.respond("❌ Ошибка: вы не состоите в семье.")
            del baby_edit_pending[user_id]
            return
        
        if field == "name":
            if len(text) > 50:
                await event.respond("❌ Имя слишком длинное. Максимум 50 символов.")
                return
            update_baby_info(family_id, name=text)
            await event.respond(f"✅ Имя малыша обновлено: {text}")
        
        elif field == "birth":
            try:
                # Проверяем формат даты
                datetime.strptime(text, "%d.%m.%Y")
                update_baby_info(family_id, birth_date=text)
                await event.respond(f"✅ Дата рождения обновлена: {text}")
            except ValueError:
                await event.respond("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
                return
        
        elif field == "weight":
            try:
                weight = float(text)
                if weight < 0 or weight > 50:
                    await event.respond("❌ Неверный вес. Введите число от 0 до 50 кг.")
                    return
                update_baby_info(family_id, weight=weight)
                await event.respond(f"✅ Вес обновлен: {weight} кг")
            except ValueError:
                await event.respond("❌ Неверный формат веса. Введите число (например: 7.5)")
                return
        
        elif field == "height":
            try:
                height = float(text)
                if height < 0 or height > 200:
                    await event.respond("❌ Неверный рост. Введите число от 0 до 200 см.")
                    return
                update_baby_info(family_id, height=height)
                await event.respond(f"✅ Рост обновлен: {height} см")
            except ValueError:
                await event.respond("❌ Неверный формат роста. Введите число (например: 68.5)")
                return
        
        del baby_edit_pending[user_id]
        await baby_info_menu(event, family_id)

async def main():
    """Основная функция"""
    # Инициализируем базу данных
    init_db()
    
    # Настраиваем планировщик задач
    scheduler.add_job(check_feeding_reminder, 'interval', minutes=30)
    scheduler.add_job(check_diaper_reminder, 'interval', minutes=30)
    scheduler.add_job(send_tips, 'cron', hour=9, minute=0)
    scheduler.add_job(check_bath_reminder, 'interval', minutes=1)
    
    # Запускаем планировщик
    scheduler.start()
    
    # Запускаем бота
    await client.start(bot_token=BOT_TOKEN)
    print("🤖 BabyCareBot запущен на Replit!")
    
    # Держим бота запущенным
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Запускаем бота
    asyncio.run(main())
