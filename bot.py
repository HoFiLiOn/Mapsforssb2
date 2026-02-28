import telebot
from telebot import types
import os
from flask import Flask
import threading
import json
from datetime import datetime, timedelta

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

# ========== КНОПКИ ==========
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton("📢 Канал", url="https://t.me/mapsinssb2byhofilion")
    btn2 = types.InlineKeyboardButton("🕵️ Анонимно", callback_data="anon")
    btn3 = types.InlineKeyboardButton("📊 Статистика", callback_data="stats")
    markup.add(btn1, btn2, btn3)
    return markup

def get_confirm_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("✅ Да, отправить", callback_data="confirm_anon")
    btn2 = types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_anon")
    markup.add(btn1, btn2)
    return markup

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.id == message.from_user.id:
        welcome_text = "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту 👇"
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())
    else:
        bot.send_message(message.chat.id, "✅ Бот работает! Пиши мне в личку")

# ========== ОБРАБОТКА КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "anon":
        bot.edit_message_text(
            "⚠️ Сообщение будет отправлено анонимно (без ника и ID).\nПродолжить?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_confirm_keyboard()
        )
    
    elif call.data == "confirm_anon":
        bot.answer_callback_query(call.id, "✅ Режим анонимки включен")
        bot.edit_message_text(
            "📨 Теперь отправь сообщение, оно уйдет анонимно",
            call.message.chat.id,
            call.message.message_id
        )
        # Сохраняем флаг анонимки для пользователя
        message_links[f"anon_{call.from_user.id}"] = True
        save_json(LINKS_FILE, message_links)
    
    elif call.data == "cancel_anon":
        bot.answer_callback_query(call.id, "❌ Отменено")
        bot.edit_message_text(
            "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту 👇",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_keyboard()
        )
        if f"anon_{call.from_user.id}" in message_links:
            del message_links[f"anon_{call.from_user.id}"]
            save_json(LINKS_FILE, message_links)
    
    elif call.data == "stats":
        total_users = len(stats.get("users", []))
        total_msgs = stats.get("messages_count", 0)
        
        text = f"""
📊 Статистика бота:
👥 Пользователей: {total_users}
💬 Сообщений: {total_msgs}
        """
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text)

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
@bot.message_handler(func=lambda message: message.chat.id == message.from_user.id, 
                    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 
                                 'video_note', 'sticker', 'animation'])
def handle_user_message(message):
    user_id = message.from_user.id
    
    # Проверка на бан
    if is_banned(user_id):
        bot.reply_to(message, "❌ Вы забанены")
        return
    
    # Обновляем статистику
    update_stats(user_id)
    
    # Проверяем анонимный режим
    anon_mode = message_links.get(f"anon_{user_id}", False)
    
    # Формируем подпись
    if anon_mode:
        caption = "📨 Анонимное сообщение"
        # Сбрасываем анонимный режим
        del message_links[f"anon_{user_id}"]
        save_json(LINKS_FILE, message_links)
    else:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        caption = f"📨 От: {username}\n🆔 {user_id}"
    
    sent_message = None
    
    # Отправка в чат
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
        
        bot.reply_to(message, "✅ Ваше сообщение отправлено администратору!", reply_markup=get_main_keyboard())
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при отправке")

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

# ========== РАССЫЛКА ==========
@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    msg = bot.reply_to(message, "📢 Введи текст для рассылки:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text
    sent = 0
    failed = 0
    
    for user_id in stats.get("users", []):
        try:
            bot.send_message(int(user_id), f"📢 Рассылка от администратора:\n\n{text}")
            sent += 1
        except:
            failed += 1
    
    bot.reply_to(message, f"✅ Рассылка завершена!\n📨 Отправлено: {sent}\n❌ Не доставлено: {failed}")

# ========== СТАТИСТИКА ДЛЯ ВСЕХ ==========
@bot.message_handler(commands=['stats'])
def public_stats(message):
    total_users = len(stats.get("users", []))
    total_msgs = stats.get("messages_count", 0)
    
    text = f"""
📊 Статистика бота:
👥 Всего пользователей: {total_users}
💬 Всего сообщений: {total_msgs}
    """
    bot.send_message(message.chat.id, text)

# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========
@bot.message_handler(commands=['adminstats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_msgs = stats.get("daily", {}).get(today, 0)
    
    text = f"""
📊 ПОЛНАЯ СТАТИСТИКА (Админ)

👥 Всего пользователей: {len(stats.get("users", []))}
💬 Всего сообщений: {stats.get("messages_count", 0)}
📨 За сегодня: {today_msgs}
⛔ Забанено: {len(blacklist)}
    """
    bot.send_message(message.chat.id, text)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка с улучшениями запущен...")
    bot.infinity_polling()