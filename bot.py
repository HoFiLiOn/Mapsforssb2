import telebot
import sqlite3
import requests
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === НАСТРОЙКИ ===
TOKEN = "8786399001:AAF2GODnsIrCluHiFPH8XYC8uVMuPrDiSss"
ADMIN_ID = 7040677455
API_URL = f"https://api.telegram.org/bot{TOKEN}"

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
            first_date TEXT
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
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# === ФУНКЦИИ БД ===
def add_user(user_id, username, first_name):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(
        'INSERT OR IGNORE INTO users (user_id, username, first_name, first_date) VALUES (?, ?, ?, ?)',
        (user_id, username, first_name, datetime.now().strftime("%d.%m.%Y %H:%M"))
    )
    conn.commit()
    conn.close()

def add_application(user_id, name, age, contact, skills, experience, about):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO applications (user_id, name, age, contact, skills, experience, about, date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, name, age, contact, skills, experience, about, datetime.now().strftime("%d.%m.%Y %H:%M"), 'pending')
    )
    app_id = c.lastrowid
    conn.commit()
    conn.close()
    return app_id

def update_application_status(app_id, status):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE applications SET status = ? WHERE id = ?', (status, app_id))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    count = c.fetchone()[0]
    conn.close()
    return count

def get_applications_stats():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM applications')
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status = 'accepted'")
    accepted = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status = 'rejected'")
    rejected = c.fetchone()[0]
    conn.close()
    return total, pending, accepted, rejected

def get_all_applications():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT id, user_id, name, age, contact, skills, experience, about, date, status FROM applications ORDER BY id DESC')
    apps = c.fetchall()
    conn.close()
    return apps

def get_user_applications(user_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT id, name, skills, date, status FROM applications WHERE user_id = ? ORDER BY id DESC', (user_id,))
    apps = c.fetchall()
    conn.close()
    return apps

def get_application_by_id(app_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT id, user_id, name, age, contact, skills, experience, about, date, status FROM applications WHERE id = ?', (app_id,))
    app = c.fetchone()
    conn.close()
    return app

def get_all_users():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT user_id, username, first_name, first_date FROM users ORDER BY first_date DESC')
    users = c.fetchall()
    conn.close()
    return users

# === ВРЕМЕННЫЕ ДАННЫЕ ===
temp_data = {}
temp_skills = {}

# === ОТПРАВКА С ЦВЕТНЫМИ КНОПКАМИ ===
def send_colored_message(chat_id, text, keyboard=None, parse_mode="HTML"):
    """Отправка сообщения с цветными кнопками через API"""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    response = requests.post(f"{API_URL}/sendMessage", json=payload)
    return response.json()

def edit_colored_message(chat_id, message_id, text, keyboard=None, parse_mode="HTML"):
    """Редактирование сообщения с цветными кнопками через API"""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    response = requests.post(f"{API_URL}/editMessageText", json=payload)
    return response.json()

# === КЛАВИАТУРЫ С ЦВЕТНЫМИ КНОПКАМИ ===
def main_menu():
    """Главное меню"""
    return {
        "inline_keyboard": [
            [{"text": "📝 Подать заявку", "callback_data": "apply", "style": "primary"}],
            [{"text": "📋 Мои заявки", "callback_data": "my_apps"}],
            [{"text": "ℹ️ О проекте", "callback_data": "about"}]
        ]
    }

def admin_menu():
    """Админ-панель"""
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Статистика", "callback_data": "admin_stats", "style": "primary"},
                {"text": "📋 Все заявки", "callback_data": "admin_apps"}
            ],
            [
                {"text": "👥 Пользователи", "callback_data": "admin_users"},
                {"text": "🔍 Поиск заявки", "callback_data": "admin_search"}
            ],
            [
                {"text": "📤 Экспорт CSV", "callback_data": "admin_export", "style": "success"},
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
            [{"text": "✅ Готово", "callback_data": "skill_done", "style": "success"}]
        ]
    }

def decision_buttons(app_id):
    """Кнопки принять/отклонить"""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Принять", "callback_data": f"accept_{app_id}", "style": "success"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{app_id}", "style": "danger"}
            ],
            [{"text": "📋 Подробнее", "callback_data": f"detail_{app_id}", "style": "primary"}]
        ]
    }

