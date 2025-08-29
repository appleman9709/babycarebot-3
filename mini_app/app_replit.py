#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BabyCareBot Mini App - Веб-дашборд для родителей (Replit версия)
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)

# Путь к базе данных на Replit
DB_PATH = os.path.join(os.getcwd(), 'babybot.db')

def get_thai_time():
    """Получить текущее время в тайском часовом поясе"""
    return datetime.now()

def get_thai_date():
    """Получить текущую дату в тайском часовом поясе"""
    return get_thai_time().date()

def init_database():
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
    
    # Создаем тестовую семью, если её нет
    cur.execute("SELECT id FROM families WHERE name = 'Коршиковы'")
    if not cur.fetchone():
        cur.execute("INSERT INTO families (name) VALUES (?)", ('Коршиковы',))
        family_id = cur.lastrowid
        
        # Добавляем тестовых членов семьи
        cur.execute("INSERT INTO family_members (family_id, user_id, role, name) VALUES (?, ?, ?, ?)",
                   (family_id, 461993396, 'Папа', 'Петя'))
        cur.execute("INSERT INTO family_members (family_id, user_id, role, name) VALUES (?, ?, ?, ?)",
                   (family_id, 361468682, 'Мама', 'Надежда'))
        
        # Добавляем настройки
        cur.execute("""
            INSERT INTO settings (family_id, feed_interval, diaper_interval, 
                               tips_time_hour, tips_time_minute, 
                               bath_interval, bath_time_hour, bath_time_minute, bath_enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (family_id, 4, 2, 9, 0, 2, 19, 0, 1))
        
        # Добавляем информацию о малыше
        cur.execute("""
            INSERT INTO baby_info (family_id, name, birth_date, gender, weight, height)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (family_id, 'Анна', '15.01.2024', 'Девочка', 7.2, 68.0))
        
        # Добавляем тестовые записи активности
        for i in range(5):
            # Кормления
            feeding_time = datetime.now() - timedelta(days=i, hours=10+i)
            cur.execute("""
                INSERT INTO feedings (family_id, author_id, timestamp, author_role, author_name)
                VALUES (?, ?, ?, ?, ?)
            """, (family_id, 361468682, feeding_time.isoformat(), 'Мама', 'Надежда'))
            
            # Смены подгузников
            diaper_time = datetime.now() - timedelta(days=i, hours=12+i)
            cur.execute("""
                INSERT INTO diapers (family_id, author_id, timestamp, author_role, author_name)
                VALUES (?, ?, ?, ?, ?)
            """, (family_id, 461993396, diaper_time.isoformat(), 'Папа', 'Петя'))
    
    conn.commit()
    conn.close()
    return True

