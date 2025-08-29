# BabyCareBot 2.0

Telegram бот для помощи родителям в уходе за малышом с веб-дашбордом.

## 🚀 Возможности

### Telegram Bot
- 📝 Запись кормлений и смен подгузников
- ⏰ Напоминания о кормлении, смене подгузников и купании
- 👥 Управление семьей и ролями
- 💡 Полезные советы для родителей
- 👶 Настройка информации о малыше (имя, дата рождения, пол, вес, рост)

### Веб-дашборд
- 📊 Статистика кормлений и смен подгузников
- 📈 Графики активности по дням
- 👶 Информация о малыше
- ⚙️ Настройки ухода
- 📱 Адаптивный дизайн

## 🛠 Технологии

- **Backend**: Python, Flask, SQLite
- **Telegram Bot**: Telethon
- **Планировщик**: APScheduler
- **Frontend**: HTML, CSS (Bootstrap 5), JavaScript (Chart.js)
- **База данных**: SQLite3

## 📁 Структура проекта

```
BabyCareBot 1.2/
├── main.py                 # Основной бот
├── mini_app/              # Веб-дашборд
│   ├── app.py             # Flask приложение
│   ├── templates/         # HTML шаблоны
│   │   └── dashboard.html # Главная страница
│   └── requirements.txt   # Зависимости для веб-приложения
├── config.env             # Конфигурация (не включен в Git)
├── requirements.txt       # Зависимости для бота
└── README.md             # Документация
```

## 🚀 Развертывание

### 1. Клонирование репозитория
```bash
git clone https://github.com/appleman9709/babycarebot-2.git
cd babycarebot-2
```

### 2. Настройка Telegram Bot
1. Получите API_ID и API_HASH на [my.telegram.org/apps](https://my.telegram.org/apps)
2. Получите BOT_TOKEN от [@BotFather](https://t.me/BotFather)
3. Создайте файл `config.env`:
```env
API_ID=ваш_api_id
API_HASH=ваш_api_hash
BOT_TOKEN=ваш_bot_token
```

### 3. Установка зависимостей
```bash
# Для основного бота
pip install -r requirements.txt

# Для веб-дашборда
cd mini_app
pip install -r requirements.txt
```

### 4. Запуск
```bash
# Запуск бота
python main.py

# Запуск веб-дашборда (в отдельном терминале)
cd mini_app
python app.py
```

## 🌐 Развертывание на Vercel

### 1. Подготовка для Vercel
Создайте файл `vercel.json` в корне проекта:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "mini_app/app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "mini_app/app.py"
    }
  ]
}
```

### 2. Развертывание
1. Подключите репозиторий к Vercel
2. Установите переменные окружения в Vercel Dashboard
3. Deploy!

## 📱 Использование

### Telegram Bot
1. Найдите бота по имени
2. Отправьте `/start` для начала работы
3. Создайте семью или присоединитесь к существующей
4. Настройте информацию о малыше в настройках

### Веб-дашборд
1. Откройте дашборд в браузере
2. Просматривайте статистику и активность
3. Обновляйте информацию о малыше

## 🔧 Настройка

### Интервалы напоминаний
- **Кормление**: 1-6 часов
- **Смена подгузников**: 1-6 часов
- **Купание**: 1-7 дней
- **Советы**: ежедневно в указанное время

### Время напоминаний
- **Купание**: настраиваемое время (по умолчанию 19:00)
- **Советы**: настраиваемое время (по умолчанию 09:00)

## 📊 База данных

Проект использует SQLite3 с таблицами:
- `families` - семьи
- `family_members` - члены семьи
- `baby_info` - информация о малыше
- `feedings` - записи кормлений
- `diapers` - записи смен подгузников
- `settings` - настройки семьи

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. `LICENSE` для деталей.

## 📞 Поддержка

Если у вас есть вопросы или предложения, создайте Issue в репозитории.

---

**BabyCareBot** - заботливый помощник для родителей! 👶❤️
