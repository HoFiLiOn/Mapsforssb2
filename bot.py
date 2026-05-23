import telebot
import sqlite3
import requests
import logging
import time
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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
            agreed INTEGER DEFAULT 0
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
user_msg_ids = {}

# === ФУНКЦИИ БД ===
def db_execute(query, params=(), fetch=False):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        result = c.fetchall()
    else:
        result = c
    conn.commit()
    conn.close()
    return result

def add_user(user_id, username, first_name):
    db_execute(
        'INSERT OR IGNORE INTO users (user_id, username, first_name, first_date) VALUES (?, ?, ?, ?)',
        (user_id, username, first_name, datetime.now().strftime("%d.%m.%Y %H:%M"))
    )

def user_agreed(user_id):
    result = db_execute('SELECT agreed FROM users WHERE user_id = ?', (user_id,), True)
    return result and result[0][0] == 1

def set_agreed(user_id):
    db_execute('UPDATE users SET agreed = 1 WHERE user_id = ?', (user_id,))

def add_application(user_id, name, age, contact, skills, experience, about):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO applications (user_id, name, age, contact, skills, experience, about, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, name, age, contact, skills, experience, about, datetime.now().strftime("%d.%m.%Y %H:%M"))
    )
    app_id = c.lastrowid
    conn.commit()
    conn.close()
    return app_id

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
    result = db_execute('SELECT * FROM applications WHERE id = ?', (app_id,), True)
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

def get_public_stats():
    users = db_execute('SELECT COUNT(*) FROM users', (), True)[0][0]
    total = db_execute('SELECT COUNT(*) FROM applications', (), True)[0][0]
    accepted = db_execute("SELECT COUNT(*) FROM applications WHERE status = 'accepted'", (), True)[0][0]
    return users, total, accepted

def get_all_apps(status_filter=None):
    if status_filter:
        return db_execute(
            'SELECT * FROM applications WHERE status = ? ORDER BY id DESC',
            (status_filter,), True
        )
    return db_execute('SELECT * FROM applications ORDER BY id DESC', (), True)

def get_all_users():
    return db_execute('SELECT * FROM users ORDER BY first_date DESC', (), True)

# === REACTIONS ===
def set_reaction(chat_id, message_id, emoji):
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

# === КЛАВИАТУРЫ (ТОЛЬКО ИНЛАЙН) ===
def agreement_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Принимаю", "callback_data": "agree_yes", "style": "success"},
                {"text": "❌ Отказываюсь", "callback_data": "agree_no", "style": "danger"}
            ]
        ]
    }

def main_menu(user_id=None):
    keyboard = {
        "inline_keyboard": [
            [{"text": "📝 Подать заявку", "callback_data": "apply", "style": "primary"}],
            [{"text": "📋 Мои заявки", "callback_data": "my_apps"}],
            [{"text": "📊 Статистика", "callback_data": "public_stats"}],
            [{"text": "ℹ️ О проекте", "callback_data": "about"}],
            [{"text": "💬 Техподдержка", "callback_data": "support"}]
        ]
    }
    if user_id == ADMIN_ID:
        keyboard["inline_keyboard"].append(
            [{"text": "⚙️ Админ-панель", "callback_data": "admin_panel", "style": "success"}]
        )
    return keyboard

def admin_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Статистика", "callback_data": "admin_stats", "style": "primary"},
                {"text": "📋 Заявки", "callback_data": "admin_apps_page_0"}
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
    return {
        "inline_keyboard": [
            [{"text": "🔍 Поиск информации", "callback_data": "skill_search"}],
            [{"text": "✅ Проверка фактов", "callback_data": "skill_facts"}],
            [{"text": "✍️ Написание текстов", "callback_data": "skill_write"}],
            [{"text": "🪲 Тестирование", "callback_data": "skill_test"}],
            [{"text": "🌍 Перевод текстов", "callback_data": "skill_translate"}],
            [{"text": "🎨 Дизайн (фотографии)", "callback_data": "skill_design"}],
            [{"text": "✅ Готово", "callback_data": "skill_done", "style": "success"}],
            [{"text": "❌ Отменить", "callback_data": "apply_cancel", "style": "danger"}]
        ]
    }

