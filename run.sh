#!/bin/bash
# Скрипт запуска для Replit

echo "🚀 Установка зависимостей..."
pip install -r requirements.txt

echo "🤖 Запуск BabyCareBot..."
python replit_start.py