def back_button(data="admin_back"):
    """Кнопка назад (прозрачная)"""
    return {
        "inline_keyboard": [
            [{"text": "⬅️ Назад", "callback_data": data}]
        ]
    }

# === ОБРАБОТЧИКИ КОМАНД ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "—"
    first_name = message.from_user.first_name or "Гость"
    
    add_user(user_id, username, first_name)
    
    send_colored_message(
        message.chat.id,
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        "Я бот для набора в команду <b>SSB2 Archives</b>.\n"
        "Помогай проекту выбираться из бета-версии!",
        main_menu()
    )

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    total, pending, accepted, rejected = get_applications_stats()
    total_users = get_users_count()
    
    send_colored_message(
        message.chat.id,
        f"⚙️ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"📩 Заявок: <b>{total}</b> | ⏳{pending} | ✅{accepted} | ❌{rejected}",
        admin_menu()
    )

@bot.message_handler(commands=['cancel'])
def cancel(message):
    user_id = message.from_user.id
    temp_data.pop(user_id, None)
    temp_skills.pop(user_id, None)
    send_colored_message(
        message.chat.id,
        "❌ Анкета отменена.",
        main_menu()
    )

# === CALLBACK-ОБРАБОТЧИКИ ===
@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    edit_colored_message(
        call.message.chat.id,
        call.message.message_id,
        "<b>ℹ️ О проекте</b>\n\n"
        "<b>SSB2 Archives</b> — неофициальный сайт-архив по игре Simple Sandbox 2.\n\n"
        "<b>Кого ищем:</b>\n"
        "🔍 Поиск информации\n✅ Проверка фактов\n✍️ Написание текстов\n"
        "🪲 Тестирование\n🌍 Перевод\n🎨 Дизайн\n\n"
        "<b>Создатель:</b> @HoFiLiOnclkc",
        main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "apply")
def apply_start(call):
    user_id = call.from_user.id
    temp_data[user_id] = {}
    temp_skills[user_id] = []
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    msg = bot.send_message(
        call.message.chat.id,
        "<b>📝 Заявка в команду</b>\n\nКак тебя зовут (ник или имя)?",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, get_name)

@bot.callback_query_handler(func=lambda call: call.data == "my_apps")
def my_applications(call):
    user_id = call.from_user.id
    apps = get_user_applications(user_id)
    
    if not apps:
        return edit_colored_message(
            call.message.chat.id,
            call.message.message_id,
            "<b>📋 Мои заявки</b>\n\nУ тебя пока нет заявок.",
            main_menu()
        )
    
    status_emoji = {'pending': '⏳', 'accepted': '✅', 'rejected': '❌'}
    text = "<b>📋 Мои заявки</b>\n\n"
    
    for app in apps:
        emoji = status_emoji.get(app[4], '⏳')
        text += f"{emoji} <b>#{app[0]}</b> — {app[1]} ({app[2]}) — {app[3]}\n"
    
    edit_colored_message(
        call.message.chat.id,
        call.message.message_id,
        text,
        main_menu()
    )

# === ШАГИ АНКЕТЫ ===
def get_name(message):
    user_id = message.from_user.id
    temp_data[user_id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "Сколько тебе лет?")
    bot.register_next_step_handler(msg, get_age)

def get_age(message):
    user_id = message.from_user.id
    temp_data[user_id]['age'] = message.text
    msg = bot.send_message(message.chat.id, "Твой Telegram для связи (или Discord)?")
    bot.register_next_step_handler(msg, get_contact)