def decision_buttons(app_id):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Принять", "callback_data": f"accept_{app_id}", "style": "success"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{app_id}", "style": "danger"}
            ],
            [
                {"text": "💬 Комментарий", "callback_data": f"comment_{app_id}", "style": "primary"},
                {"text": "⬅️ Назад", "callback_data": "admin_apps_page_0"}
            ]
        ]
    }

def my_app_buttons(app_id, status):
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

def support_menu():
    return {
        "inline_keyboard": [
            [{"text": "❓ Как подать заявку?", "callback_data": "sup_1"}],
            [{"text": "❓ Что такое навыки?", "callback_data": "sup_2"}],
            [{"text": "❓ Как отозвать заявку?", "callback_data": "sup_3"}],
            [{"text": "❓ Кто создатель?", "callback_data": "sup_4"}],
            [{"text": "💬 Написать владельцу", "url": CREATOR_LINK}],
            [{"text": "⬅️ Назад", "callback_data": "back_to_main"}]
        ]
    }

def back_to_support():
    return {
        "inline_keyboard": [
            [{"text": "⬅️ Назад к вопросам", "callback_data": "support"}]
        ]
    }

# === ОТПРАВКА СООБЩЕНИЙ ===
def send_message(chat_id, text, keyboard=None, parse_mode="HTML"):
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
    logger.info(f"Пользователь: {first_name} (@{username})")
    
    if not user_agreed(user_id):
        send_message(
            message.chat.id,
            "📋 <b>Пользовательское соглашение</b>\n\n"
            "Перед использованием бота ознакомься с правилами:\n\n"
            "• Твои данные используются только для рассмотрения заявки\n"
            "• Ты можешь отозвать заявку в любой момент\n"
            "• Не указывай пароли и конфиденциальную информацию\n"
            "• Спам и оскорбительные заявки отклоняются\n\n"
            "<i>Нажимая «Принимаю», ты соглашаешься с условиями.</i>",
            agreement_keyboard()
        )
    else:
        send_message(
            message.chat.id,
            f"👋 <b>Привет, {first_name}!</b>\n\n"
            "Я бот для набора в команду <b>SSB2 Archives</b>.\n"
            "Помогай проекту выбираться из бета-версии!",
            main_menu(user_id)
        )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    if not user_agreed(message.from_user.id):
        return send_message(message.chat.id, "Сначала прими пользовательское соглашение — напиши /start")
    
    send_message(
        message.chat.id,
        "<b>📚 Помощь</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - главное меню\n"
        "/help - помощь\n"
        "/cancel - отменить анкету\n\n"
        "<b>Разделы:</b>\n"
        "📝 Подать заявку - заполнить анкету\n"
        "📋 Мои заявки - посмотреть статус\n"
        "📊 Статистика - сколько уже заявок\n"
        "ℹ️ О проекте - информация\n"
        "💬 Техподдержка - ответы на вопросы\n\n"
        "<b>Создатель:</b> @HoFiLiOnclkc",
        main_menu(message.from_user.id)
    )

@bot.message_handler(commands=['cancel'])
def cancel_cmd(message):
    user_id = message.from_user.id
    temp_data.pop(user_id, None)
    temp_skills.pop(user_id, None)
    user_states.pop(user_id, None)
    user_msg_ids.pop(user_id, None)
    send_message(
        message.chat.id,
        "❌ Анкета отменена.",
        main_menu(user_id)
    )

# === СОГЛАШЕНИЕ ===
@bot.callback_query_handler(func=lambda call: call.data == "agree_yes")
def agree_yes(call):
    set_agreed(call.from_user.id)
    logger.info(f"Пользователь {call.from_user.id} принял соглашение")
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        "✅ <b>Соглашение принято!</b>\n\nДобро пожаловать!",
        main_menu(call.from_user.id)
    )

@bot.callback_query_handler(func=lambda call: call.data == "agree_no")
def agree_no(call):
    edit_message(
        call.message.chat.id, call.message.message_id,
        "❌ Ты отказался от соглашения.\n\n"
        "Бот недоступен. Напиши /start чтобы попробовать снова."
    )

# === ПУБЛИЧНАЯ СТАТИСТИКА ===
@bot.callback_query_handler(func=lambda call: call.data == "public_stats")
def public_stats(call):
    users, total, accepted = get_public_stats()
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        f"<b>📊 Статистика проекта</b>\n\n"
        f"👥 Пользователей бота: <b>{users}</b>\n"
        f"📩 Всего подано заявок: <b>{total}</b>\n"
        f"✅ Принято в команду: <b>{accepted}</b>\n\n"
        f"<i>Хочешь присоединиться? Жми «📝 Подать заявку»!</i>",
        main_menu(call.from_user.id)
    )

