import os
import re
import sqlite3
from urllib.parse import quote_plus
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
DB_PATH = os.getenv('DB_PATH', 'bot.db')
PHONE_RE = re.compile(r'^\+?[0-9()\-\s]{7,20}$')
NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ\-']+(?:\s+[A-Za-zА-Яа-яЁёІіЇїЄєҐґ\-']+){1,2}$")
ENGINES = [('Google','https://www.google.com/search?q={q}'),('Bing','https://www.bing.com/search?q={q}'),('DuckDuckGo','https://duckduckgo.com/?q={q}')]
BLOCKED_PATTERNS = [r'\bпаспорт\b',r'\bснилс\b',r'\bинн\b',r'\bбанковск',r'\bкарта\b',r'\bкредит\b',r'\bадрес\b',r'\bпропис',r'\bутеч',r'\bслив',r'\bпробив\b',r'\bбаза\s+данных\b',r'\bдокумент',r'\bпароль\b',r'\bлогин\b']

def db():
    c=sqlite3.connect(DB_PATH); c.execute('CREATE TABLE IF NOT EXISTS searches (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,search_type TEXT NOT NULL,query TEXT NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'); c.commit(); return c

def save_search(uid,t,q):
    c=db(); c.execute('INSERT INTO searches(user_id,search_type,query) VALUES (?,?,?)',(uid,t,q)); c.commit(); c.close()

def get_history(uid):
    c=db(); r=c.execute('SELECT search_type,query,created_at FROM searches WHERE user_id=? ORDER BY id DESC LIMIT 10',(uid,)).fetchall(); c.close(); return r

def blocked(s): return any(re.search(p,s.lower()) for p in BLOCKED_PATTERNS)
def normalize_phone(s):
    d=re.sub(r'\D','',s)
    return '7'+d[1:] if d.startswith('8') and len(d)==11 else d

def phone_queries(s):
    d=normalize_phone(s); out=[d]
    if len(d)==11 and d.startswith('7'): out.append(f'+7 {d[1:4]} {d[4:7]}-{d[7:9]}-{d[9:11]}')
    return list(dict.fromkeys(out))

def menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton('📱 Поиск по номеру',callback_data='phone')],[InlineKeyboardButton('👤 Поиск по ФИО',callback_data='name')],[InlineKeyboardButton('🕘 История',callback_data='history')],[InlineKeyboardButton('ℹ️ О боте',callback_data='about')]])

def url(template,q): return template.format(q=quote_plus(q))

async def start(update,context):
    context.user_data.clear(); await update.message.reply_text('🔎 *PUBLIC OSINT*\n\nПроверка номера телефона или ФИО по открытым веб-источникам.\n\nВыбери тип поиска:',parse_mode='Markdown',reply_markup=menu())

async def buttons(update,context):
    q=update.callback_query; await q.answer()
    if q.data in ('phone','name'):
        context.user_data.update(search_type=q.data,awaiting_query=True)
        text=('📱 *Поиск по номеру*\n\nОтправь номер, например `+7 999 123-45-67`.' if q.data=='phone' else '👤 *Поиск по ФИО*\n\nОтправь имя и фамилию или полное ФИО, например `Иванов Иван Иванович`.')
        await q.edit_message_text(text+'\n\nБудут сформированы ссылки на публичный веб-поиск.',parse_mode='Markdown')
    elif q.data=='history':
        rows=get_history(q.from_user.id); labels={'phone':'📱','name':'👤'}
        text='🕘 *История пока пустая.*' if not rows else '🕘 *Последние запросы:*\n\n'+'\n'.join(f"{labels.get(t,'🔎')} `{v}` — {dt}" for t,v,dt in rows)
        await q.edit_message_text(text,parse_mode='Markdown',reply_markup=menu())
    elif q.data=='about':
        await q.edit_message_text('ℹ️ *PUBLIC OSINT*\n\nБот помогает искать публичные упоминания номера телефона или ФИО.\n\nОн не получает данные из утечек или закрытых баз и не обходит ограничения доступа. Результаты открываются через обычные поисковики.',parse_mode='Markdown',reply_markup=menu())

async def handle_text(update,context):
    if not context.user_data.get('awaiting_query'):
        await update.message.reply_text('Выбери тип поиска:',reply_markup=menu()); return
    value=update.message.text.strip(); t=context.user_data.get('search_type')
    if not value or len(value)>120: await update.message.reply_text('Запрос должен быть от 1 до 120 символов.'); return
    if blocked(value):
        context.user_data.clear(); await update.message.reply_text('🛡️ Этот запрос не поддерживается. Бот не ищет паспортные, банковские, адресные данные, пароли или сведения из утечек.',reply_markup=menu()); return
    if t=='phone' and not PHONE_RE.fullmatch(value): await update.message.reply_text('Похоже, это не обычный номер. Пример: +7 999 123-45-67'); return
    if t=='name' and not NAME_RE.fullmatch(value): await update.message.reply_text('Введи имя + фамилию или полное ФИО.'); return
    save_search(update.effective_user.id,t,value); context.user_data.clear()
    qs=[f'"{x}"' for x in phone_queries(value)] if t=='phone' else [f'"{value}"']
    kb=[]
    for i,qtext in enumerate(qs,1):
        for name,template in ENGINES: kb.append([InlineKeyboardButton(f'{name} — запрос {i}',url=url(template,qtext))])
    kb += [[InlineKeyboardButton('📱 Новый поиск',callback_data='phone')],[InlineKeyboardButton('👤 Поиск по ФИО',callback_data='name')]]
    label='📱 Номер' if t=='phone' else '👤 ФИО'
    await update.message.reply_text(f'{label}: `{value}`\n\nГотово. Ниже — ссылки на публичный поиск. Открывай их и проверяй результаты самостоятельно.\n\n⚠️ Бот не получает закрытые сведения и не использует базы утечек.',parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb))

def main():
    if not BOT_TOKEN: raise RuntimeError('Не найден BOT_TOKEN. Добавь переменную окружения BOT_TOKEN.')
    db(); app=Application.builder().token(BOT_TOKEN).build(); app.add_handler(CommandHandler('start',start)); app.add_handler(CallbackQueryHandler(buttons)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text)); print('Bot started.'); app.run_polling()
if __name__=='__main__': main()
