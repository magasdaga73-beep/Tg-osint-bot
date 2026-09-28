# PUBLIC OSINT Telegram Bot v2

Telegram-бот для навигации по публичному интернет-поиску по номеру телефона и ФИО.

## Возможности
- 📱 поиск по номеру телефона;
- 👤 поиск по имени/фамилии или полному ФИО;
- Google, Bing и DuckDuckGo;
- нормализация российского номера 8XXXXXXXXXX → 7XXXXXXXXXX;
- история последних 10 запросов в SQLite;
- Telegram-меню.

Бот не подключается к слитым/закрытым базам, не обходит авторизацию и не извлекает скрытые персональные данные. Он только формирует ссылки на обычный публичный веб-поиск.

## Render
Build Command:
`pip install -r requirements.txt`

Start Command:
`python bot.py`

Environment Variable:
KEY = `BOT_TOKEN`
VALUE = токен Telegram-бота от @BotFather.

Не добавляй токен в GitHub или bot.py.

При запуске создаётся `bot.db`.