# === ТЕХПОДДЕРЖКА ===
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    edit_message(
        call.message.chat.id, call.message.message_id,
        "<b>💬 Техподдержка</b>\n\n"
        "Выбери вопрос или напиши владельцу:",
        support_menu()
    )

support_answers = {
    "sup_1": "<b>❓ Как подать заявку?</b>\n\n"
             "Нажми кнопку «📝 Подать заявку» в главном меню и ответь на вопросы бота.\n\n"
             "Некоторые поля (возраст, контакт, о себе) можно пропустить.",
    "sup_2": "<b>❓ Что такое навыки?</b>\n\n"
             "Навыки - это то, что ты умеешь и чем хочешь помогать проекту.\n\n"
             "Например: поиск информации, тестирование, написание текстов или их перевод, дизайн.",
    "sup_3": "<b>❓ Как отозвать заявку?</b>\n\n"
             "1. Зайди в раздел «📋 Мои заявки»\n"
             "2. Выбери нужную заявку\n"
             "3. Нажми «🔄 Отозвать заявку»\n\n"
             "После отзыва ты сможешь подать новую заявку.",
    "sup_4": "<b>❓ Кто создатель?</b>\n\n"
             "Создатель проекта SSB2 Archives: @HoFiLiOnclkc\n\n"
             "Ты можешь написать ему лично, нажав кнопку «💬 Написать владельцу»."
}

@bot.callback_query_handler(func=lambda call: call.data in support_answers)
def support_answer(call):
    edit_message(
        call.message.chat.id, call.message.message_id,
        support_answers[call.data],
        back_to_support()
    )

# === О ПРОЕКТЕ ===
@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    edit_message(
        call.message.chat.id, call.message.message_id,
        "<b>ℹ️ О проекте</b>\n\n"
        "<b>SSB2 Archives</b> - это неофициальный сайт-архив по игре Simple Sandbox 2.\n\n"
        "<b>Кого ищем:</b>\n"
        "🔍 Людей которые смогут находить информацию\n"
        "✅ Людей для проверки информации\n"
        "✍️ Людей для написание текстов\n"
        "🪲 Людей для тестирований\n"
        "🌍 Людей для перевода\n"
        "🎨 Ну и людей для дизайна фотографий и прочего) \n\n"
        "<b>Создатель:</b> @HoFiLiOnclkc",
        main_menu(call.from_user.id)
    )

# === ЗАЯВКА (НАЧАЛО) ===
@bot.callback_query_handler(func=lambda call: call.data == "apply")
def apply_start(call):
    user_id = call.from_user.id
    
    if not user_agreed(user_id):
        return bot.answer_callback_query(call.id, "Сначала прими соглашение — напиши /start")
    
    if has_active_app(user_id):
        return bot.answer_callback_query(call.id, "У тебя уже есть активная заявка. Проверь раздел «Мои заявки».")
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    temp_data[user_id] = {}
    temp_skills[user_id] = []
    
    msg = bot.send_message(
        call.message.chat.id,
        "<b>📝 Заявка в команду</b>\n\nКак тебя зовут (ник или имя)?",
        parse_mode="HTML"
    )
    user_msg_ids[user_id] = msg.message_id
    bot.register_next_step_handler(msg, get_name)

# === ШАГИ АНКЕТЫ ===
def get_name(message):
    user_id = message.from_user.id
    temp_data[user_id]['name'] = message.text
    
    msg = bot.send_message(
        message.chat.id,
        "🎂 Сколько тебе лет?",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_age")]]
        )
    )
    user_msg_ids[user_id] = msg.message_id
    bot.register_next_step_handler(msg, get_age)

@bot.callback_query_handler(func=lambda call: call.data == "skip_age")
def skip_age(call):
    user_id = call.from_user.id
    temp_data[user_id]['age'] = "Не указано"
    
    try:
        bot.delete_message(call.message.chat.id, user_msg_ids.get(user_id, call.message.message_id))
    except Exception:
        pass
    
    # Очищаем предыдущий handler, чтобы не было двойного срабатывания
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    
    msg = bot.send_message(
        call.message.chat.id,
        "📞 Твой Telegram для связи (или Discord)?",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_contact")]]
        )
    )
    user_msg_ids[user_id] = msg.message_id
    bot.register_next_step_handler(msg, get_contact)

