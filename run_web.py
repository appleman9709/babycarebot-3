#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска веб-приложения BabyCareBot на Replit
"""

import os
import sys

# Добавляем путь к mini_app
sys.path.append('mini_app')

# Импортируем и запускаем веб-приложение
from app_replit import app

if __name__ == '__main__':
    # Инициализируем базу данных при запуске
    from app_replit import init_database
    init_database()
    
    # Запускаем Flask приложение
    app.run(debug=True, host='0.0.0.0', port=8080)