def get_contact(message):
    user_id = message.from_user.id
    temp_data[user_id]['contact'] = message.text
    send_colored_message(
        message.chat.id,
        "<b>Что умеешь?</b>\nВыбери навыки (можно несколько):",
        skills_menu()
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
    
    edit_colored_message(
        call.message.chat.id,
        call.message.message_id,
        "<b>Опыт в SSB2</b>\n\nНапиши, как давно играешь и в каких режимах:"
    )
    
    bot.register_next_step_handler(call.message, get_experience)

def get_experience(message):
    user_id = message.from_user.id
    temp_data[user_id]['experience'] = message.text
    msg = bot.send_message(
        message.chat.id,
        "<b>Последний шаг!</b>\n\nРасскажи о себе: почему хочешь помогать, какие идеи есть?",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, get_about)

def get_about(message):
    user_id = message.from_user.id
    temp_data[user_id]['about'] = message.text
    data = temp_data[user_id]
    
    app_id = add_application(
        user_id, data['name'], data['age'], data['contact'],
        data['skills'], data['experience'], data['about']
    )
    
    admin_msg = (
        f"<b>📩 НОВАЯ ЗАЯВКА #{app_id}</b>\n"
        f"├ <b>Имя:</b> {data['name']}\n"
        f"├ <b>Возраст:</b> {data['age']}\n"
        f"├ <b>Контакт:</b> {data['contact']}\n"
        f"├ <b>Навыки:</b> {data['skills']}\n"
        f"├ <b>Опыт:</b> {data['experience']}\n"
        f"└ <b>О себе:</b> {data['about']}"
    )
    
    send_colored_message(ADMIN_ID, admin_msg, decision_buttons(app_id))
    
    temp_data.pop(user_id, None)
    
    send_colored_message(
        message.chat.id,
        "<b>✅ Заявка отправлена!</b>\n\nЯ свяжусь с тобой в ближайшее время.\nСпасибо, что хочешь помочь проекту! 🔥",
        main_menu()
    )

# === АДМИН-ПАНЕЛЬ ===
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats" or call.data == "admin_refresh")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    total, pending, accepted, rejected = get_applications_stats()
    total_users = get_users_count()
    
    edit_colored_message(
        call.message.chat.id,
        call.message.message_id,
        f"<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"📩 Заявок всего: <b>{total}</b>\n"
        f"⏳ На рассмотрении: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>",
        admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_apps")
def admin_apps_list(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    apps = get_all_applications()
    
    if not apps:
        return edit_colored_message(
            call.message.chat.id, call.message.message_id,
            "Заявок пока нет.", admin_menu()
        )
    
    status_emoji = {'pending': '⏳', 'accepted': '✅', 'rejected': '❌'}
    text = "<b>📋 Все заявки</b>\n\n"
    
    for app in apps[:15]:
        emoji = status_emoji.get(app[9], '⏳')
        text += f"{emoji} <b>#{app[0]}</b> {app[2]} | {app[8]}\n"
    
    keyboard = admin_menu()
    keyboard["inline_keyboard"].insert(0, [
        {"text": "⏳ В ожидании", "callback_data": "admin_filter_pending"},
        {"text": "✅ Принятые", "callback_data": "admin_filter_accepted"},
        {"text": "❌ Отклонённые", "callback_data": "admin_filter_rejected"}
    ])
    
    edit_colored_message(
        call.message.chat.id, call.message.message_id,
        text, keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users_list(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users = get_all_users()
    
    if not users:
        return edit_colored_message(
            call.message.chat.id, call.message.message_id,
            "Пользователей пока нет.", admin_menu()
        )
    
    text = "<b>👥 Пользователи</b>\n\n"
    for user in users[:20]:
        text += f"• <b>{user[2]}</b> (@{user[1]}) — {user[3]}\n"
    
    edit_colored_message(
        call.message.chat.id, call.message.message_id,
        text, admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_export")
def admin_export(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    apps = get_all_applications()
    
    if not apps:
        return bot.answer_callback_query(call.id, "Нечего экспортировать")
    
    csv_text = "ID;UserID;Имя;Возраст;Контакт;Навыки;Опыт;О себе;Дата;Статус\n"
    for app in apps:
        csv_text += f"{app[0]};{app[1]};{app[2]};{app[3]};{app[4]};{app[5]};{app[6]};{app[7]};{app[8]};{app[9]}\n"
    
    with open("export.csv", "w", encoding="utf-8") as f:
        f.write(csv_text)
    
    with open("export.csv", "rb") as f:
        bot.send_document(ADMIN_ID, f, caption="📤 Экспорт заявок")
    
    bot.answer_callback_query(call.id, "✅ Экспорт отправлен в личку!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_filter_"))
def admin_filter(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    filter_type = call.data.replace("admin_filter_", "")
    apps = get_all_applications()
    
    filtered = [app for app in apps if app[9] == filter_type]
    
    if not filtered:
        return bot.answer_callback_query(call.id, f"Нет заявок со статусом «{filter_type}»")
    
    text = f"<b>📋 Заявки: {filter_type}</b>\n\n"
    for app in filtered[:15]:
        text += f"<b>#{app[0]}</b> {app[2]} | {app[8]}\n"
    
    edit_colored_message(
        call.message.chat.id, call.message.message_id,
        text, admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("detail_"))
def app_detail(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    app_id = int(call.data.replace("detail_", ""))
    app = get_application_by_id(app_id)
    
    if not app:
        return bot.answer_callback_query(call.id, "Заявка не найдена")
    
    text = (
        f"<b>📩 Заявка #{app[0]}</b>\n\n"
        f"👤 <b>Имя:</b> {app[2]}\n"
        f"🎂 <b>Возраст:</b> {app[3]}\n"
        f"📞 <b>Контакт:</b> {app[4]}\n"
        f"🛠 <b>Навыки:</b> {app[5]}\n"
        f"🎮 <b>Опыт:</b> {app[6]}\n"
        f"💬 <b>О себе:</b> {app[7]}\n"
        f"📅 <b>Дата:</b> {app[8]}\n"
        f"📊 <b>Статус:</b> {app[9]}"
    )
    
    edit_colored_message(
        call.message.chat.id, call.message.message_id,
        text, decision_buttons(app_id)
    )

# === ПРИНЯТЬ/ОТКЛОНИТЬ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    action, app_id = call.data.split("_")
    app_id = int(app_id)
    
    app = get_application_by_id(app_id)
    if not app:
        return bot.answer_callback_query(call.id, "Заявка не найдена")
    
    if action == "accept":
        update_application_status(app_id, "accepted")
        status_text = "✅ ПРИНЯТО"
        
        # Уведомляем пользователя
        try:
            send_colored_message(
                app[1],
                f"🎉 <b>Твоя заявка #{app_id} принята!</b>\n\n"
                "Скоро с тобой свяжется создатель проекта.\n"
                "Добро пожаловать в команду SSB2 Archives! 🔥",
                main_menu()
            )
        except:
            pass
    else:
        update_application_status(app_id, "rejected")
        status_text = "❌ ОТКЛОНЕНО"
        
        # Уведомляем пользователя
        try:
            send_colored_message(
                app[1],
                f"<b>Заявка #{app_id}</b>\n\n"
                "К сожалению, твоя заявка не была принята.\n"
                "Не расстраивайся, ты можешь подать новую заявку позже! 💪",
                main_menu()
            )
        except:
            pass
    
    new_text = call.message.text + f"\n\n<b>{status_text}</b>"
    
    edit_colored_message(
        call.message.chat.id,
        call.message.message_id,
        new_text
    )
    
    bot.answer_callback_query(call.id, status_text)

@bot.callback_query_handler(func=lambda call: call.data == "admin_search")
def admin_search_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    msg = bot.send_message(call.message.chat.id, "Введи ID заявки для поиска:")
    bot.register_next_step_handler(msg, admin_search_result)

def admin_search_result(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        app_id = int(message.text)
    except:
        return bot.send_message(message.chat.id, "❌ Неверный ID. Введи число.")
    
    app = get_application_by_id(app_id)
    
    if not app:
        return send_colored_message(message.chat.id, "❌ Заявка не найдена.", admin_menu())
    
    text = (
        f"<b>📩 Заявка #{app[0]}</b>\n\n"
        f"👤 <b>Имя:</b> {app[2]}\n"
        f"🎂 <b>Возраст:</b> {app[3]}\n"
        f"📞 <b>Контакт:</b> {app[4]}\n"
        f"🛠 <b>Навыки:</b> {app[5]}\n"
        f"🎮 <b>Опыт:</b> {app[6]}\n"
        f"💬 <b>О себе:</b> {app[7]}\n"
        f"📅 <b>Дата:</b> {app[8]}\n"
        f"📊 <b>Статус:</b> {app[9]}"
    )
    
    send_colored_message(
        message.chat.id,
        text,
        decision_buttons(app_id)
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    edit_colored_message(
        call.message.chat.id,
        call.message.message_id,
        "⚙️ <b>Админ-панель</b>",
        admin_menu()
    )

# === ЗАПУСК ===
if __name__ == "__main__":
    print("✅ Бот запущен с цветными кнопками!")
    print(f"🤖 @{bot.get_me().username}")
    bot.infinity_polling()