def get_age(message):
    user_id = message.from_user.id
    temp_data[user_id]['age'] = message.text
    
    msg = bot.send_message(
        message.chat.id,
        "📞 Твой Telegram для связи (или Discord)?",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_contact")]]
        )
    )
    user_msg_ids[user_id] = msg.message_id
    bot.register_next_step_handler(msg, get_contact)

@bot.callback_query_handler(func=lambda call: call.data == "skip_contact")
def skip_contact(call):
    user_id = call.from_user.id
    temp_data[user_id]['contact'] = f"@{call.from_user.username}" if call.from_user.username else "Не указано"
    
    try:
        bot.delete_message(call.message.chat.id, user_msg_ids.get(user_id, call.message.message_id))
    except Exception:
        pass
    
    # Очищаем предыдущий handler
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    
    send_message(
        call.message.chat.id,
        "<b>🛠 Что умеешь?</b>\nВыбери навыки (можно несколько):",
        skills_menu()
    )

def get_contact(message):
    user_id = message.from_user.id
    temp_data[user_id]['contact'] = message.text
    
    send_message(
        message.chat.id,
        "<b>🛠 Что умеешь?</b>\nВыбери навыки (можно несколько):",
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
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        "<b>🎮 Опыт в SSB2</b>\n\nНапиши, как давно играешь и в каких типах серверов (рп, дчх и т,д) :"
    )
    bot.register_next_step_handler(call.message, get_experience)

@bot.callback_query_handler(func=lambda call: call.data == "apply_cancel")
def apply_cancel(call):
    user_id = call.from_user.id
    temp_data.pop(user_id, None)
    temp_skills.pop(user_id, None)
    user_msg_ids.pop(user_id, None)
    
    edit_message(
        call.message.chat.id, call.message.message_id,
        "❌ Анкета отменена.",
        main_menu(user_id)
    )

def get_experience(message):
    user_id = message.from_user.id
    temp_data[user_id]['experience'] = message.text
    
    msg = bot.send_message(
        message.chat.id,
        "<b>💬 О себе</b>\n\nРасскажи о себе или нажми пропустить:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_about")]]
        ),
        parse_mode="HTML"
    )
    user_msg_ids[user_id] = msg.message_id
    bot.register_next_step_handler(msg, get_about)

@bot.callback_query_handler(func=lambda call: call.data == "skip_about")
def skip_about(call):
    user_id = call.from_user.id
    temp_data[user_id]['about'] = "Не указано"
    
    try:
        bot.delete_message(call.message.chat.id, user_msg_ids.get(user_id, call.message.message_id))
    except Exception:
        pass
    
    finish_application(call.message, user_id)

def get_about(message):
    user_id = message.from_user.id
    temp_data[user_id]['about'] = message.text
    finish_application(message, user_id)

def finish_application(message, user_id):
    data = temp_data[user_id]
    
    app_id = add_application(
        user_id,
        data['name'],
        data['age'],
        data['contact'],
        data['skills'],
        data['experience'],
        data['about']
    )
    
    logger.info(f"Новая заявка #{app_id} от {data['name']} (ID: {user_id})")
    
    admin_msg = (
        f"<b>📩 НОВАЯ ЗАЯВКА #{app_id}</b>\n"
        f"├ <b>Имя:</b> {data['name']}\n"
        f"├ <b>Возраст:</b> {data['age']}\n"
        f"├ <b>Контакт:</b> {data['contact']}\n"
        f"├ <b>Навыки:</b> {data['skills']}\n"
        f"├ <b>Опыт в SSB2:</b> {data['experience']}\n"
        f"├ <b>О себе:</b> {data['about']}\n"
        f"└ <b>Пользователь:</b> @{message.from_user.username or '—'}"
    )
    
    admin_msg_id = send_message(ADMIN_ID, admin_msg, decision_buttons(app_id))
    
    if admin_msg_id:
        set_reaction(ADMIN_ID, admin_msg_id, "👍")
    
    temp_data.pop(user_id, None)
    user_msg_ids.pop(user_id, None)
    
    send_message(
        message.chat.id,
        "<b>✅ Заявка отправлена!</b>\n\n"
        "Я свяжусь с тобой в ближайшее время.\n"
        "Спасибо, что хочешь помочь проекту! 🔥",
        main_menu(user_id)
    )

