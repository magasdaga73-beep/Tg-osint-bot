# Public OSINT Telegram Bot

Безопасный Telegram-бот для навигации по публичным источникам.

## Возможности
- /start и inline-меню
- поиск по нику, имени или домену через публичные поисковики
- ссылки на Google, Bing и DuckDuckGo
- локальная история последних 10 запросов
- SQLite-база `bot.db`
- блокировка запросов, связанных с чувствительными персональными данными и утечками

Бот не подключается к закрытым или слитым базам и не извлекает номера телефонов,
адреса, паспортные данные, банковские данные и т.п.

## 1. Создать бота
В Telegram открой `@BotFather`.
Выполни `/newbot`, задай имя и username.
Скопируй выданный токен.

## 2. Установить Python
Нужен Python 3.10+.

## 3. Установка
В папке проекта:

    python -m venv .venv

Windows:
    .venv\Scripts\activate

Linux/macOS:
    source .venv/bin/activate

Затем:

    pip install -r requirements.txt

## 4. Задать токен

Linux/macOS:
    export BOT_TOKEN="ТОКЕН_ОТ_BOTFATHER"

Windows PowerShell:
    $env:BOT_TOKEN="ТОКЕН_ОТ_BOTFATHER"

## 5. Запуск

    python bot.py

При первом запуске автоматически создастся `bot.db`.

## 6. Важно
Не публикуй токен бота в GitHub, чатах или скриншотах.
Если токен случайно раскрыт — перевыпусти его через BotFather.

## Структура
    tg_osint_bot/
      bot.py
      requirements.txt
      README.md
      bot.db
