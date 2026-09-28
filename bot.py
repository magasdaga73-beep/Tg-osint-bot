import os
import re
import sqlite3
from urllib.parse import quote_plus

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Публичные поисковые источники. Бот НЕ обращается к слитым/закрытым базам.
SEARCH_ENGINES = [
    ("Google", "https://www.google.com/search?q={q}"),
    ("Bing", "https://www.bing.com/search?q={q}"),
    ("DuckDuckGo", "https://duckduckgo.com/?q={q}"),
]

BLOCKED_PATTERNS = [
    r"\bпаспорт\b", r"\bснилс\b", r"\bинн\b",
    r"\bбанковск", r"\bкарта\b", r"\bкредит\b",
    r"\bадрес\b", r"\bместо\s+жительства\b",
    r"\bпропис", r"\bтелефон\b", r"\bномер\b",
    r"\bутеч", r"\bслив", r"\bпробив\b",
    r"\bбаза\s+данных\b",
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def save_search(user_id: int, query: str):
    conn = db()
    conn.execute("INSERT INTO searches(user_id, query) VALUES (?, ?)", (user_id, query))
    conn.commit()
    conn.close()

def history(user_id: int):
    conn = db()
    rows = conn.execute(
        "SELECT query, created_at FROM searches WHERE user_id=? "
        "ORDER BY id DESC LIMIT 10", (user_id,)
    ).fetchall()
    conn.close()
    return rows

def blocked(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in BLOCKED_PATTERNS)

def search_links(query: str):
    q = quote_plus(query.strip())
    return [(name, url.format(q=q)) for name, url in SEARCH_ENGINES]

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Новый поиск", callback_data="search")],
        [InlineKeyboardButton("🕘 История", callback_data="history")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_query"] = False
    await update.message.reply_text(
        "🔎 *Public OSINT Bot*\n\n"
        "Поиск информации только по открытым источникам.\n\n"
        "Выбери действие ниже.",
        parse_mode="Markdown",
        reply_markup=menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        context.user_data["awaiting_query"] = True
        await query.edit_message_text(
            "🔎 Отправь имя, никнейм или домен для поиска.\n\n"
            "Например: `example_user` или `example.com`\n\n"
            "Не отправляй паспортные данные, адреса, телефоны, банковские данные "
            "или запросы на поиск по утечкам.",
            parse_mode="Markdown"
        )

    elif query.data == "history":
        rows = history(query.from_user.id)
        if not rows:
            text = "🕘 История пока пустая."
        else:
            text = "🕘 *Последние запросы:*\n\n" + "\n".join(
                f"• `{q}` — {dt}" for q, dt in rows
            )
        await query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=menu()
        )

    elif query.data == "about":
        await query.edit_message_text(
            "ℹ️ *Что умеет бот*\n\n"
            "• формирует ссылки для поиска по публичному интернету;\n"
            "• сохраняет историю запросов локально;\n"
            "• не использует слитые или закрытые базы;\n"
            "• не предназначен для поиска чувствительных персональных данных.\n\n"
            "Источники поиска: Google, Bing и DuckDuckGo.",
            parse_mode="Markdown", reply_markup=menu()
        )

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_query"):
        await update.message.reply_text("Нажми 🔎 «Новый поиск».", reply_markup=menu())
        return

    q = update.message.text.strip()

    if not q or len(q) > 120:
        await update.message.reply_text("Запрос должен быть от 1 до 120 символов.")
        return

    if blocked(q):
        context.user_data["awaiting_query"] = False
        await update.message.reply_text(
            "🛡️ Такой запрос не поддерживается. "
            "Бот работает только с обычным поиском по открытым источникам "
            "и не помогает получать чувствительные данные или сведения из утечек.",
            reply_markup=menu()
        )
        return

    save_search(update.effective_user.id, q)
    context.user_data["awaiting_query"] = False

    links = search_links(q)
    keyboard = [
        [InlineKeyboardButton(name, url=url)] for name, url in links
    ]
    keyboard.append([InlineKeyboardButton("🔎 Новый поиск", callback_data="search")])

    await update.message.reply_text(
        f"🔎 *Запрос:* `{q}`\n\n"
        "Открой поисковик и проверь публичные результаты самостоятельно.\n\n"
        "⚠️ Бот не получает доступ к закрытым базам и утечкам.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Установи переменную окружения BOT_TOKEN."
        )

    db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    print("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
