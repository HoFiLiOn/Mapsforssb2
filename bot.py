import telebot
from telebot import types
import os
from flask import Flask
import threading
import json
from datetime import datetime

# ========== ТОКЕН ==========
TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
bot = telebot.TeleBot(TOKEN)

# ========== ID АДМИНА ==========
ADMIN_ID = 8388843828

# ========== ID ЧАТА КУДА ПЕРЕСЫЛАТЬ ==========
CHAT_ID = -1003578745710

# ========== ФАЙЛЫ ==========
LINKS_FILE = "message_links.json"
STATS_FILE = "stats.json"
BLACKLIST_FILE = "blacklist.json"

# ========== ЗАГРУЗКА/СОХРАНЕНИЕ ==========
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f)

message_links = load_json(LINKS_FILE)
stats = load_json(STATS_FILE)
blacklist = load_json(BLACKLIST_FILE)

if "users" not in stats:
    stats["users"] = []
if "messages_count" not in stats:
    stats["messages_count"] = 0
if "daily" not in stats:
    stats["daily"] = {}

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
    markup.add(btn1, btn2, btn3, btn4)
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

# ========== КНОПКИ ДЛЯ АДМИНА (REPLY KEYBOARD) ==========
def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📊 Админ статистика")
    btn2 = types.KeyboardButton("👥 Пользователи")
    btn3 = types.KeyboardButton("⛔ Черный список")
    btn4 = types.KeyboardButton("📢 Рассылка")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.id == message.from_user.id:
        welcome_text = """
📬 **Предложка | Support**

Скидывай сюда свой вопрос или карту 👇

_Используй кнопки ниже для навигации_
        """
        if message.from_user.id == ADMIN_ID:
            bot.send_message(
                message.chat.id, 
                welcome_text + "\n\n🔐 **Режим администратора**",
                parse_mode="Markdown",
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
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    else:
        bot.send_message(message.chat.id, "✅ Бот работает! Пиши мне в личку")

# ========== ОБРАБОТКА КНОПОК (INLINE) ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "back_to_menu":
        bot.edit_message_text(
            "📬 **Главное меню**\n\nСкидывай сюда свой вопрос или карту 👇",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "anon":
        bot.edit_message_text(
            "🕵️ **Анонимная отправка**\n\nСообщение будет отправлено **без ника и ID**.\n\nПродолжить?",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_confirm_keyboard()
        )
    
    elif call.data == "confirm_anon":
        bot.answer_callback_query(call.id, "✅ Режим анонимки включен")
        bot.edit_message_text(
            "🕵️ **Режим анонимки**\n\nТеперь отправь сообщение, оно уйдет без ника и ID.\n\nПосле отправки вернись в меню по кнопке ниже 👇",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        message_links[f"anon_{call.from_user.id}"] = True
        save_json(LINKS_FILE, message_links)
    
    elif call.data == "stats":
        total_users = len(stats.get("users", []))
        total_msgs = stats.get("messages_count", 0)
        
        text = f"""
📊 **Статистика бота**

👥 Пользователей: `{total_users}`
💬 Сообщений: `{total_msgs}`

_Нажми кнопку ниже чтобы вернуться_
        """
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
    
    elif call.data == "help":
        help_text = """
❓ **Помощь**

📢 **Канал** — перейти на наш канал
🕵️ **Анонимно** — отправить без ника
📊 **Статистика** — информация о боте

Просто отправь фото, файл или текст — и оно уйдет админу!
        """
        bot.edit_message_text(
            help_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )

# ========== ОБРАБОТКА КНОПОК АДМИНА (REPLY) ==========
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.text in [
    "📊 Админ статистика", "👥 Пользователи", "⛔ Черный список", "📢 Рассылка"
])
def handle_admin_buttons(message):
    if message.text == "📊 Админ статистика":
        today = datetime.now().strftime("%Y-%m-%d")
        today_msgs = stats.get("daily", {}).get(today, 0)
        
        text = f"""
📊 **АДМИН СТАТИСТИКА**

👥 Всего пользователей: {len(stats.get("users", []))}
💬 Всего сообщений: {stats.get("messages_count", 0)}
📨 За сегодня: {today_msgs}
⛔ В бане: {len(blacklist)}
        """
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    
    elif message.text == "👥 Пользователи":
        users_list = stats.get("users", [])[-10:]
        if users_list:
            text = "👥 **Последние пользователи:**\n\n"
            for user_id in users_list:
                text += f"• `{user_id}`\n"
        else:
            text = "👥 Пока нет пользователей"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    
    elif message.text == "⛔ Черный список":
        if blacklist:
            text = "⛔ **Забаненные пользователи:**\n\n"
            for user_id in blacklist:
                text += f"• `{user_id}`\n"
        else:
            text = "✅ Черный список пуст"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    
    elif message.text == "📢 Рассылка":
        msg = bot.send_message(message.chat.id, "📢 Введи текст для рассылки:")
        bot.register_next_step_handler(msg, send_broadcast)

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

# ========== ПОЛЬЗОВАТЕЛЬ ПИШЕТ (игнорируем команды) ==========
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
    
    update_stats(user_id)
    
    anon_mode = message_links.get(f"anon_{user_id}", False)
    
    if anon_mode:
        caption = "📨 Анонимное сообщение"
        del message_links[f"anon_{user_id}"]
        save_json(LINKS_FILE, message_links)
    else:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        caption = f"📨 От: {username}\n🆔 {user_id}"
    
    sent_message = None
    
    try:
        if message.text:
            sent_message = bot.send_message(CHAT_ID, f"{caption}\n\n{message.text}")
        elif message.photo:
            file_id = message.photo[-1].file_id
            if message.caption:
                sent_message = bot.send_photo(CHAT_ID, file_id, 
                                            caption=f"{caption}\n\n{message.caption}")
            else:
                sent_message = bot.send_photo(CHAT_ID, file_id, caption=caption)
        elif message.video:
            if message.caption:
                sent_message = bot.send_video(CHAT_ID, message.video.file_id, 
                                            caption=f"{caption}\n\n{message.caption}")
            else:
                sent_message = bot.send_video(CHAT_ID, message.video.file_id, caption=caption)
        elif message.document:
            if message.caption:
                sent_message = bot.send_document(CHAT_ID, message.document.file_id, 
                                               caption=f"{caption}\n\n{message.caption}")
            else:
                sent_message = bot.send_document(CHAT_ID, message.document.file_id, caption=caption)
        elif message.audio:
            if message.caption:
                sent_message = bot.send_audio(CHAT_ID, message.audio.file_id, 
                                            caption=f"{caption}\n\n{message.caption}")
            else:
                sent_message = bot.send_audio(CHAT_ID, message.audio.file_id, caption=caption)
        elif message.voice:
            sent_message = bot.send_voice(CHAT_ID, message.voice.file_id, caption=caption)
        elif message.video_note:
            bot.send_video_note(CHAT_ID, message.video_note.file_id)
            sent_message = bot.send_message(CHAT_ID, caption)
        elif message.sticker:
            bot.send_sticker(CHAT_ID, message.sticker.file_id)
            sent_message = bot.send_message(CHAT_ID, caption)
        elif message.animation:
            if message.caption:
                sent_message = bot.send_animation(CHAT_ID, message.animation.file_id, 
                                                caption=f"{caption}\n\n{message.caption}")
            else:
                sent_message = bot.send_animation(CHAT_ID, message.animation.file_id, caption=caption)
        
        if sent_message:
            message_links[str(sent_message.message_id)] = {
                "user_id": user_id,
                "status": "delivered"
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
            "❌ Ошибка при отправке",
            reply_markup=get_main_keyboard()
        )

# ========== ОТВЕТЫ ИЗ ЧАТА (АДМИН ОТВЕЧАЕТ) ==========
@bot.message_handler(func=lambda message: message.chat.id == CHAT_ID and message.reply_to_message)
def handle_reply(message):
    try:
        original_msg_id = message.reply_to_message.message_id
        
        if str(original_msg_id) in message_links:
            user_id = message_links[str(original_msg_id)]["user_id"]
            
            bot.send_message(
                user_id,
                f"📨 **Ответ от администратора:**\n\n{message.text}",
                parse_mode="Markdown"
            )
            
            message_links[str(original_msg_id)]["status"] = "replied"
            save_json(LINKS_FILE, message_links)
            
            bot.reply_to(message, "✅ Ответ отправлен пользователю!")
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

# ========== СПИСОК ЗАБАНЕННЫХ ДЛЯ ВСЕХ ==========
@bot.message_handler(commands=['banlist'])
def banlist_command(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/mapsinssb2byhofilion")
    markup.add(btn)
    
    if blacklist:
        count = len(blacklist)
        text = f"""
⛔ **Забанено пользователей:** {count}

_Список не показывается в целях безопасности_
        """
    else:
        text = "✅ Забаненных пользователей нет"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# ========== РАССЫЛКА ==========
def send_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text
    sent = 0
    failed = 0
    
    for user_id in stats.get("users", []):
        try:
            bot.send_message(int(user_id), f"📢 **Рассылка от администратора:**\n\n{text}", parse_mode="Markdown")
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
📬 **Предложка | Support**

Бот создан для обратной связи.
Все сообщения уходят напрямую администратору.

По всем вопросам - сюда 👇
    """
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========
@bot.message_handler(commands=['adminstats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_msgs = stats.get("daily", {}).get(today, 0)
    
    text = f"""
📊 **ПОЛНАЯ СТАТИСТИКА (Админ)**

👥 Всего пользователей: {len(stats.get("users", []))}
💬 Всего сообщений: {stats.get("messages_count", 0)}
📨 За сегодня: {today_msgs}
⛔ Забанено: {len(blacklist)}
    """
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка с улучшениями запущен...")
    bot.infinity_polling()