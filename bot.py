import telebot
from telebot import types
import os
from flask import Flask
import threading
import json

# ========== ТОКЕН ==========
TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
bot = telebot.TeleBot(TOKEN)

# ========== ТВОЙ ЛИЧНЫЙ ID ==========
ADMIN_ID = 8388843828

# ========== ФАЙЛ ДЛЯ ХРАНЕНИЯ СВЯЗЕЙ ==========
LINKS_FILE = "message_links.json"

def load_links():
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_links(links):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f)

message_links = load_links()

# ========== ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📢 Канал", url="https://t.me/mapsinssb2byhofilion")
    markup.add(btn)
    
    welcome_text = "📬 Предложка | Support\n\nСкидывай сюда пост, он появится на канале 👇"
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# ========== ФУНКЦИЯ ДЛЯ ПОДПИСИ ==========
def get_user_info(user):
    username = user.username or f"{user.first_name or 'Аноним'}"
    return f"📨 От: {username} (ID: {user.id})"

# ========== ТЕКСТ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.text and not message.photo and not message.video and not message.voice and not message.video_note and not message.sticker and not message.document and not message.audio and not message.animation)
def handle_text(message):
    try:
        user_info = get_user_info(message.from_user)
        sent = bot.send_message(ADMIN_ID, f"{user_info}\n\n{message.text}")
        
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== ФОТО ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.photo)
def handle_photo(message):
    try:
        user_info = get_user_info(message.from_user)
        text = message.caption or ""
        full_caption = f"{user_info}\n\n{text}" if text else user_info
        
        sent = bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=full_caption)
        
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== ВИДЕО ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.video)
def handle_video(message):
    try:
        user_info = get_user_info(message.from_user)
        text = message.caption or ""
        full_caption = f"{user_info}\n\n{text}" if text else user_info
        
        sent = bot.send_video(ADMIN_ID, message.video.file_id, caption=full_caption)
        
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== ГИФКИ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.animation)
def handle_animation(message):
    try:
        user_info = get_user_info(message.from_user)
        text = message.caption or ""
        
        # Отправляем гифку
        sent_animation = bot.send_animation(ADMIN_ID, message.animation.file_id)
        
        # Отправляем сообщение с подписью и текстом
        if text:
            sent_text = bot.send_message(ADMIN_ID, f"{user_info}\n\n{text}")
            message_links[str(sent_text.message_id)] = message.chat.id
        else:
            sent_text = bot.send_message(ADMIN_ID, user_info)
            message_links[str(sent_text.message_id)] = message.chat.id
        
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== СТИКЕРЫ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.sticker)
def handle_sticker(message):
    try:
        user_info = get_user_info(message.from_user)
        
        # Отправляем стикер
        sent_sticker = bot.send_sticker(ADMIN_ID, message.sticker.file_id)
        
        # Отправляем подпись
        sent_text = bot.send_message(ADMIN_ID, user_info)
        message_links[str(sent_text.message_id)] = message.chat.id
        
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== КРУЖКИ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.video_note)
def handle_video_note(message):
    try:
        user_info = get_user_info(message.from_user)
        
        # Отправляем кружок
        sent_note = bot.send_video_note(ADMIN_ID, message.video_note.file_id)
        
        # Отправляем подпись
        sent_text = bot.send_message(ADMIN_ID, user_info)
        message_links[str(sent_text.message_id)] = message.chat.id
        
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== ГОЛОСОВЫЕ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.voice)
def handle_voice(message):
    try:
        user_info = get_user_info(message.from_user)
        sent = bot.send_voice(ADMIN_ID, message.voice.file_id, caption=user_info)
        
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== ДОКУМЕНТЫ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.document)
def handle_document(message):
    try:
        user_info = get_user_info(message.from_user)
        text = message.caption or ""
        full_caption = f"{user_info}\n\n{text}" if text else user_info
        
        sent = bot.send_document(ADMIN_ID, message.document.file_id, caption=full_caption)
        
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== АУДИО ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.audio)
def handle_audio(message):
    try:
        user_info = get_user_info(message.from_user)
        text = message.caption or ""
        full_caption = f"{user_info}\n\n{text}" if text else user_info
        
        sent = bot.send_audio(ADMIN_ID, message.audio.file_id, caption=full_caption)
        
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Пост отправлен на канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== АДМИН ОТВЕЧАЕТ ==========
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message)
def reply_to_user(message):
    try:
        original_msg_id = message.reply_to_message.message_id
        
        if str(original_msg_id) in message_links:
            user_id = message_links[str(original_msg_id)]
            
            # Отправляем ответ пользователю
            bot.send_message(user_id, f"📨 Ответ от админа:\n\n{message.text}")
            bot.reply_to(message, "✅ Ответ отправлен!")
        else:
            bot.reply_to(message, "❌ Не могу найти пользователя")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка запущен...")
    bot.infinity_polling()