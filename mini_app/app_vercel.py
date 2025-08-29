#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BabyCareBot Mini App - Веб-дашборд для родителей (Vercel версия)
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Демо-данные для Vercel (без базы данных)
def get_demo_baby_info(family_id):
    """Получить демо-информацию о малыше"""
    return {
        'family_name': 'Коршиковы',
        'baby': {
            'name': 'Анна',
            'age_months': 8,
            'weight': 7.2,
            'height': 68,
            'birth_date': '15.01.2024',
            'gender': 'Девочка'
        },
        'members': [
            {'user_id': 461993396, 'role': 'Папа', 'name': 'Петя'},
            {'user_id': 361468682, 'role': 'Мама', 'name': 'Надежда'}
        ],
        'settings': {
            'feed_interval': 4,
            'diaper_interval': 2,
            'tips_enabled': 1,
            'tips_time': '09:00',
            'bath_interval': 2,
            'bath_time': '19:00',
            'bath_enabled': 1
        }
    }

def get_demo_activity(family_id, days=7):
    """Получить демо-активность"""
    activities = []
    
    for i in range(min(days, 5)):
        # Кормления
        activities.append({
            'type': 'feeding',
            'time': f"{10 + i}:{30 + i:02d}",
            'date': f"{15 + i}.08",
            'author': 'Мама Надежда',
            'timestamp': f"2024-08-{15 + i}T{10 + i}:{30 + i:02d}:00"
        })
        
        # Смены подгузников
        activities.append({
            'type': 'diaper',
            'time': f"{12 + i}:{15 + i:02d}",
            'date': f"{15 + i}.08",
            'author': 'Папа Петя',
            'timestamp': f"2024-08-{15 + i}T{12 + i}:{15 + i:02d}:00"
        })
    
    # Сортируем по времени
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:20]

def get_demo_stats(family_id, days=7):
    """Получить демо-статистику"""
    stats = []
    
    for i in range(days):
        stats.append({
            'date': f"{15 + i}.08",
            'feedings': 3 + (i % 2),
            'diapers': 2 + (i % 3),
            'total': 5 + (i % 2) + (i % 3)
        })
    
    return stats

@app.route('/')
def dashboard():
    """Главная страница дашборда"""
    return render_template('dashboard.html')

@app.route('/api/baby/<int:family_id>')
def api_baby(family_id):
    """API для получения данных о малыше"""
    try:
        baby_data = get_demo_baby_info(family_id)
        return jsonify(baby_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity/<int:family_id>')
def api_activity(family_id):
    """API для получения последней активности"""
    try:
        days = request.args.get('days', 7, type=int)
        activities = get_demo_activity(family_id, days)
        return jsonify(activities)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/<int:family_id>')
def api_stats(family_id):
    """API для получения статистики"""
    try:
        days = request.args.get('days', 7, type=int)
        stats = get_demo_stats(family_id, days)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'babycare-mini-app-vercel',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