# === МОИ ЗАЯВКИ ===
@bot.callback_query_handler(func=lambda call: call.data == "my_apps")
def my_apps_callback(call):
    user_id = call.from_user.id
    apps = get_user_apps(user_id)
    
    if not apps:
        return edit_message(
            call.message.chat.id,
            call.message.message_id,
            "<b>📋 Мои заявки</b>\n\nУ тебя пока нет заявок.",
            main_menu(user_id)
        )
    
    status_emoji = {
        'pending': '⏳',
        'accepted': '✅',
        'rejected': '❌',
        'revoked': '🔄'
    }
    
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
    
    edit_message(call.message.chat.id, call.message.message_id, text, keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        "<b>Главное меню</b>\n\nВыбери действие:",
        main_menu(call.from_user.id)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_app_"))
def view_application(call):
    app_id = int(call.data.replace("view_app_", ""))
    app = get_app_by_id(app_id)
    
    if not app:
        return bot.answer_callback_query(call.id, "Заявка не найдена")
    
    status_emoji = {
        'pending': '⏳',
        'accepted': '✅',
        'rejected': '❌',
        'revoked': '🔄'
    }
    emoji = status_emoji.get(app[9], '⏳')
    
    text = (
        f"<b>📩 Заявка #{app[0]}</b>\n\n"
        f"👤 <b>Имя:</b> {app[2]}\n"
        f"🎂 <b>Возраст:</b> {app[3]}\n"
        f"📞 <b>Контакт:</b> {app[4]}\n"
        f"🛠 <b>Навыки:</b> {app[5]}\n"
        f"🎮 <b>Опыт в SSB2:</b> {app[6]}\n"
        f"💬 <b>О себе:</b> {app[7]}\n"
        f"📅 <b>Дата:</b> {app[8]}\n"
        f"📊 <b>Статус:</b> {emoji} {app[9]}"
    )
    
    if app[10]:
        text += f"\n💬 <b>Комментарий:</b> {app[10]}"
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        text,
        my_app_buttons(app_id, app[9])
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("revoke_"))
def revoke_application(call):
    app_id = int(call.data.replace("revoke_", ""))
    app = get_app_by_id(app_id)
    
    if not app or app[9] != 'pending':
        return bot.answer_callback_query(call.id, "Нельзя отозвать эту заявку")
    
    update_app_status(app_id, 'revoked')
    logger.info(f"Заявка #{app_id} отозвана пользователем {call.from_user.id}")
    
    send_message(
        ADMIN_ID,
        f"🔄 <b>Заявка #{app_id} отозвана</b>\n"
        f"👤 {app[2]} (@{call.from_user.username or '—'})"
    )
    
    bot.answer_callback_query(call.id, "✅ Заявка отозвана")
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        call.message.text + "\n\n<b>🔄 ЗАЯВКА ОТОЗВАНА</b>",
        main_menu(call.from_user.id)
    )

# === АДМИН-ПАНЕЛЬ ===
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users, total, pending, accepted, rejected, revoked = get_stats()
    
    send_message(
        call.message.chat.id,
        f"⚙️ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"📩 Заявок всего: <b>{total}</b>\n"
        f"⏳ На рассмотрении: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>\n"
        f"🔄 Отозвано: <b>{revoked}</b>",
        admin_menu()
    )
    
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ["admin_stats", "admin_refresh"])
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users, total, pending, accepted, rejected, revoked = get_stats()
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        f"<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"📩 Заявок всего: <b>{total}</b>\n"
        f"⏳ На рассмотрении: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>\n"
        f"🔄 Отозвано: <b>{revoked}</b>",
        admin_menu()
    )

