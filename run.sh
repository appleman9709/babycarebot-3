#!/bin/bash
# Скрипт запуска для Replit

echo "🚀 Установка зависимостей..."
pip3 install -r requirements.txt

echo "🤖 Запуск BabyCareBot..."
python3 replit_start.py
