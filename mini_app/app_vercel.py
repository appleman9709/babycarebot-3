#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BabyCareBot Mini App - Веб-дашборд для родителей (Vercel версия с PostgreSQL)
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = Flask(__name__)

# Функция для получения соединения с PostgreSQL
def get_db_connection():
    """Получить соединение с PostgreSQL"""
    try:
        # Получаем переменные окружения для подключения к базе данных
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Для Vercel PostgreSQL
            conn = psycopg2.connect(database_url)
        else:
            # Локальное подключение (для разработки)
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'babycarebot'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                port=os.getenv('DB_PORT', '5432')
            )
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Функция для инициализации базы данных
def init_database():
    """Инициализация таблиц в PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Создание таблиц
        cur.execute("""
            CREATE TABLE IF NOT EXISTS families (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                family_id INTEGER REFERENCES families(id),
                user_id BIGINT,
                role VARCHAR(100) DEFAULT 'Родитель',
                name VARCHAR(255) DEFAULT 'Неизвестно'
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedings (
                id SERIAL PRIMARY KEY,
                family_id INTEGER REFERENCES families(id),
                author_id BIGINT,
                timestamp TIMESTAMP NOT NULL,
                author_role VARCHAR(100) DEFAULT 'Родитель',
                author_name VARCHAR(255) DEFAULT 'Неизвестно'
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS diapers (
                id SERIAL PRIMARY KEY,
                family_id INTEGER REFERENCES families(id),
                author_id BIGINT,
                timestamp TIMESTAMP NOT NULL,
                author_role VARCHAR(100) DEFAULT 'Родитель',
                author_name VARCHAR(255) DEFAULT 'Неизвестно'
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                family_id INTEGER REFERENCES families(id),
                feed_interval INTEGER DEFAULT 3,
                diaper_interval INTEGER DEFAULT 2,
                tips_enabled INTEGER DEFAULT 1,
                tips_time_hour INTEGER DEFAULT 9,
                tips_time_minute INTEGER DEFAULT 0,
                bath_interval INTEGER DEFAULT 1,
                bath_time_hour INTEGER DEFAULT 19,
                bath_time_minute INTEGER DEFAULT 0,
                bath_enabled INTEGER DEFAULT 1
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS baby_info (
                family_id INTEGER PRIMARY KEY REFERENCES families(id),
                name VARCHAR(255) DEFAULT 'Малыш',
                birth_date VARCHAR(20),
                gender VARCHAR(50) DEFAULT 'Не указан',
                weight DECIMAL(4,2) DEFAULT 0.0,
                height DECIMAL(5,2) DEFAULT 0.0
            )
        """)
        
        # Создаем тестовую семью, если её нет
        cur.execute("SELECT id FROM families WHERE name = 'Коршиковы'")
        if not cur.fetchone():
            cur.execute("INSERT INTO families (name) VALUES ('Коршиковы') RETURNING id")
            family_id = cur.fetchone()[0]
            
            # Добавляем тестовых членов семьи
            cur.execute("""
                INSERT INTO family_members (family_id, user_id, role, name) 
                VALUES (%s, %s, %s, %s)
            """, (family_id, 461993396, 'Папа', 'Петя'))
            
            cur.execute("""
                INSERT INTO family_members (family_id, user_id, role, name) 
                VALUES (%s, %s, %s, %s)
            """, (family_id, 361468682, 'Мама', 'Надежда'))
            
            # Добавляем настройки
            cur.execute("""
                INSERT INTO settings (family_id, feed_interval, diaper_interval, 
                                   tips_time_hour, tips_time_minute, 
                                   bath_interval, bath_time_hour, bath_time_minute, bath_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (family_id, 4, 2, 9, 0, 2, 19, 0, 1))
            
            # Добавляем информацию о малыше
            cur.execute("""
                INSERT INTO baby_info (family_id, name, birth_date, gender, weight, height)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (family_id, 'Анна', '15.01.2024', 'Девочка', 7.2, 68.0))
            
            # Добавляем тестовые записи активности
            for i in range(5):
                # Кормления
                cur.execute("""
                    INSERT INTO feedings (family_id, author_id, timestamp, author_role, author_name)
                    VALUES (%s, %s, %s, %s, %s)
                """, (family_id, 361468682, 
                      datetime.now() - timedelta(days=i, hours=10+i), 
                      'Мама', 'Надежда'))
                
                # Смены подгузников
                cur.execute("""
                    INSERT INTO diapers (family_id, author_id, timestamp, author_role, author_name)
                    VALUES (%s, %s, %s, %s, %s)
                """, (family_id, 461993396, 
                      datetime.now() - timedelta(days=i, hours=12+i), 
                      'Папа', 'Петя'))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка инициализации базы данных: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False

def get_baby_info(family_id):
    """Получить информацию о малыше из PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Получаем информацию о семье
        cur.execute("SELECT name FROM families WHERE id = %s", (family_id,))
        family_result = cur.fetchone()
        
        if not family_result:
            cur.close()
            conn.close()
            return None
        
        family_name = family_result['name']
        
        # Получаем членов семьи
        cur.execute("SELECT user_id, role, name FROM family_members WHERE family_id = %s", (family_id,))
        members = cur.fetchall()
        
        # Получаем настройки
        cur.execute("""
            SELECT feed_interval, diaper_interval, tips_enabled, tips_time_hour, tips_time_minute, 
                   bath_interval, bath_time_hour, bath_time_minute, bath_enabled 
            FROM settings WHERE family_id = %s
        """, (family_id,))
        settings_result = cur.fetchone()
        
        # Получаем информацию о малыше
        cur.execute("""
            SELECT name, birth_date, gender, weight, height 
            FROM baby_info WHERE family_id = %s
        """, (family_id,))
        baby_result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if baby_result:
            # Вычисляем возраст в месяцах
            age_months = 0
            if baby_result['birth_date']:
                try:
                    birth_dt = datetime.strptime(baby_result['birth_date'], "%d.%m.%Y")
                    today = datetime.now()
                    age_months = (today.year - birth_dt.year) * 12 + (today.month - birth_dt.month)
                    if today.day < birth_dt.day:
                        age_months -= 1
                except:
                    age_months = 0
            
            baby_info = {
                'name': baby_result['name'],
                'age_months': age_months,
                'weight': float(baby_result['weight']),
                'height': float(baby_result['height']),
                'birth_date': baby_result['birth_date'] or 'Не указана',
                'gender': baby_result['gender']
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
            'members': [{'user_id': m['user_id'], 'role': m['role'], 'name': m['name']} for m in members],
            'settings': {
                'feed_interval': settings_result['feed_interval'] if settings_result else 3,
                'diaper_interval': settings_result['diaper_interval'] if settings_result else 2,
                'tips_enabled': settings_result['tips_enabled'] if settings_result else 1,
                'tips_time': f"{settings_result['tips_time_hour']:02d}:{settings_result['tips_time_minute']:02d}" if settings_result and settings_result['tips_time_hour'] is not None else "09:00",
                'bath_interval': settings_result['bath_interval'] if settings_result else 1,
                'bath_time': f"{settings_result['bath_time_hour']:02d}:{settings_result['bath_time_minute']:02d}" if settings_result and settings_result['bath_time_hour'] is not None else "19:00",
                'bath_enabled': settings_result['bath_enabled'] if settings_result else 1
            }
        }
        
    except Exception as e:
        print(f"Ошибка получения информации о малыше: {e}")
        if conn:
            conn.close()
        return None

def get_recent_activity(family_id, days=7):
    """Получить последнюю активность семьи из PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Получаем кормления за последние дни
        start_date = datetime.now() - timedelta(days=days)
        cur.execute("""
            SELECT timestamp, author_role, author_name 
            FROM feedings 
            WHERE family_id = %s AND timestamp >= %s 
            ORDER BY timestamp DESC
        """, (family_id, start_date))
        feedings = cur.fetchall()
        
        # Получаем смены подгузников за последние дни
        cur.execute("""
            SELECT timestamp, author_role, author_name 
            FROM diapers 
            WHERE family_id = %s AND timestamp >= %s 
            ORDER BY timestamp DESC
        """, (family_id, start_date))
        diapers = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Форматируем данные
        activities = []
        
        for f in feedings:
            activities.append({
                'type': 'feeding',
                'time': f['timestamp'].strftime('%H:%M'),
                'date': f['timestamp'].strftime('%d.%m'),
                'author': f"{f['author_role']} {f['author_name']}" if f['author_role'] and f['author_name'] else "Неизвестно",
                'timestamp': f['timestamp'].isoformat()
            })
        
        for d in diapers:
            activities.append({
                'type': 'diaper',
                'time': d['timestamp'].strftime('%H:%M'),
                'date': d['timestamp'].strftime('%d.%m'),
                'author': f"{d['author_role']} {d['author_name']}" if d['author_role'] and d['author_name'] else "Неизвестно",
                'timestamp': d['timestamp'].isoformat()
            })
        
        # Сортируем по времени
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:20]
        
    except Exception as e:
        print(f"Ошибка получения активности: {e}")
        if conn:
            conn.close()
        return []

def get_daily_stats(family_id, days=7):
    """Получить статистику по дням из PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        stats = []
        
        for i in range(days):
            target_date = datetime.now() - timedelta(days=i)
            start_date = datetime.combine(target_date.date(), datetime.min.time())
            end_date = datetime.combine(target_date.date(), datetime.max.time())
            
            # Кормления за день
            cur.execute("""
                SELECT COUNT(*) FROM feedings 
                WHERE family_id = %s AND timestamp BETWEEN %s AND %s
            """, (family_id, start_date, end_date))
            feedings_count = cur.fetchone()['count']
            
            # Смены подгузников за день
            cur.execute("""
                SELECT COUNT(*) FROM diapers 
                WHERE family_id = %s AND timestamp BETWEEN %s AND %s
            """, (family_id, start_date, end_date))
            diapers_count = cur.fetchone()['count']
            
            stats.append({
                'date': target_date.strftime('%d.%m'),
                'feedings': feedings_count,
                'diapers': diapers_count,
                'total': feedings_count + diapers_count
            })
        
        cur.close()
        conn.close()
        return stats
        
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        if conn:
            conn.close()
        return []

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
        'service': 'babycare-mini-app-vercel-postgres',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/init-db')
def init_db():
    """Инициализация базы данных (только для разработки)"""
    if init_database():
        return jsonify({'status': 'success', 'message': 'База данных инициализирована'})
    else:
        return jsonify({'status': 'error', 'message': 'Ошибка инициализации базы данных'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