def get_baby_info(family_id):
    """Получить информацию о малыше"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Получаем информацию о семье
    cur.execute("SELECT name FROM families WHERE id = ?", (family_id,))
    family_result = cur.fetchone()
    
    if not family_result:
        conn.close()
        return None
    
    family_name = family_result[0]
    
    # Получаем членов семьи
    cur.execute("SELECT user_id, role, name FROM family_members WHERE family_id = ?", (family_id,))
    members = cur.fetchall()
    
    # Получаем настройки
    cur.execute("""
        SELECT feed_interval, diaper_interval, tips_enabled, tips_time_hour, tips_time_minute, 
               bath_interval, bath_time_hour, bath_time_minute, bath_enabled 
        FROM settings WHERE family_id = ?
    """, (family_id,))
    settings = cur.fetchone()
    
    # Получаем информацию о малыше
    cur.execute("SELECT name, birth_date, gender, weight, height FROM baby_info WHERE family_id = ?", (family_id,))
    baby_result = cur.fetchone()
    
    conn.close()
    
    if baby_result:
        name, birth_date, gender, weight, height = baby_result
        
        # Вычисляем возраст в месяцах
        age_months = 0
        if birth_date:
            try:
                birth_dt = datetime.strptime(birth_date, "%d.%m.%Y")
                today = datetime.now()
                age_months = (today.year - birth_dt.year) * 12 + (today.month - birth_dt.month)
                if today.day < birth_dt.day:
                    age_months -= 1
            except:
                age_months = 0
        
        baby_info = {
            'name': name,
            'age_months': age_months,
            'weight': weight,
            'height': height,
            'birth_date': birth_date or 'Не указана',
            'gender': gender
        }
    else:
        baby_info = {
            'name': 'Малыш',
            'age_months': 0,
            'weight': 0.0,
            'height': 0.0,
            'birth_date': 'Не указана',
            'gender': 'Не указан'
        }
    
    return {
        'family_name': family_name,
        'baby': baby_info,
        'members': [{'user_id': m[0], 'role': m[1], 'name': m[2]} for m in members],
        'settings': {
            'feed_interval': settings[0] if settings else 3,
            'diaper_interval': settings[1] if settings else 2,
            'tips_enabled': settings[2] if settings else 1,
            'tips_time': f"{settings[3]:02d}:{settings[4]:02d}" if settings and settings[3] is not None else "09:00",
            'bath_interval': settings[5] if settings else 1,
            'bath_time': f"{settings[6]:02d}:{settings[7]:02d}" if settings and settings[6] is not None else "19:00",
            'bath_enabled': settings[8] if settings else 1
        }
    }

def get_recent_activity(family_id, days=7):
    """Получить последнюю активность семьи"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Получаем кормления за последние дни
    start_date = (get_thai_date() - timedelta(days=days)).isoformat()
    cur.execute("""
        SELECT timestamp, author_role, author_name 
        FROM feedings 
        WHERE family_id = ? AND timestamp >= ? 
        ORDER BY timestamp DESC
    """, (family_id, start_date))
    feedings = cur.fetchall()
    
    # Получаем смены подгузников за последние дни
    cur.execute("""
        SELECT timestamp, author_role, author_name 
        FROM diapers 
        WHERE family_id = ? AND timestamp >= ? 
        ORDER BY timestamp DESC
    """, (family_id, start_date))
    diapers = cur.fetchall()
    
    conn.close()
    
    # Форматируем данные
    activities = []
    
    for f in feedings:
        try:
            dt = datetime.fromisoformat(f[0])
            activities.append({
                'type': 'feeding',
                'time': dt.strftime('%H:%M'),
                'date': dt.strftime('%d.%m'),
                'author': f"{f[1]} {f[2]}" if f[1] and f[2] else "Неизвестно",
                'timestamp': f[0]
            })
        except:
            continue
    
    for d in diapers:
        try:
            dt = datetime.fromisoformat(d[0])
            activities.append({
                'type': 'diaper',
                'time': dt.strftime('%H:%M'),
                'date': dt.strftime('%d.%m'),
                'author': f"{d[1]} {d[2]}" if d[1] and d[2] else "Неизвестно",
                'timestamp': d[0]
            })
        except:
            continue
    
    # Сортируем по времени
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:20]

def get_daily_stats(family_id, days=7):
    """Получить статистику по дням"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    stats = []
    
    for i in range(days):
        target_date = get_thai_date() - timedelta(days=i)
        start_date = datetime.combine(target_date, datetime.min.time()).isoformat()
        end_date = datetime.combine(target_date, datetime.max.time()).isoformat()
        
        # Кормления за день
        cur.execute("""
            SELECT COUNT(*) FROM feedings 
            WHERE family_id = ? AND timestamp BETWEEN ? AND ?
        """, (family_id, start_date, end_date))
        feedings_count = cur.fetchone()[0]
        
        # Смены подгузников за день
        cur.execute("""
            SELECT COUNT(*) FROM diapers 
            WHERE family_id = ? AND timestamp BETWEEN ? AND ?
        """, (family_id, start_date, end_date))
        diapers_count = cur.fetchone()[0]
        
        stats.append({
            'date': target_date.strftime('%d.%m'),
            'feedings': feedings_count,
            'diapers': diapers_count,
            'total': feedings_count + diapers_count
        })
    
    conn.close()
    return stats

@app.route('/')
def dashboard():
    """Главная страница дашборда"""
    return render_template('dashboard.html')

@app.route('/api/baby/<int:family_id>')
def api_baby(family_id):
    """API для получения данных о малыше"""
    try:
        baby_data = get_baby_info(family_id)
        if baby_data:
            return jsonify(baby_data)
        else:
            return jsonify({'error': 'Семья не найдена'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity/<int:family_id>')
def api_activity(family_id):
    """API для получения последней активности"""
    try:
        days = request.args.get('days', 7, type=int)
        activities = get_recent_activity(family_id, days)
        return jsonify(activities)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/<int:family_id>')
def api_stats(family_id):
    """API для получения статистики"""
    try:
        days = request.args.get('days', 7, type=int)
        stats = get_daily_stats(family_id, days)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'babycare-mini-app-replit',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/init-db')
def init_db():
    """Инициализация базы данных"""
    if init_database():
        return jsonify({'status': 'success', 'message': 'База данных инициализирована'})
    else:
        return jsonify({'status': 'error', 'message': 'Ошибка инициализации базы данных'}), 500

if __name__ == '__main__':
    # Инициализируем базу данных при запуске
    init_database()
    app.run(debug=True, host='0.0.0.0', port=8080)
