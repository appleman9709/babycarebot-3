#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Альтернативный скрипт запуска для Replit
Запускает бота и дашборд в отдельных потоках
"""

import os
import sys
import threading
import time
import subprocess
from pathlib import Path

def install_dependencies():
    """Установка зависимостей"""
    print("🚀 Установка зависимостей...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Зависимости установлены")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Ошибка установки зависимостей: {e}")
        print("Продолжаем без установки...")

def run_bot():
    """Запуск основного бота"""
    print("🤖 Запуск Telegram бота...")
    try:
        # Импортируем и запускаем бота
        import main
        print("✅ Бот запущен успешно")
        
        # Запускаем планировщик
        main.scheduler.start()
        print("⏰ Планировщик запущен")
        
        # Запускаем бота
        main.client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()

def run_dashboard():
    """Запуск веб-дашборда"""
    print("🌐 Запуск веб-дашборда...")
    try:
        # Переходим в папку mini_app
        os.chdir('mini_app')
        
        # Импортируем и запускаем Flask приложение
        from app import app
        print("✅ Дашборд запущен успешно")
        
        # Запускаем Flask на всех интерфейсах
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        print(f"❌ Ошибка запуска дашборда: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция запуска"""
    print("🚀 Запуск BabyCareBot на Replit...")
    
    # Проверяем наличие необходимых файлов
    if not Path("main.py").exists():
        print("❌ Файл main.py не найден")
        return
    
    if not Path("mini_app/app.py").exists():
        print("❌ Файл mini_app/app.py не найден")
        return
    
    # Проверяем переменные окружения
    required_env = ['API_ID', 'API_HASH', 'BOT_TOKEN']
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_env)}")
        print("💡 Добавьте их в Secrets в Replit")
        return
    
    print("✅ Все переменные окружения установлены")
    
    # Устанавливаем зависимости
    install_dependencies()
    
    # Инициализируем базу данных
    print("🗄️ Проверка базы данных...")
    try:
        from init_db_replit import init_database
        init_database()
    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Небольшая задержка для запуска бота
    time.sleep(2)
    
    # Запускаем дашборд в основном потоке
    run_dashboard()

if __name__ == "__main__":
    main()
