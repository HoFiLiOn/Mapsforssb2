import telebot
from telebot import types
import os
from flask import Flask
import threading
import json
from datetime import datetime
import time
import re

# ========== ТОКЕН ==========
TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ========== ID АДМИНА ==========
ADMIN_ID = 8388843828

# ========== ID ЧАТА КУДА ПЕРЕСЫЛАТЬ ==========
CHAT_ID = -1003578745710

# ========== ФАЙЛЫ ==========
LINKS_FILE = "message_links.json"
STATS_FILE = "stats.json"
BLACKLIST_FILE = "blacklist.json"
DIALOGS_FILE = "dialogs.json"
ADMIN_NOTES_FILE = "admin_notes.json"
RATINGS_FILE = "ratings.json"

# ========== ЗАГРУЗКА/СОХРАНЕНИЕ ==========
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

message_links = load_json(LINKS_FILE)
stats = load_json(STATS_FILE)
blacklist = load_json(BLACKLIST_FILE)
dialogs = load_json(DIALOGS_FILE)
admin_notes = load_json(ADMIN_NOTES_FILE)
ratings = load_json(RATINGS_FILE)

if "users" not in stats:
    stats["users"] = []
if "messages_count" not in stats:
    stats["messages_count"] = 0
if "daily" not in stats:
    stats["daily"] = {}
if "response_times" not in stats:
    stats["response_times"] = []
if "admin_stats" not in stats:
    stats["admin_stats"] = {}

# ========== АНТИФЛУД ==========
user_last_message = {}
ANTIFLOOD_SECONDS = 5

def check_antiflood(user_id):
    if str(user_id) in WHITELIST:
        return True
    now = time.time()
    if user_id in user_last_message:
        if now - user_last_message[user_id] < ANTIFLOOD_SECONDS:
            return False
    user_last_message[user_id] = now
    return True

# ========== БЕЛЫЙ СПИСОК ==========
WHITELIST = []

# ========== ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ========== КНОПКИ (INLINE) ==========
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/mapsinssb2byhofilion")
    btn2 = types.InlineKeyboardButton("🕵️ Анонимно", callback_data="anon")
    btn3 = types.InlineKeyboardButton("📊 Статистика", callback_data="stats")
    btn4 = types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    btn5 = types.InlineKeyboardButton("💳 Поддержать", callback_data="donate")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("◀️ В главное меню", callback_data="back_to_menu")
    markup.add(btn)
    return markup

def get_confirm_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("✅ Да, отправить", callback_data="confirm_anon")
    btn2 = types.InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")
    markup.add(btn1, btn2)
    return markup

