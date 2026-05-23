import telebot
import sqlite3
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === НАСТРОЙКИ ===
TOKEN = "8786399001:AAF2GODnsIrCluHiFPH8XYC8uVMuPrDiSss"
ADMIN_ID = 7040677455

bot = telebot.TeleBot(TOKEN)

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            first_date TEXT
        )
    ''')
    
    # Таблица заявок
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

# Инициализация БД при запуске
init_db()

# === ФУНКЦИИ ДЛЯ БД ===
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
    c.execute('SELECT id, name, age, contact, skills, experience, about, date, status FROM applications ORDER BY id DESC')
    apps = c.fetchall()
    conn.close()
    return apps

def get_all_users():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT user_id, username, first_name, first_date FROM users ORDER BY first_date DESC')
    users = c.fetchall()
    conn.close()
    return users

# === ВРЕМЕННЫЕ ДАННЫЕ АНКЕТЫ ===
temp_data = {}
temp_skills = {}

# === КЛАВИАТУРЫ ===
def main_menu():
    markup = InlineKeyboardMarkup()
    btn_apply = InlineKeyboardButton("📝 Подать заявку", callback_data="apply")
    btn_about = InlineKeyboardButton("ℹ️ О проекте", callback_data="about")
    markup.add(btn_apply)
    markup.add(btn_about)
    return markup

def admin_menu():
    markup = InlineKeyboardMarkup()
    btn_stats = InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    btn_apps = InlineKeyboardButton("📋 Заявки", callback_data="admin_apps")
    btn_users = InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
    btn_export = InlineKeyboardButton("📤 Экспорт", callback_data="admin_export")
    markup.add(btn_stats, btn_apps)
    markup.add(btn_users, btn_export)
    return markup

def skills_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔍 Поиск информации", callback_data="skill_search"))
    markup.add(InlineKeyboardButton("✅ Проверка фактов", callback_data="skill_facts"))
    markup.add(InlineKeyboardButton("✍️ Написание текстов", callback_data="skill_write"))
    markup.add(InlineKeyboardButton("🪲 Тестирование", callback_data="skill_test"))
    markup.add(InlineKeyboardButton("🌍 Перевод", callback_data="skill_translate"))
    markup.add(InlineKeyboardButton("Готово ✅", callback_data="skill_done"))
    return markup

def decision_buttons(app_id):
    markup = InlineKeyboardMarkup()
    btn_accept = InlineKeyboardButton("✅ Принять", callback_data=f"accept_{app_id}")
    btn_reject = InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{app_id}")
    markup.add(btn_accept, btn_reject)
    return markup

# === ОБРАБОТЧИКИ КОМАНД ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "—"
    first_name = message.from_user.first_name or "Гость"
    
    add_user(user_id, username, first_name)
    
    bot.send_message(
        message.chat.id,
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        "Я бот для набора в команду <b>SSB2 Archives</b>.\n"
        "Помогай проекту выбираться из бета-версии!",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    bot.send_message(
        message.chat.id,
        "⚙️ <b>Админ-панель</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

@bot.message_handler(commands=['cancel'])
def cancel(message):
    user_id = message.from_user.id
    temp_data.pop(user_id, None)
    temp_skills.pop(user_id, None)
    bot.send_message(
        message.chat.id,
        "❌ Анкета отменена.",
        reply_markup=main_menu()
    )

# === ОБРАБОТЧИКИ CALLBACK ===
@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    bot.edit_message_text(
        "<b>ℹ️ О проекте</b>\n\n"
        "<b>SSB2 Archives</b> — неофициальный сайт-архив по игре Simple Sandbox 2.\n\n"
        "<b>Кого ищем:</b>\n"
        "🔍 Поиск информации\n"
        "✅ Проверка фактов\n"
        "✍️ Написание текстов\n"
        "🪲 Тестирование\n"
        "🌍 Перевод\n\n"
        "<b>Создатель:</b> @HoFiLiOnclkc",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu(),
        parse_mode="HTML"
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
    
    bot.send_message(
        message.chat.id,
        "<b>Что умеешь?</b>\nВыбери навыки (можно несколько):",
        reply_markup=skills_menu(),
        parse_mode="HTML"
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
        "skill_translate": "🌍 Перевод"
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
    
    bot.edit_message_text(
        "<b>Опыт в SSB2</b>\n\nНапиши, как давно играешь и в каких режимах:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
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
    
    # Сохраняем в БД
    app_id = add_application(
        user_id,
        data['name'],
        data['age'],
        data['contact'],
        data['skills'],
        data['experience'],
        data['about']
    )
    
    # Отправляем админу
    admin_msg = (
        f"<b>📩 НОВАЯ ЗАЯВКА</b>\n"
        f"├ <b>Имя:</b> {data['name']}\n"
        f"├ <b>Возраст:</b> {data['age']}\n"
        f"├ <b>Контакт:</b> {data['contact']}\n"
        f"├ <b>Навыки:</b> {data['skills']}\n"
        f"├ <b>Опыт:</b> {data['experience']}\n"
        f"├ <b>О себе:</b> {data['about']}\n"
        f"└ <b>ID заявки:</b> {app_id}"
    )
    
    bot.send_message(
        ADMIN_ID,
        admin_msg,
        reply_markup=decision_buttons(app_id),
        parse_mode="HTML"
    )
    
    # Очищаем временные данные
    temp_data.pop(user_id, None)
    
    bot.send_message(
        message.chat.id,
        "<b>✅ Заявка отправлена!</b>\n\nЯ свяжусь с тобой в ближайшее время.\nСпасибо, что хочешь помочь проекту! 🔥",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# === АДМИН-ПАНЕЛЬ ===
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    total, pending, accepted, rejected = get_applications_stats()
    total_users = get_users_count()
    
    bot.edit_message_text(
        f"<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"📩 Заявок всего: <b>{total}</b>\n"
        f"⏳ На рассмотрении: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_apps")
def admin_apps(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    apps = get_all_applications()
    
    if not apps:
        return bot.edit_message_text(
            "Заявок пока нет.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_menu()
        )
    
    status_emoji = {
        'pending': '⏳',
        'accepted': '✅',
        'rejected': '❌'
    }
    
    text = "<b>📋 Последние заявки</b>\n\n"
    for app in apps[:10]:
        emoji = status_emoji.get(app[8], '⏳')
        text += f"{emoji} <b>#{app[0]}</b> | {app[1]} | {app[7]}\n"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users_list(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users_list = get_all_users()
    
    if not users_list:
        return bot.edit_message_text(
            "Пользователей пока нет.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_menu()
        )
    
    text = "<b>👥 Последние пользователи</b>\n\n"
    for user in users_list[:10]:
        text += f"• <b>{user[2]}</b> (@{user[1]}) | {user[3]}\n"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_export")
def admin_export(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    apps = get_all_applications()
    
    if not apps:
        return bot.edit_message_text(
            "Нечего экспортировать.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_menu()
        )
    
    # Создаём CSV
    csv_text = "ID;Имя;Возраст;Контакт;Навыки;Опыт;О себе;Дата;Статус\n"
    for app in apps:
        csv_text += f"{app[0]};{app[1]};{app[2]};{app[3]};{app[4]};{app[5]};{app[6]};{app[7]};{app[8]}\n"
    
    with open("export.csv", "w", encoding="utf-8") as f:
        f.write(csv_text)
    
    with open("export.csv", "rb") as f:
        bot.send_document(
            ADMIN_ID,
            f,
            caption="📤 Экспорт заявок"
        )
    
    bot.answer_callback_query(call.id, "Экспорт отправлен в личку!")

# === ПРИНЯТЬ / ОТКЛОНИТЬ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    action, app_id = call.data.split("_")
    app_id = int(app_id)
    
    if action == "accept":
        update_application_status(app_id, "accepted")
        bot.answer_callback_query(call.id, "✅ Заявка принята")
        new_text = call.message.text + "\n\n<b>✅ ПРИНЯТО</b>"
    else:
        update_application_status(app_id, "rejected")
        bot.answer_callback_query(call.id, "❌ Заявка отклонена")
        new_text = call.message.text + "\n\n<b>❌ ОТКЛОНЕНО</b>"
    
    bot.edit_message_text(
        new_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )

# === ЗАПУСК ===
if __name__ == "__main__":
    print("✅ Бот запущен!")
    bot.infinity_polling()