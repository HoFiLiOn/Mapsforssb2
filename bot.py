import telebot
import sqlite3
import requests
import logging
import time
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# === НАСТРОЙКИ ===
TOKEN = "8786399001:AAF2GODnsIrCluHiFPH8XYC8uVMuPrDiSss"
ADMIN_ID = 7040677455
API_URL = f"https://api.telegram.org/bot{TOKEN}"
CREATOR_LINK = "https://t.me/HoFiLiOnclkc"

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            first_date TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            age TEXT,
            contact TEXT,
            skills TEXT,
            experience TEXT,
            about TEXT,
            date TEXT,
            status TEXT DEFAULT 'pending',
            admin_comment TEXT DEFAULT ''
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

init_db()

# === ВРЕМЕННЫЕ ДАННЫЕ ===
temp_data = {}
temp_skills = {}
user_states = {}

# === ФУНКЦИИ БД ===
def db_execute(query, params=(), fetch=False):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        result = c.fetchall()
    else:
        result = c.rowcount
    conn.commit()
    conn.close()
    return result

def add_user(user_id, username, first_name):
    db_execute(
        'INSERT OR IGNORE INTO users (user_id, username, first_name, first_date) VALUES (?, ?, ?, ?)',
        (user_id, username, first_name, datetime.now().strftime("%d.%m.%Y %H:%M"))
    )

def add_application(user_id, name, age, contact, skills, experience, about):
    cursor = db_execute(
        'INSERT INTO applications (user_id, name, age, contact, skills, experience, about, date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, name, age, contact, skills, experience, about, datetime.now().strftime("%d.%m.%Y %H:%M"), 'pending')
    )
    return cursor.lastrowid if hasattr(cursor, 'lastrowid') else None

def get_user_apps(user_id):
    return db_execute(
        'SELECT id, name, skills, date, status, admin_comment FROM applications WHERE user_id = ? ORDER BY id DESC',
        (user_id,), True
    )

def has_active_app(user_id):
    result = db_execute(
        "SELECT COUNT(*) FROM applications WHERE user_id = ? AND status IN ('pending', 'accepted')",
        (user_id,), True
    )
    return result[0][0] > 0 if result else False

def get_app_by_id(app_id):
    result = db_execute(
        'SELECT * FROM applications WHERE id = ?',
        (app_id,), True
    )
    return result[0] if result else None

def update_app_status(app_id, status, comment=''):
    db_execute(
        'UPDATE applications SET status = ?, admin_comment = ? WHERE id = ?',
        (status, comment, app_id)
    )

def get_stats():
    users = db_execute('SELECT COUNT(*) FROM users', (), True)[0][0]
    total = db_execute('SELECT COUNT(*) FROM applications', (), True)[0][0]
    pending = db_execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'", (), True)[0][0]
    accepted = db_execute("SELECT COUNT(*) FROM applications WHERE status = 'accepted'", (), True)[0][0]
    rejected = db_execute("SELECT COUNT(*) FROM applications WHERE status = 'rejected'", (), True)[0][0]
    revoked = db_execute("SELECT COUNT(*) FROM applications WHERE status = 'revoked'", (), True)[0][0]
    return users, total, pending, accepted, rejected, revoked

def get_all_apps(status_filter=None):
    if status_filter:
        return db_execute(
            'SELECT id, user_id, name, age, contact, skills, experience, about, date, status, admin_comment FROM applications WHERE status = ? ORDER BY id DESC',
            (status_filter,), True
        )
    return db_execute(
        'SELECT id, user_id, name, age, contact, skills, experience, about, date, status, admin_comment FROM applications ORDER BY id DESC',
        (), True
    )

def get_all_users():
    return db_execute('SELECT * FROM users ORDER BY first_date DESC', (), True)