def get_category_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("❓ Вопрос", callback_data="cat_question")
    btn2 = types.InlineKeyboardButton("⚠️ Жалоба", callback_data="cat_complaint")
    btn3 = types.InlineKeyboardButton("💡 Предложение", callback_data="cat_suggestion")
    btn4 = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def get_template_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("✅ Спасибо, принято", callback_data="template_thanks")
    btn2 = types.InlineKeyboardButton("⏳ В работе", callback_data="template_work")
    btn3 = types.InlineKeyboardButton("❌ Отклонено", callback_data="template_reject")
    btn4 = types.InlineKeyboardButton("📞 Напишите в ЛС", callback_data="template_pm")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def get_take_keyboard(msg_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🖐️ Взять в работу", callback_data=f"take_{msg_id}_{user_id}")
    btn2 = types.InlineKeyboardButton("⛔ Бан пользователя", callback_data=f"quick_ban_{user_id}")
    markup.add(btn1, btn2)
    return markup

def get_rating_keyboard(msg_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("👍 Хорошо", callback_data=f"rate_good_{msg_id}_{user_id}")
    btn2 = types.InlineKeyboardButton("👎 Плохо", callback_data=f"rate_bad_{msg_id}_{user_id}")
    markup.add(btn1, btn2)
    return markup

def get_complaint_keyboard(admin_msg_id, user_id):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("⚠️ Пожаловаться на ответ", callback_data=f"complaint_{admin_msg_id}_{user_id}")
    markup.add(btn)
    return markup

# ========== КНОПКИ ДЛЯ АДМИНА (REPLY KEYBOARD) ==========
def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📊 Админ статистика")
    btn2 = types.KeyboardButton("👥 Пользователи")
    btn3 = types.KeyboardButton("⛔ Черный список")
    btn4 = types.KeyboardButton("📢 Рассылка")
    btn5 = types.KeyboardButton("📝 Шаблоны ответов")
    btn6 = types.KeyboardButton("🔍 Поиск пользователя")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.id == message.from_user.id:
        welcome_text = """
📬 <b>Предложка | Support</b>

Скидывай сюда свой вопрос или карту 👇

<i>Используй кнопки ниже для навигации</i>
        """
        if message.from_user.id == ADMIN_ID:
            bot.send_message(
                message.chat.id, 
                welcome_text + "\n\n🔐 <b>Режим администратора</b>",
                reply_markup=get_main_keyboard()
            )
            bot.send_message(
                message.chat.id,
                "🔧 Панель администратора:",
                reply_markup=get_admin_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id, 
                welcome_text, 
                reply_markup=get_main_keyboard()
            )
            bot.send_message(
                message.chat.id,
                "👋 Привет! Я бот-предложка. Твоё сообщение уйдёт администратору. Обычно отвечаем в течение часа."
            )
    else:
        bot.send_message(message.chat.id, "✅ Бот работает! Пиши мне в личку")

# ========== ОБРАБОТКА КНОПОК (INLINE) ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "back_to_menu":
        bot.edit_message_text(
            "📬 <b>Главное меню</b>\n\nСкидывай сюда свой вопрос или карту 👇",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "anon":
        bot.edit_message_text(
            "🕵️ <b>Анонимная отправка</b>\n\nВыбери категорию:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_category_keyboard()
        )
    
    elif call.data == "donate":
        bot.edit_message_text(
            "💳 <b>Поддержать проект</b>\n\nСсылка для доната:\nhttps://www.donationalerts.com/r/FxHoFiLiOn\n\nСпасибо за поддержку! ❤️",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data in ["cat_question", "cat_complaint", "cat_suggestion"]:
        categories = {
            "cat_question": ("Вопрос", "question"),
            "cat_complaint": ("Жалоба", "complaint"),
            "cat_suggestion": ("Предложение", "suggestion")
        }
        cat_name, cat_code = categories[call.data]
        
        bot.answer_callback_query(call.id, f"✅ Категория: {cat_name}")
        bot.edit_message_text(
            f"🕵️ <b>Анонимная отправка</b>\n\nКатегория: {cat_name}\n\nТеперь отправь сообщение, оно уйдёт без ника и ID.\n\nПосле отправки вернись в меню по кнопке ниже 👇",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        message_links[f"anon_{call.from_user.id}"] = {"active": True, "category": cat_code}
        save_json(LINKS_FILE, message_links)
    
    elif call.data == "confirm_anon":
        bot.answer_callback_query(call.id, "✅ Режим анонимки включен")
        bot.edit_message_text(
            "🕵️ <b>Анонимная отправка</b>\n\nТеперь отправь сообщение, оно уйдёт без ника и ID.\n\nПосле отправки вернись в меню по кнопке ниже 👇",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
        message_links[f"anon_{call.from_user.id}"] = {"active": True, "category": "none"}
        save_json(LINKS_FILE, message_links)
    
    elif call.data == "stats":
        total_users = len(stats.get("users", []))
        total_msgs = stats.get("messages_count", 0)
        
        text = f"""
📊 <b>Статистика бота</b>

👥 Пользователей: <code>{total_users}</code>
💬 Сообщений: <code>{total_msgs}</code>

<i>Нажми кнопку ниже чтобы вернуться</i>
        """
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
    
    elif call.data == "help":
        help_text = """
❓ <b>Помощь</b>

📢 <b>Канал</b> — перейти на наш канал
🕵️ <b>Анонимно</b> — отправить без ника
📊 <b>Статистика</b> — информация о боте
💳 <b>Поддержать</b> — ссылка для доната

Просто отправь фото, файл или текст — и оно уйдёт админу!
        """
        bot.edit_message_text(
            help_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_back_keyboard()
        )
    
    # ========== ШАБЛОНЫ ОТВЕТОВ ==========
    elif call.data == "template_thanks":
        answer_user(call, "✅ Спасибо за обращение! Мы приняли его в работу.")
    elif call.data == "template_work":
        answer_user(call, "⏳ Ваше обращение в работе. Ответим в ближайшее время.")
    elif call.data == "template_reject":
        answer_user(call, "❌ К сожалению, ваше обращение отклонено.")
    elif call.data == "template_pm":
        answer_user(call, "📞 Напишите мне в личную переписку для решения вопроса.")
    
    # ========== ВЗЯТЬ В РАБОТУ ==========
    elif call.data.startswith("take_"):
        parts = call.data.split("_")
        msg_id = parts[1]
        user_id = int(parts[2])
        
        if str(msg_id) in message_links:
            message_links[str(msg_id)]["taken_by"] = call.from_user.id
            message_links[str(msg_id)]["status"] = "taken"
            save_json(LINKS_FILE, message_links)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "✅ Вы взяли сообщение в работу!")
            bot.send_message(ADMIN_ID, f"👤 Админ {call.from_user.first_name} взял в работу сообщение от {user_id}")
    
    # ========== БЫСТРЫЙ БАН ==========
    elif call.data.startswith("quick_ban_"):
        user_id = call.data.split("_")[2]
        blacklist[user_id] = True
        save_json(BLACKLIST_FILE, blacklist)
        bot.answer_callback_query(call.id, f"✅ Пользователь {user_id} забанен")
        bot.send_message(ADMIN_ID, f"⛔ Админ {call.from_user.first_name} забанил {user_id}")
    
    # ========== ОЦЕНКА ОТВЕТА ==========
    elif call.data.startswith("rate_good_"):
        parts = call.data.split("_")
        msg_id = parts[2]
        user_id = int(parts[3])
        ratings[f"rate_{msg_id}_{user_id}"] = "good"
        save_json(RATINGS_FILE, ratings)
        bot.answer_callback_query(call.id, "👍 Спасибо за оценку!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    
    elif call.data.startswith("rate_bad_"):
        parts = call.data.split("_")
        msg_id = parts[2]
        user_id = int(parts[3])
        ratings[f"rate_{msg_id}_{user_id}"] = "bad"
        save_json(RATINGS_FILE, ratings)
        bot.answer_callback_query(call.id, "👎 Спасибо за обратную связь, мы учтём!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    
    # ========== ЖАЛОБА НА ОТВЕТ ==========
    elif call.data.startswith("complaint_"):
        parts = call.data.split("_")
        msg_id = parts[1]
        user_id = parts[2]
        bot.send_message(ADMIN_ID, f"⚠️ ЖАЛОБА! Пользователь {user_id} пожаловался на ответ админа (сообщение ID: {msg_id})")
        bot.answer_callback_query(call.id, "⚠️ Жалоба отправлена администратору!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОТВЕТОВ ==========
def answer_user(call, answer_text):
    try:
        original_msg_id = call.message.reply_to_message.message_id if call.message.reply_to_message else None
        
        if original_msg_id and str(original_msg_id) in message_links:
            user_id = message_links[str(original_msg_id)]["user_id"]
            bot.send_message(user_id, f"📨 <b>Ответ от администратора:</b>\n\n{answer_text}")
            
            # Отправляем пользователю кнопку с оценкой
            bot.send_message(
                user_id,
                "Был ли полезен этот ответ?",
                reply_markup=get_rating_keyboard(original_msg_id, user_id)
            )
            
            bot.answer_callback_query(call.id, "✅ Ответ отправлен!")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        else:
            bot.answer_callback_query(call.id, "❌ Не могу найти пользователя")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# ========== ОБРАБОТКА КНОПОК АДМИНА (REPLY) ==========
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.text in [
    "📊 Админ статистика", "👥 Пользователи", "⛔ Черный список", "📢 Рассылка", "📝 Шаблоны ответов", "🔍 Поиск пользователя"
])
def handle_admin_buttons(message):
    if message.text == "📊 Админ статистика":
        today = datetime.now().strftime("%Y-%m-%d")
        today_msgs = stats.get("daily", {}).get(today, 0)
        
        # Среднее время ответа
        avg_time = 0
        if stats.get("response_times"):
            avg_time = sum(stats["response_times"]) / len(stats["response_times"])
        
        text = f"""
📊 <b>АДМИН СТАТИСТИКА</b>

👥 Всего пользователей: {len(stats.get("users", []))}
💬 Всего сообщений: {stats.get("messages_count", 0)}
📨 За сегодня: {today_msgs}
⛔ В бане: {len(blacklist)}
⏱️ Среднее время ответа: {int(avg_time)} сек.
        """
        bot.send_message(message.chat.id, text)
    
    elif message.text == "👥 Пользователи":
        users_list = stats.get("users", [])[-10:]
        if users_list:
            text = "👥 <b>Последние пользователи:</b>\n\n"
            for user_id in users_list:
                text += f"• <code>{user_id}</code>\n"
        else:
            text = "👥 Пока нет пользователей"
        bot.send_message(message.chat.id, text)
    
    elif message.text == "⛔ Черный список":
        if blacklist:
            text = "⛔ <b>Забаненные пользователи:</b>\n\n"
            for user_id in blacklist:
                text += f"• <code>{user_id}</code>\n"
        else:
            text = "✅ Черный список пуст"
        bot.send_message(message.chat.id, text)
    
    elif message.text == "📢 Рассылка":
        msg = bot.send_message(message.chat.id, "📢 Введи текст для рассылки (можно с HTML-тегами):")
        bot.register_next_step_handler(msg, send_broadcast)
    
    elif message.text == "📝 Шаблоны ответов":
        bot.send_message(
            message.chat.id,
            "📝 <b>Быстрые ответы</b>\n\nНажми на кнопку, чтобы отправить шаблон в ответ на сообщение пользователя:",
            reply_markup=get_template_keyboard()
        )
    
    elif message.text == "🔍 Поиск пользователя":
        msg = bot.send_message(message.chat.id, "🔍 Введи ID или username пользователя для поиска:")
        bot.register_next_step_handler(msg, search_user)

# ========== ПОИСК ПОЛЬЗОВАТЕЛЯ ==========
def search_user(message):
    query = message.text.strip().lower()
    found = []
    
    for user_id in stats.get("users", []):
        if query in user_id:
            found.append(user_id)
            continue
        try:
            user = bot.get_chat(int(user_id))
            username = user.username.lower() if user.username else ""
            if query in username:
                found.append(user_id)
        except:
            pass
    
    if found:
        text = "🔍 <b>Результаты поиска:</b>\n\n"
        for uid in found[:10]:
            text += f"• <code>{uid}</code>\n"
            if uid in admin_notes:
                text += f"  <i>Заметка: {admin_notes[uid][:50]}</i>\n"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "❌ Ничего не найдено")

# ========== ПРОВЕРКА БАНА ==========
def is_banned(user_id):
    return str(user_id) in blacklist

# ========== ОБНОВЛЕНИЕ СТАТИСТИКИ ==========
def update_stats(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    
    if str(user_id) not in stats["users"]:
        stats["users"].append(str(user_id))
    
    stats["messages_count"] += 1
    
    if today not in stats["daily"]:
        stats["daily"][today] = 0
    stats["daily"][today] += 1
    
    save_json(STATS_FILE, stats)

# ========== ПОЛЬЗОВАТЕЛЬ ПИШЕТ ==========
@bot.message_handler(func=lambda message: 
    message.chat.id == message.from_user.id and 
    message.chat.id != ADMIN_ID and
    not message.text.startswith('/') if message.text else True,
    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 
                 'video_note', 'sticker', 'animation'])
def handle_user_message(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    if not check_antiflood(user_id):
        bot.reply_to(message, "⏰ Не флуди! Подожди 5 секунд.")
        return
    
    update_stats(user_id)
    
    anon_data = message_links.get(f"anon_{user_id}", {})
    anon_mode = anon_data.get("active", False)
    category = anon_data.get("category", "none")
    
    if anon_mode:
        cat_names = {"question": "Вопрос", "complaint": "Жалоба", "suggestion": "Предложение", "none": "Без категории"}
        caption = f"📨 Анонимное сообщение\n📂 Категория: {cat_names.get(category, 'Без категории')}"
        del message_links[f"anon_{user_id}"]
        save_json(LINKS_FILE, message_links)
    else:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        caption = f"📨 От: {username}\n🆔 {user_id}"
    
    sent_message = None
    
    # Сохраняем диалог
    if str(user_id) not in dialogs:
        dialogs[str(user_id)] = []
    dialogs[str(user_id)].append({
        "time": datetime.now().isoformat(),
        "text": message.text or "[медиа]",
        "direction": "user"
    })
    if len(dialogs[str(user_id)]) > 10:
        dialogs[str(user_id)] = dialogs[str(user_id)][-10:]
    save_json(DIALOGS_FILE, dialogs)
    
    try:
        if message.text:
            sent_message = bot.send_message(CHAT_ID, f"{caption}\n\n{message.text}", reply_markup=get_take_keyboard("temp", user_id))
        elif message.photo:
            file_id = message.photo[-1].file_id
            if message.caption:
                sent_message = bot.send_photo(CHAT_ID, file_id, 
                                            caption=f"{caption}\n\n{message.caption}",
                                            reply_markup=get_take_keyboard("temp", user_id))
            else:
                sent_message = bot.send_photo(CHAT_ID, file_id, caption=caption, reply_markup=get_take_keyboard("temp", user_id))
        elif message.video:
            if message.caption:
                sent_message = bot.send_video(CHAT_ID, message.video.file_id, 
                                            caption=f"{caption}\n\n{message.caption}",
                                            reply_markup=get_take_keyboard("temp", user_id))
            else:
                sent_message = bot.send_video(CHAT_ID, message.video.file_id, caption=caption, reply_markup=get_take_keyboard("temp", user_id))
        elif message.document:
            if message.caption:
                sent_message = bot.send_document(CHAT_ID, message.document.file_id, 
                                               caption=f"{caption}\n\n{message.caption}",
                                               reply_markup=get_take_keyboard("temp", user_id))
            else:
                sent_message = bot.send_document(CHAT_ID, message.document.file_id, caption=caption, reply_markup=get_take_keyboard("temp", user_id))
        elif message.audio:
            if message.caption:
                sent_message = bot.send_audio(CHAT_ID, message.audio.file_id, 
                                            caption=f"{caption}\n\n{message.caption}",
                                            reply_markup=get_take_keyboard("temp", user_id))
            else:
                sent_message = bot.send_audio(CHAT_ID, message.audio.file_id, caption=caption, reply_markup=get_take_keyboard("temp", user_id))
        elif message.voice:
            sent_message = bot.send_voice(CHAT_ID, message.voice.file_id, caption=caption, reply_markup=get_take_keyboard("temp", user_id))
        elif message.video_note:
            bot.send_video_note(CHAT_ID, message.video_note.file_id)
            sent_message = bot.send_message(CHAT_ID, caption, reply_markup=get_take_keyboard("temp", user_id))
        elif message.sticker:
            bot.send_sticker(CHAT_ID, message.sticker.file_id)
            sent_message = bot.send_message(CHAT_ID, caption, reply_markup=get_take_keyboard("temp", user_id))
        elif message.animation:
            if message.caption:
                sent_message = bot.send_animation(CHAT_ID, message.animation.file_id, 
                                                caption=f"{caption}\n\n{message.caption}",
                                                reply_markup=get_take_keyboard("temp", user_id))
            else:
                sent_message = bot.send_animation(CHAT_ID, message.animation.file_id, caption=caption, reply_markup=get_take_keyboard("temp", user_id))
        
        if sent_message:
            # Обновляем кнопку "Взять в работу" с правильным message_id
            try:
                bot.edit_message_reply_markup(CHAT_ID, sent_message.message_id, reply_markup=get_take_keyboard(sent_message.message_id, user_id))
            except:
                pass
            
            message_links[str(sent_message.message_id)] = {
                "user_id": user_id,
                "status": "delivered",
                "time": datetime.now().isoformat()
            }
            save_json(LINKS_FILE, message_links)
        
        bot.send_message(
            message.chat.id,
            "✅ Ваше сообщение отправлено администратору!",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Ошибка при отправке: {e}",
            reply_markup=get_main_keyboard()
        )

# ========== ОТВЕТЫ ИЗ ЧАТА (АДМИН ОТВЕЧАЕТ) ==========
@bot.message_handler(func=lambda message: message.chat.id == CHAT_ID and message.reply_to_message)
def handle_reply(message):
    try:
        original_msg_id = message.reply_to_message.message_id
        
        if str(original_msg_id) in message_links:
            user_id = message_links[str(original_msg_id)]["user_id"]
            
            # Засекаем время ответа
            sent_time = datetime.fromisoformat(message_links[str(original_msg_id)]["time"])
            response_time = (datetime.now() - sent_time).total_seconds()
            stats["response_times"].append(response_time)
            save_json(STATS_FILE, stats)
            
            # Статистика по админам
            admin_name = message.from_user.first_name
            if admin_name not in stats["admin_stats"]:
                stats["admin_stats"][admin_name] = 0
            stats["admin_stats"][admin_name] += 1
            save_json(STATS_FILE, stats)
            
            # Отправляем ответ пользователю
            bot.send_message(
                user_id,
                f"📨 <b>Ответ от администратора:</b>\n\n{message.text}",
                reply_markup=get_rating_keyboard(original_msg_id, user_id)
            )
            
            # Отправляем админу кнопку с жалобой (в чат, где он ответил)
            bot.send_message(
                CHAT_ID,
                f"✅ Ответ отправлен пользователю {user_id}",
                reply_to_message_id=message.message_id,
                reply_markup=get_complaint_keyboard(original_msg_id, user_id)
            )
            
            # Сохраняем диалог
            if str(user_id) not in dialogs:
                dialogs[str(user_id)] = []
            dialogs[str(user_id)].append({
                "time": datetime.now().isoformat(),
                "text": message.text,
                "direction": "admin"
            })
            if len(dialogs[str(user_id)]) > 10:
                dialogs[str(user_id)] = dialogs[str(user_id)][-10:]
            save_json(DIALOGS_FILE, dialogs)
            
            message_links[str(original_msg_id)]["status"] = "replied"
            message_links[str(original_msg_id)]["replied_at"] = datetime.now().isoformat()
            save_json(LINKS_FILE, message_links)
        else:
            bot.reply_to(message, "❌ Не могу найти пользователя")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ЧЕРНЫЙ СПИСОК ==========
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = str(int(message.text.split()[1]))
        blacklist[user_id] = True
        save_json(BLACKLIST_FILE, blacklist)
        bot.reply_to(message, f"✅ Пользователь {user_id} забанен")
    except:
        bot.reply_to(message, "❌ Использование: /ban 123456789")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = str(int(message.text.split()[1]))
        if user_id in blacklist:
            del blacklist[user_id]
            save_json(BLACKLIST_FILE, blacklist)
            bot.reply_to(message, f"✅ Пользователь {user_id} разбанен")
    except:
        bot.reply_to(message, "❌ Использование: /unban 123456789")

# ========== ЗАМЕТКИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========
@bot.message_handler(commands=['note'])
def add_note(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        user_id = parts[1]
        note_text = parts[2]
        admin_notes[user_id] = note_text
        save_json(ADMIN_NOTES_FILE, admin_notes)
        bot.reply_to(message, f"✅ Заметка для {user_id} сохранена")
    except:
        bot.reply_to(message, "❌ Использование: /note 123456789 Текст заметки")

@bot.message_handler(commands=['getnote'])
def get_note(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = message.text.split()[1]
        note = admin_notes.get(user_id, "Нет заметок")
        bot.reply_to(message, f"📝 Заметка для {user_id}:\n{note}")
    except:
        bot.reply_to(message, "❌ Использование: /getnote 123456789")

# ========== ИСТОРИЯ ДИАЛОГА ==========
@bot.message_handler(commands=['history'])
def show_history(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = message.text.split()[1]
        history = dialogs.get(user_id, [])
        
        if not history:
            bot.reply_to(message, f"📭 Нет истории для {user_id}")
            return
        
        text = f"📜 <b>История диалога с {user_id}</b>\n\n"
        for entry in history[-10:]:
            direction = "👤 Пользователь" if entry["direction"] == "user" else "👨‍💼 Админ"
            time_str = entry["time"][:16]
            text += f"[{time_str}] {direction}:\n{entry['text'][:100]}\n\n"
        
        bot.send_message(message.chat.id, text[:4000])
    except:
        bot.reply_to(message, "❌ Использование: /history 123456789")

# ========== СПИСОК ЗАБАНЕННЫХ ДЛЯ ВСЕХ ==========
@bot.message_handler(commands=['banlist'])
def banlist_command(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/mapsinssb2byhofilion")
    markup.add(btn)
    
    if blacklist:
        count = len(blacklist)
        text = f"""
⛔ <b>Забанено пользователей:</b> {count}

<i>Список не показывается в целях безопасности</i>
        """
    else:
        text = "✅ Забаненных пользователей нет"
    
    bot.send_message(message.chat.id, text, reply_markup=markup)

# ========== РАССЫЛКА ==========
def send_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text
    sent = 0
    failed = 0
    
    for user_id in stats.get("users", []):
        try:
            bot.send_message(int(user_id), f"📢 <b>Рассылка от администратора:</b>\n\n{text}")
            sent += 1
        except:
            failed += 1
    
    bot.reply_to(message, f"✅ Рассылка завершена!\n📨 Отправлено: {sent}\n❌ Не доставлено: {failed}")

# ========== ИНФО ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========
@bot.message_handler(commands=['info'])
def info_command(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/mapsinssb2byhofilion")
    markup.add(btn)
    
    text = """
📬 <b>Предложка | Support</b>

Бот создан для обратной связи.
Все сообщения уходят напрямую администратору.
    """
    bot.send_message(message.chat.id, text, reply_markup=markup)

# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========
@bot.message_handler(commands=['adminstats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_msgs = stats.get("daily", {}).get(today, 0)
    
    avg_time = 0
    if stats.get("response_times"):
        avg_time = sum(stats["response_times"]) / len(stats["response_times"])
    
    admin_ranking = sorted(stats.get("admin_stats", {}).items(), key=lambda x: x[1], reverse=True)
    admin_text = ""
    for name, count in admin_ranking[:5]:
        admin_text += f"• {name}: {count} ответов\n"
    
    text = f"""
📊 <b>ПОЛНАЯ СТАТИСТИКА (Админ)</b>

👥 Всего пользователей: {len(stats.get("users", []))}
💬 Всего сообщений: {stats.get("messages_count", 0)}
📨 За сегодня: {today_msgs}
⛔ Забанено: {len(blacklist)}
⏱️ Среднее время ответа: {int(avg_time)} сек.

<b>🏆 Топ админов по ответам:</b>
{admin_text or "Нет данных"}
    """
    bot.send_message(message.chat.id, text)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка с улучшениями запущен...")
    bot.infinity_polling()