# === ЗАЯВКИ С ПАГИНАЦИЕЙ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_apps_page_"))
def admin_apps_page(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    page = int(call.data.replace("admin_apps_page_", ""))
    apps = get_all_apps()
    
    if not apps:
        return edit_message(
            call.message.chat.id,
            call.message.message_id,
            "Заявок пока нет.",
            admin_menu()
        )
    
    per_page = 5
    total_pages = max(1, (len(apps) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    
    start = page * per_page
    end = start + per_page
    page_apps = apps[start:end]
    
    status_emoji = {
        'pending': '⏳',
        'accepted': '✅',
        'rejected': '❌',
        'revoked': '🔄'
    }
    
    text = f"<b>📋 Заявки (страница {page+1}/{total_pages})</b>\n\n"
    keyboard = {"inline_keyboard": []}
    
    for app in page_apps:
        emoji = status_emoji.get(app[9], '⏳')
        text += f"{emoji} <b>#{app[0]}</b> — {app[2]} | {app[8]}\n"
        keyboard["inline_keyboard"].append(
            [{"text": f"{emoji} Заявка #{app[0]} — {app[2]}", "callback_data": f"admin_view_{app[0]}"}]
        )
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            {"text": "⬅️ Назад", "callback_data": f"admin_apps_page_{page-1}"}
        )
    if page < total_pages - 1:
        nav_buttons.append(
            {"text": "Вперёд ➡️", "callback_data": f"admin_apps_page_{page+1}"}
        )
    
    if nav_buttons:
        keyboard["inline_keyboard"].append(nav_buttons)
    
    keyboard["inline_keyboard"].append(
        [{"text": "⬅️ В админ-панель", "callback_data": "admin_back"}]
    )
    
    if len(apps) > 5:
        text += f"\n<i>Показано {start+1}-{min(end, len(apps))} из {len(apps)}</i>"
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        text,
        keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_view_"))
def admin_view_app(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    app_id = int(call.data.replace("admin_view_", ""))
    app = get_app_by_id(app_id)
    
    if not app:
        return bot.answer_callback_query(call.id, "Заявка не найдена")
    
    status_emoji = {
        'pending': '⏳',
        'accepted': '✅',
        'rejected': '❌',
        'revoked': '🔄'
    }
    emoji = status_emoji.get(app[9], '⏳')
    
    text = (
        f"<b>📩 Заявка #{app[0]}</b>\n\n"
        f"👤 <b>Имя:</b> {app[2]}\n"
        f"🎂 <b>Возраст:</b> {app[3]}\n"
        f"📞 <b>Контакт:</b> {app[4]}\n"
        f"🛠 <b>Навыки:</b> {app[5]}\n"
        f"🎮 <b>Опыт в SSB2:</b> {app[6]}\n"
        f"💬 <b>О себе:</b> {app[7]}\n"
        f"📅 <b>Дата:</b> {app[8]}\n"
        f"📊 <b>Статус:</b> {emoji} {app[9]}"
    )
    
    if app[10]:
        text += f"\n💬 <b>Комментарий:</b> {app[10]}"
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        text,
        decision_buttons(app_id)
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
        text += f"<b>#{app[0]}</b> — {app[2]} | {app[8]}\n"
    
    if len(apps) > 15:
        text += f"\n<i>Показано 15 из {len(apps)}</i>"
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        text,
        admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users_list(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users = get_all_users()
    
    if not users:
        return edit_message(
            call.message.chat.id,
            call.message.message_id,
            "Пользователей пока нет.",
            admin_menu()
        )
    
    text = "<b>👥 Пользователи</b>\n\n"
    for user in users[:20]:
        agreed_icon = "✅" if user[4] else "❌"
        text += f"{agreed_icon} <b>{user[2]}</b> (@{user[1]}) — {user[3]}\n"
    
    if len(users) > 20:
        text += f"\n<i>Показано 20 из {len(users)}</i>"
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        text,
        admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_search")
def admin_search_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    msg = bot.send_message(call.message.chat.id, "🔍 Введи ID заявки для поиска:")
    bot.register_next_step_handler(msg, admin_search_result)

def admin_search_result(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        app_id = int(message.text)
    except ValueError:
        return send_message(message.chat.id, "❌ Неверный ID. Введи число.")
    
    app = get_app_by_id(app_id)
    
    if not app:
        return send_message(
            message.chat.id,
            "❌ Заявка не найдена.",
            admin_menu()
        )
    
    status_emoji = {
        'pending': '⏳',
        'accepted': '✅',
        'rejected': '❌',
        'revoked': '🔄'
    }
    emoji = status_emoji.get(app[9], '⏳')
    
    text = (
        f"<b>📩 Заявка #{app[0]}</b>\n\n"
        f"👤 <b>Имя:</b> {app[2]}\n"
        f"🎂 <b>Возраст:</b> {app[3]}\n"
        f"📞 <b>Контакт:</b> {app[4]}\n"
        f"🛠 <b>Навыки:</b> {app[5]}\n"
        f"🎮 <b>Опыт в SSB2:</b> {app[6]}\n"
        f"💬 <b>О себе:</b> {app[7]}\n"
        f"📅 <b>Дата:</b> {app[8]}\n"
        f"📊 <b>Статус:</b> {emoji} {app[9]}"
    )
    
    if app[10]:
        text += f"\n💬 <b>Комментарий:</b> {app[10]}"
    
    send_message(
        message.chat.id,
        text,
        decision_buttons(app_id)
    )

# === ЭКСПОРТ ===
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
        bot.send_document(
            ADMIN_ID,
            f,
            caption="📤 Экспорт заявок (CSV)"
        )
    
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
        txt_text += f"Заявка #{app[0]}\n"
        txt_text += f"{'='*30}\n"
        txt_text += f"Имя: {app[2]}\n"
        txt_text += f"Возраст: {app[3]}\n"
        txt_text += f"Контакт: {app[4]}\n"
        txt_text += f"Навыки: {app[5]}\n"
        txt_text += f"Опыт: {app[6]}\n"
        txt_text += f"О себе: {app[7]}\n"
        txt_text += f"Дата: {app[8]}\n"
        txt_text += f"Статус: {app[9]}\n"
        if app[10]:
            txt_text += f"Комментарий: {app[10]}\n"
        txt_text += "\n"
    
    with open("export.txt", "w", encoding="utf-8") as f:
        f.write(txt_text)
    
    with open("export.txt", "rb") as f:
        bot.send_document(
            ADMIN_ID,
            f,
            caption="📤 Экспорт заявок (TXT)"
        )
    
    bot.answer_callback_query(call.id, "✅ Экспорт отправлен в личку!")

# === РАССЫЛКА ===
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
        call.message.chat.id,
        call.message.message_id,
        "<b>📢 Рассылка</b>\n\nВыбери, кому отправить сообщение:",
        keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("broadcast_"))
def broadcast_target(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    target = call.data.replace("broadcast_", "")
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
        users = db_execute('SELECT user_id FROM users WHERE agreed = 1', (), True)
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
        except Exception:
            failed += 1
    
    send_message(
        ADMIN_ID,
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"📤 Отправлено: <b>{sent}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>",
        admin_menu()
    )

# === ПРИНЯТЬ/ОТКЛОНИТЬ С КОММЕНТАРИЕМ ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("comment_"))
def admin_comment_prompt(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    app_id = int(call.data.replace("comment_", ""))
    user_states[ADMIN_ID] = {'comment_app_id': app_id}
    
    msg = bot.send_message(
        call.message.chat.id,
        "💬 Введи комментарий к заявке:"
    )
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
    
    send_message(
        message.chat.id,
        f"✅ Комментарий добавлен к заявке #{app_id}\n\n"
        f"Теперь выбери действие:",
        decision_buttons(app_id)
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
        except Exception:
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
        except Exception:
            logger.warning(f"Не удалось уведомить пользователя {app[1]}")
    
    set_reaction(call.message.chat.id, call.message.message_id, reaction)
    
    new_text = call.message.text + f"\n\n<b>{status_text}</b>"
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        new_text
    )
    
    bot.answer_callback_query(call.id, status_text)
    logger.info(f"Заявка #{app_id} {status_text}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")
    
    users, total, pending, accepted, rejected, revoked = get_stats()
    
    edit_message(
        call.message.chat.id,
        call.message.message_id,
        f"⚙️ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"📩 Заявок: <b>{total}</b>\n"
        f"⏳{pending} | ✅{accepted} | ❌{rejected} | 🔄{revoked}",
        admin_menu()
    )

# === ЗАПУСК ===
if __name__ == "__main__":
    logger.info("✅ Бот запущен!")
    
    try:
        send_message(
            ADMIN_ID,
            "✅ <b>Бот запущен и работает!</b>",
            admin_menu()
        )
    except Exception:
        logger.warning("Не удалось отправить уведомление админу")
    
    bot.infinity_polling()