# === REACTIONS ===
def set_reaction(chat_id, message_id, emoji):
    """Ставит реакцию на сообщение"""
    try:
        requests.post(
            f"{API_URL}/setMessageReaction",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "reaction": [{"type": "emoji", "emoji": emoji}]
            }
        )
    except Exception as e:
        logger.error(f"Ошибка реакции: {e}")

# === КЛАВИАТУРЫ ===
def main_menu(user_id=None):
    """Главное меню с цветными кнопками"""
    keyboard = {
        "inline_keyboard": [
            [{"text": "📝 Подать заявку", "callback_data": "apply", "style": "primary"}],
            [{"text": "📋 Мои заявки", "callback_data": "my_apps"}],
            [{"text": "ℹ️ О проекте", "callback_data": "about"}]
        ]
    ]
    if user_id == ADMIN_ID:
        keyboard["inline_keyboard"].append(
            [{"text": "⚙️ Админ-панель", "callback_data": "admin_panel", "style": "success"}]
        )
    return keyboard

def reply_keyboard():
    """Reply-клавиатура внизу"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📝 Заявка"), KeyboardButton("📋 Мои заявки"))
    markup.add(KeyboardButton("ℹ️ О проекте"))
    return markup

def admin_menu():
    """Админ-панель"""
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Статистика", "callback_data": "admin_stats", "style": "primary"},
                {"text": "📋 Заявки", "callback_data": "admin_apps"}
            ],
            [
                {"text": "👥 Пользователи", "callback_data": "admin_users"},
                {"text": "🔍 Поиск", "callback_data": "admin_search"}
            ],
            [
                {"text": "⏳ Ожидают", "callback_data": "admin_filter_pending"},
                {"text": "✅ Приняты", "callback_data": "admin_filter_accepted"}
            ],
            [
                {"text": "❌ Отклонены", "callback_data": "admin_filter_rejected"},
                {"text": "🔄 Отозваны", "callback_data": "admin_filter_revoked"}
            ],
            [
                {"text": "📤 Экспорт CSV", "callback_data": "admin_export", "style": "success"},
                {"text": "📤 Экспорт TXT", "callback_data": "admin_export_txt"}
            ],
            [
                {"text": "📢 Рассылка", "callback_data": "admin_broadcast", "style": "danger"},
                {"text": "🔄 Обновить", "callback_data": "admin_refresh"}
            ]
        ]
    }

def skills_menu():
    """Меню выбора навыков"""
    return {
        "inline_keyboard": [
            [{"text": "🔍 Поиск информации", "callback_data": "skill_search"}],
            [{"text": "✅ Проверка фактов", "callback_data": "skill_facts"}],
            [{"text": "✍️ Написание текстов", "callback_data": "skill_write"}],
            [{"text": "🪲 Тестирование", "callback_data": "skill_test"}],
            [{"text": "🌍 Перевод", "callback_data": "skill_translate"}],
            [{"text": "🎨 Дизайн", "callback_data": "skill_design"}],
            [{"text": "✅ Готово", "callback_data": "skill_done", "style": "success"}],
            [{"text": "❌ Отменить", "callback_data": "apply_cancel", "style": "danger"}]
        ]
    }

def decision_buttons(app_id):
    """Кнопки для админа"""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Принять", "callback_data": f"accept_{app_id}", "style": "success"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{app_id}", "style": "danger"}
            ],
            [
                {"text": "💬 С комментарием", "callback_data": f"comment_{app_id}", "style": "primary"},
                {"text": "⬅️ Назад", "callback_data": "admin_back"}
            ]
        ]
    }

def my_app_buttons(app_id, status):
    """Кнопки для пользователя"""
    keyboard = {"inline_keyboard": []}
    if status == 'pending':
        keyboard["inline_keyboard"].append(
            [{"text": "🔄 Отозвать заявку", "callback_data": f"revoke_{app_id}", "style": "danger"}]
        )
    elif status == 'accepted':
        keyboard["inline_keyboard"].append(
            [{"text": "💬 Связаться с создателем", "url": CREATOR_LINK}]
        )
    keyboard["inline_keyboard"].append(
        [{"text": "⬅️ Назад", "callback_data": "my_apps"}]
    )
    return keyboard

# === ОТПРАВКА СООБЩЕНИЙ ===
def send_message(chat_id, text, keyboard=None, parse_mode="HTML"):
    """Отправка с цветными кнопками через API"""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        response = requests.post(f"{API_URL}/sendMessage", json=payload).json()
        return response.get('result', {}).get('message_id')
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return None

def edit_message(chat_id, message_id, text, keyboard=None, parse_mode="HTML"):
    """Редактирование сообщения"""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        requests.post(f"{API_URL}/editMessageText", json=payload)
    except Exception as e:
        logger.error(f"Ошибка редактирования: {e}")

# === ОБРАБОТЧИКИ КОМАНД ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "—"
    first_name = message.from_user.first_name or "Гость"
    
    add_user(user_id, username, first_name)
    logger.info(f"Новый пользователь: {first_name} (@{username})")
    
    msg_id = send_message(
        message.chat.id,
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        "Я бот для набора в команду <b>SSB2 Archives</b>.\n"
        "Помогай проекту выбираться из бета-версии!\n\n"
        "Выбери действие:",
        main_menu(user_id)
    )
    
    bot.send_message(
        message.chat.id,
        "Используй кнопки ниже для быстрого доступа:",
        reply_markup=reply_keyboard()
    )

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    show_admin_panel(message.chat.id)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    send_message(
        message.chat.id,
        "<b>📚 Помощь</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/cancel — отменить анкету\n\n"
        "<b>Кнопки:</b>\n"
        "📝 Подать заявку — заполнить анкету\n"
        "📋 Мои заявки — посмотреть статус\n"
        "ℹ️ О проекте — информация\n\n"
        "<b>Создатель:</b> @HoFiLiOnclkc",
        main_menu(message.from_user.id)
    )

# === ОБРАБОТКА REPLY-КЛАВИАТУРЫ ===
@bot.message_handler(func=lambda m: m.text in ["📝 Заявка", "📋 Мои заявки", "ℹ️ О проекте"])
def reply_handler(message):
    user_id = message.from_user.id
    
    if message.text == "📝 Заявка":
        if has_active_app(user_id):
            send_message(
                message.chat.id,
                "⚠️ У тебя уже есть активная заявка.\n"
                "Дождись решения или отмени текущую заявку в разделе «Мои заявки».",
                main_menu(user_id)
            )
        else:
            start_application(message)
    elif message.text == "📋 Мои заявки":
        show_my_apps(message.chat.id, user_id, message.message_id if hasattr(message, 'message_id') else None)
    elif message.text == "ℹ️ О проекте":
        send_message(
            message.chat.id,
            "<b>ℹ️ О проекте</b>\n\n"
            "<b>SSB2 Archives</b> — неофициальный сайт-архив по игре Simple Sandbox 2.\n\n"
            "<b>Кого ищем:</b>\n"
            "🔍 Поиск информации\n✅ Проверка фактов\n✍️ Написание текстов\n"
            "🪲 Тестирование\n🌍 Перевод\n🎨 Дизайн\n\n"
            "<b>Создатель:</b> @HoFiLiOnclkc",
            main_menu(user_id)
        )

# === CALLBACK-ОБРАБОТЧИКИ ===
@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    edit_message(
        call.message.chat.id, call.message.message_id,
        "<b>ℹ️ О проекте</b>\n\n"
        "<b>SSB2 Archives</b> — неофициальный сайт-архив по игре Simple Sandbox 2.\n\n"
        "<b>Кого ищем:</b>\n"
        "🔍 Поиск информации\n✅ Проверка фактов\n✍️ Написание текстов\n"
        "🪲 Тестирование\n🌍 Перевод\n🎨 Дизайн\n\n"
        "<b>Создатель:</b> @HoFiLiOnclkc",
        main_menu(call.from_user.id)
    )

@bot.callback_query_handler(func=lambda call: call.data == "apply")
def apply_start(call):
    user_id = call.from_user.id
    
    if has_active_app(user_id):
        return edit_message(
            call.message.chat.id, call.message.message_id,
            "⚠️ У тебя уже есть активная заявка.\n"
            "Дождись решения или отмени текущую заявку в разделе «Мои заявки».",
            main_menu(user_id)
        )
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    start_application(call.message)

def start_application(message):
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    temp_data[user_id] = {}
    temp_skills[user_id] = []
    user_states[user_id] = 'applying'
    
    msg = bot.send_message(
        message.chat.id if hasattr(message, 'chat') else message.chat.id,
        "<b>📝 Заявка в команду</b>\n\nКак тебя зовут (ник или имя)?",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, get_name)

@bot.callback_query_handler(func=lambda call: call.data == "my_apps")
def my_apps_callback(call):
    show_my_apps(call.message.chat.id, call.from_user.id, call.message.message_id)

def show_my_apps(chat_id, user_id, message_id=None):
    apps = get_user_apps(user_id)
    
    if not apps:
        text = "<b>📋 Мои заявки</b>\n\nУ тебя пока нет заявок."
        keyboard = main_menu(user_id)
    else:
        status_emoji = {'pending': '⏳', 'accepted': '✅', 'rejected': '❌', 'revoked': '🔄'}
        text = "<b>📋 Мои заявки</b>\n\n"
        
        keyboard = {"inline_keyboard": []}
        for app in apps:
            emoji = status_emoji.get(app[4], '⏳')
            text += f"{emoji} <b>#{app[0]}</b> — {app[1]} ({app[2]}) — {app[3]}\n"
            if app[5]:
                text += f"   💬 <i>{app[5]}</i>\n"
            keyboard["inline_keyboard"].append(
                [{"text": f"{emoji} Заявка #{app[0]}", "callback_data": f"view_app_{app[0]}"}]
            )
        
        keyboard["inline_keyboard"].append(
            [{"text": "⬅️ Главное меню", "callback_data": "back_to_main"}]
        )
    
    if message_id:
        edit_message(chat_id, message_id, text, keyboard)
    else:
        send_message(chat_id, text, keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    edit_message(
        call.message.chat.id, call.message.message_id,
        "<b>Главное меню</b>\n\nВыбери действие:",
        main_menu(call.from_user.id)
    )

# === ПРОСМОТР ЗАЯВКИ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("view_app_"))
def view_application(call):
    app_id = int(call.data.replace("view_app_", ""))
    app = get_app_by_id(app_id)
    
    if not app:
        return bot.answer_callback_query(call.id, "Заявка не найдена")
    
    status_emoji = {'pending': '⏳', 'accepted': '✅', 'rejected': '❌', 'revoked': '🔄'}
    emoji = status_emoji.get(app[9], '⏳')
    
    text = (
        f"<b>📩 Заявка #{app[0]}</b>\n\n"
        f"👤 <b>Имя:</b> {app[2]}\n"
        f"🎂 <b>Возраст:</b> {app[3]}\n"
        f"📞 <b>Контакт:</b> {app[4]}\n"
        f"🛠 <b>Навыки:</b> {app[5]}\n"
        f"🎮 <b>Опыт:</b> {app[6]}\n"
        f"💬 <b>О себе:</b> {app[7]}\n"
        f"📅 <b>Дата:</b> {app[8]}\n"
        f"📊 <b>Статус:</b> {emoji} {app[9]}"
    )
    
    if app[10]:
        text += f"\n💬 <b>Комментарий:</b> {app[10]}"
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        text,
        my_app_buttons(app_id, app[9])
    )

# === ОТЗЫВ ЗАЯВКИ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("revoke_"))
def revoke_application(call):
    app_id = int(call.data.replace("revoke_", ""))
    app = get_app_by_id(app_id)
    
    if not app or app[9] != 'pending':
        return bot.answer_callback_query(call.id, "Нельзя отозвать эту заявку")
    
    update_app_status(app_id, 'revoked')
    logger.info(f"Заявка #{app_id} отозвана пользователем {call.from_user.id}")
    
    # Уведомляем админа
    send_message(
        ADMIN_ID,
        f"🔄 <b>Заявка #{app_id} отозвана</b>\n"
        f"👤 {app[2]} (@{call.from_user.username or '—'})"
    )
    
    bot.answer_callback_query(call.id, "✅ Заявка отозвана")
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        call.message.text.replace("⏳", "🔄").replace("pending", "revoked") + "\n\n<b>🔄 ЗАЯВКА ОТОЗВАНА</b>",
        main_menu(call.from_user.id)
    )

# === ШАГИ АНКЕТЫ ===
def get_name(message):
    user_id = message.from_user.id
    temp_data[user_id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "🎂 Сколько тебе лет?")
    bot.register_next_step_handler(msg, get_age)

def get_age(message):
    user_id = message.from_user.id
    temp_data[user_id]['age'] = message.text
    msg = bot.send_message(message.chat.id, "📞 Твой Telegram для связи (или Discord)?")
    bot.register_next_step_handler(msg, get_contact)

def get_contact(message):
    user_id = message.from_user.id
    temp_data[user_id]['contact'] = message.text
    send_message(
        message.chat.id,
        "<b>🛠 Что умеешь?</b>\nВыбери навыки (можно несколько):",
        skills_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "apply_cancel")
def apply_cancel(call):
    user_id = call.from_user.id
    temp_data.pop(user_id, None)
    temp_skills.pop(user_id, None)
    user_states.pop(user_id, None)
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        "❌ Анкета отменена.",
        main_menu(user_id)
    )

# === НАВЫКИ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("skill_") and call.data != "skill_done")
def skill_select(call):
    user_id = call.from_user.id
    
    skill_map = {
        "skill_search": "🔍 Поиск информации",
        "skill_facts": "✅ Проверка фактов",
        "skill_write": "✍️ Написание текстов",
        "skill_test": "🪲 Тестирование",
        "skill_translate": "🌍 Перевод",
        "skill_design": "🎨 Дизайн"
    }
    
    skill = skill_map.get(call.data)
    
    if skill in temp_skills.get(user_id, []):
        temp_skills[user_id].remove(skill)
    else:
        temp_skills[user_id].append(skill)
    
    skills_text = ", ".join(temp_skills[user_id]) if temp_skills[user_id] else "ничего не выбрано"
    bot.answer_callback_query(call.id, f"Выбрано: {skills_text}")

@bot.callback_query_handler(func=lambda call: call.data == "skill_done")
def skill_done(call):
    user_id = call.from_user.id
    temp_data[user_id]['skills'] = ", ".join(temp_skills.get(user_id, [])) or "Не выбрано"
    temp_skills.pop(user_id, None)
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        "<b>🎮 Опыт в SSB2</b>\n\nНапиши, как давно играешь и в каких режимах:"
    )
    bot.register_next_step_handler(call.message, get_experience)

def get_experience(message):
    user_id = message.from_user.id
    temp_data[user_id]['experience'] = message.text
    msg = bot.send_message(
        message.chat.id,
        "<b>💬 О себе</b>\n\nРасскажи: почему хочешь помогать, какие идеи есть?",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, get_about)

def get_about(message):
    user_id = message.from_user.id
    temp_data[user_id]['about'] = message.text
    data = temp_data[user_id]
    
    # Сохраняем через прямой SQL для получения ID
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO applications (user_id, name, age, contact, skills, experience, about, date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, data['name'], data['age'], data['contact'], data['skills'], data['experience'], data['about'], datetime.now().strftime("%d.%m.%Y %H:%M"), 'pending')
    )
    app_id = c.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f"Новая заявка #{app_id} от {data['name']} (ID: {user_id})")
    
    # Отправляем админу
    admin_msg = (
        f"<b>📩 НОВАЯ ЗАЯВКА #{app_id}</b>\n"
        f"├ <b>Имя:</b> {data['name']}\n"
        f"├ <b>Возраст:</b> {data['age']}\n"
        f"├ <b>Контакт:</b> {data['contact']}\n"
        f"├ <b>Навыки:</b> {data['skills']}\n"
        f"├ <b>Опыт:</b> {data['experience']}\n"
        f"├ <b>О себе:</b> {data['about']}\n"
        f"└ <b>Пользователь:</b> @{message.from_user.username or '—'}"
    )
    
    admin_msg_id = send_message(ADMIN_ID, admin_msg, decision_buttons(app_id))
    
    # Ставим реакцию 👍
    if admin_msg_id:
        set_reaction(ADMIN_ID, admin_msg_id, "👍")
    
    temp_data.pop(user_id, None)
    user_states.pop(user_id, None)
    
    send_message(
        message.chat.id,
        "<b>✅ Заявка отправлена!</b>\n\n"
        "Я свяжусь с тобой в ближайшее время.\n"
        "Спасибо, что хочешь помочь проекту! 🔥",
        main_menu(user_id)
    )

# === АДМИН-ПАНЕЛЬ ===
def show_admin_panel(chat_id):
    users, total, pending, accepted, rejected, revoked = get_stats()
    
    send_message(
        chat_id,
        f"⚙️ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"📩 Заявок: <b>{total}</b>\n"
        f"⏳ Ожидают: {pending} | ✅ Приняты: {accepted}\n"
        f"❌ Отклонены: {rejected} | 🔄 Отозваны: {revoked}",
        admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    show_admin_panel(call.message.chat.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ["admin_stats", "admin_refresh"])
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users, total, pending, accepted, rejected, revoked = get_stats()
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        f"<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"📩 Заявок всего: <b>{total}</b>\n"
        f"⏳ На рассмотрении: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>\n"
        f"🔄 Отозвано: <b>{revoked}</b>",
        admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_apps")
def admin_apps_list(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    apps = get_all_apps()
    
    if not apps:
        return edit_message(
            call.message.chat.id, call.message.message_id,
            "Заявок пока нет.", admin_menu()
        )
    
    status_emoji = {'pending': '⏳', 'accepted': '✅', 'rejected': '❌', 'revoked': '🔄'}
    text = "<b>📋 Все заявки</b>\n\n"
    
    for app in apps[:15]:
        emoji = status_emoji.get(app[9], '⏳')
        text += f"{emoji} <b>#{app[0]}</b> {app[2]} | {app[8]}\n"
    
    if len(apps) > 15:
        text += f"\n<i>Показано 15 из {len(apps)}</i>"
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        text, admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users_list(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users = get_all_users()
    
    if not users:
        return edit_message(
            call.message.chat.id, call.message.message_id,
            "Пользователей пока нет.", admin_menu()
        )
    
    text = "<b>👥 Пользователи</b>\n\n"
    for user in users[:20]:
        text += f"• <b>{user[2]}</b> (@{user[1]}) — {user[3]}\n"
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        text, admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_filter_"))
def admin_filter(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    filter_type = call.data.replace("admin_filter_", "")
    apps = get_all_apps(filter_type)
    
    if not apps:
        return bot.answer_callback_query(call.id, f"Нет заявок со статусом «{filter_type}»")
    
    text = f"<b>📋 Заявки: {filter_type}</b>\n\n"
    for app in apps[:15]:
        text += f"<b>#{app[0]}</b> {app[2]} | {app[8]}\n"
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        text, admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_search")
def admin_search_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    msg = bot.send_message(call.message.chat.id, "🔍 Введи ID заявки:")
    bot.register_next_step_handler(msg, admin_search_result)

def admin_search_result(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        app_id = int(message.text)
    except:
        return send_message(message.chat.id, "❌ Неверный ID.")
    
    app = get_app_by_id(app_id)
    
    if not app:
        return send_message(message.chat.id, "❌ Заявка не найдена.", admin_menu())
    
    text = (
        f"<b>📩 Заявка #{app[0]}</b>\n\n"
        f"👤 Имя: {app[2]}\n🎂 Возраст: {app[3]}\n📞 Контакт: {app[4]}\n"
        f"🛠 Навыки: {app[5]}\n🎮 Опыт: {app[6]}\n💬 О себе: {app[7]}\n"
        f"📅 Дата: {app[8]}\n📊 Статус: {app[9]}"
    )
    
    send_message(message.chat.id, text, decision_buttons(app_id))

@bot.callback_query_handler(func=lambda call: call.data == "admin_export")
def admin_export_csv(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    apps = get_all_apps()
    
    if not apps:
        return bot.answer_callback_query(call.id, "Нечего экспортировать")
    
    csv_text = "ID;UserID;Имя;Возраст;Контакт;Навыки;Опыт;О себе;Дата;Статус;Комментарий\n"
    for app in apps:
        csv_text += f"{app[0]};{app[1]};{app[2]};{app[3]};{app[4]};{app[5]};{app[6]};{app[7]};{app[8]};{app[9]};{app[10]}\n"
    
    with open("export.csv", "w", encoding="utf-8") as f:
        f.write(csv_text)
    
    with open("export.csv", "rb") as f:
        bot.send_document(ADMIN_ID, f, caption="📤 Экспорт CSV")
    
    bot.answer_callback_query(call.id, "✅ Экспорт отправлен в личку!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_export_txt")
def admin_export_txt(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    apps = get_all_apps()
    
    if not apps:
        return bot.answer_callback_query(call.id, "Нечего экспортировать")
    
    txt_text = "=== ЭКСПОРТ ЗАЯВОК ===\n\n"
    for app in apps:
        txt_text += (
            f"Заявка #{app[0]}\n"
            f"{'='*30}\n"
            f"Имя: {app[2]}\nВозраст: {app[3]}\nКонтакт: {app[4]}\n"
            f"Навыки: {app[5]}\nОпыт: {app[6]}\nО себе: {app[7]}\n"
            f"Дата: {app[8]}\nСтатус: {app[9]}\n"
        )
        if app[10]:
            txt_text += f"Комментарий: {app[10]}\n"
        txt_text += "\n"
    
    with open("export.txt", "w", encoding="utf-8") as f:
        f.write(txt_text)
    
    with open("export.txt", "rb") as f:
        bot.send_document(ADMIN_ID, f, caption="📤 Экспорт TXT")
    
    bot.answer_callback_query(call.id, "✅ Экспорт отправлен в личку!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "Всем пользователям", "callback_data": "broadcast_all"}],
            [{"text": "Принятым заявкам", "callback_data": "broadcast_accepted"}],
            [{"text": "Ожидающим заявкам", "callback_data": "broadcast_pending"}],
            [{"text": "⬅️ Назад", "callback_data": "admin_back"}]
        ]
    }
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        "<b>📢 Рассылка</b>\n\nВыбери кому отправить:",
        keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("broadcast_"))
def broadcast_target(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    target = call.data.replace("broadcast_", "")
    call.message.chat.id
    user_states[ADMIN_ID] = {'broadcast_target': target}
    
    msg = bot.send_message(call.message.chat.id, "📝 Введи текст рассылки:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    target = user_states.get(ADMIN_ID, {}).get('broadcast_target', 'all')
    text = message.text
    
    sent = 0
    failed = 0
    
    if target == 'all':
        users = db_execute('SELECT user_id FROM users', (), True)
    elif target == 'accepted':
        users = db_execute("SELECT DISTINCT user_id FROM applications WHERE status = 'accepted'", (), True)
    elif target == 'pending':
        users = db_execute("SELECT DISTINCT user_id FROM applications WHERE status = 'pending'", (), True)
    else:
        users = []
    
    for user in users:
        try:
            send_message(user[0], f"📢 <b>Рассылка</b>\n\n{text}")
            sent += 1
            time.sleep(0.5)
        except:
            failed += 1
    
    send_message(
        ADMIN_ID,
        f"✅ Рассылка завершена\n\nОтправлено: {sent}\nОшибок: {failed}",
        admin_menu()
    )

# === ПРИНЯТЬ/ОТКЛОНИТЬ С КОММЕНТАРИЕМ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("comment_"))
def admin_comment_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    app_id = int(call.data.replace("comment_", ""))
    user_states[ADMIN_ID] = {'comment_app_id': app_id}
    
    msg = bot.send_message(call.message.chat.id, "💬 Введи комментарий к заявке:")
    bot.register_next_step_handler(msg, admin_comment_result)

def admin_comment_result(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    app_id = user_states.get(ADMIN_ID, {}).get('comment_app_id')
    if not app_id:
        return
    
    comment = message.text
    app = get_app_by_id(app_id)
    
    if not app:
        return send_message(message.chat.id, "❌ Заявка не найдена")
    
    update_app_status(app_id, app[9], comment)
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Принять", "callback_data": f"accept_{app_id}", "style": "success"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{app_id}", "style": "danger"}
            ]
        ]
    }
    
    send_message(
        message.chat.id,
        f"✅ Комментарий добавлен к заявке #{app_id}\n\n"
        f"Теперь выбери действие:",
        keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    action, app_id = call.data.split("_")
    app_id = int(app_id)
    
    app = get_app_by_id(app_id)
    if not app:
        return bot.answer_callback_query(call.id, "Заявка не найдена")
    
    if action == "accept":
        update_app_status(app_id, "accepted", app[10])
        status_text = "✅ ПРИНЯТО"
        reaction = "🎉"
        
        try:
            keyboard = {
                "inline_keyboard": [
                    [{"text": "💬 Связаться с создателем", "url": CREATOR_LINK, "style": "primary"}]
                ]
            }
            send_message(
                app[1],
                f"🎉 <b>Твоя заявка #{app_id} принята!</b>\n\n"
                "Добро пожаловать в команду SSB2 Archives! 🔥\n"
                "Свяжись с создателем по кнопке ниже:",
                keyboard
            )
        except:
            logger.warning(f"Не удалось уведомить пользователя {app[1]}")
    else:
        update_app_status(app_id, "rejected", app[10])
        status_text = "❌ ОТКЛОНЕНО"
        reaction = "👎"
        
        try:
            text = f"<b>Заявка #{app_id} отклонена</b>\n\n"
            if app[10]:
                text += f"💬 <i>{app[10]}</i>\n\n"
            text += "Ты можешь подать новую заявку позже."
            send_message(app[1], text)
        except:
            logger.warning(f"Не удалось уведомить пользователя {app[1]}")
    
    # Ставим реакцию
    set_reaction(call.message.chat.id, call.message.message_id, reaction)
    
    new_text = call.message.text + f"\n\n<b>{status_text}</b>"
    edit_message(call.message.chat.id, call.message.message_id, new_text)
    bot.answer_callback_query(call.id, status_text)
    
    logger.info(f"Заявка #{app_id} {status_text}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    show_admin_panel(call.message.chat.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)

# === ЗАПУСК ===
if __name__ == "__main__":
    logger.info("✅ Бот запущен!")
    
    # Уведомление админу
    try:
        send_message(ADMIN_ID, "✅ <b>Бот запущен и работает!</b>", admin_menu())
    except:
        logger.warning("Не удалось отправить уведомление админу")
    
    bot.infinity_polling()