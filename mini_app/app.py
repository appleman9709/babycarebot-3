#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BabyCareBot Mini App - Веб-дашборд для родителей
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import pytz
import json

app = Flask(__name__)

# Функция для получения тайского времени
def get_thai_time():
    """Получить текущее время в тайском часовом поясе"""
    thai_tz = pytz.timezone('Asia/Bangkok')
    utc_now = datetime.now(pytz.UTC)
    thai_now = utc_now.astimezone(thai_tz)
    return thai_now

def get_thai_date():
    """Получить текущую дату в тайском часовом поясе"""
    return get_thai_time().date()

def get_baby_info(family_id):
    """Получить информацию о малыше"""
    conn = sqlite3.connect("../babybot.db")
    cur = conn.cursor()
    
    # Получаем информацию о семье
    cur.execute("SELECT name FROM families WHERE id = ?", (family_id,))
    family_name = cur.fetchone()
    
    # Получаем членов семьи
    cur.execute("SELECT user_id, role, name FROM family_members WHERE family_id = ?", (family_id,))
    members = cur.fetchall()
    
    # Получаем настройки
    cur.execute("SELECT feed_interval, diaper_interval, tips_enabled, tips_time_hour, tips_time_minute, bath_interval, bath_time_hour, bath_time_minute, bath_enabled FROM settings WHERE family_id = ?", (family_id,))
    settings = cur.fetchone()
    
    # Получаем информацию о малыше из базы данных
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
        # Значения по умолчанию
        baby_info = {
            'name': 'Малыш',
            'age_months': 0,
            'weight': 0.0,
            'height': 0.0,
            'birth_date': 'Не указана',
            'gender': 'Не указан'
        }
    
    return {
        'family_name': family_name[0] if family_name else 'Неизвестная семья',
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
    conn = sqlite3.connect("../babybot.db")
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
    
    return activities[:20]  # Возвращаем последние 20 активностей

def get_daily_stats(family_id, days=7):
    """Получить статистику по дням"""
    conn = sqlite3.connect("../babybot.db")
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
        print(f"DEBUG: Запрос информации о малыше для семьи {family_id}")
        baby_data = get_baby_info(family_id)
        print(f"DEBUG: Получены данные: {baby_data}")
        if baby_data:
            return jsonify(baby_data)
        else:
            return jsonify({'error': 'Семья не найдена'}), 404
    except Exception as e:
        print(f"ERROR: Ошибка в API baby: {e}")
        import traceback
        traceback.print_exc()
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
        'service': 'babycare-mini-app',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Получаем порт из переменных окружения Replit или используем 5000 по умолчанию
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
