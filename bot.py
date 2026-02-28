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

# ========== УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ВСЕХ ТИПОВ ==========
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note', 'sticker', 'document', 'audio', 'animation'], func=lambda message: message.chat.id != ADMIN_ID)
def forward_to_admin(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        # Подпись для админа
        caption = f"📨 От: {username} (ID: {user.id})"
        
        # Определяем тип контента и пересылаем
        sent = None
        
        if message.text:
            sent = bot.send_message(ADMIN_ID, f"{caption}\n\n{message.text}")
            
        elif message.photo:
            sent = bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
            
        elif message.video:
            sent = bot.send_video(ADMIN_ID, message.video.file_id, caption=caption)
            
        elif message.voice:
            sent = bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption)
            
        elif message.video_note:
            sent = bot.send_video_note(ADMIN_ID, message.video_note.file_id)
            if sent:
                bot.send_message(ADMIN_ID, caption)
                
        elif message.sticker:
            sent = bot.send_sticker(ADMIN_ID, message.sticker.file_id)
            if sent:
                bot.send_message(ADMIN_ID, caption)
                
        elif message.document:
            sent = bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
            
        elif message.audio:
            sent = bot.send_audio(ADMIN_ID, message.audio.file_id, caption=caption)
            
        elif message.animation:
            sent = bot.send_animation(ADMIN_ID, message.animation.file_id, caption=caption)
        
        # Запоминаем связь для ответов
        if sent:
            # Если отправили два сообщения (для стикеров и кружков)
            if isinstance(sent, list):
                for msg in sent:
                    message_links[str(msg.message_id)] = message.chat.id
            else:
                message_links[str(sent.message_id)] = message.chat.id
            
            save_links(message_links)
        
        # Подтверждение пользователю
        bot.reply_to(message, "✅ Ваше сообщение возможно скоро будет на канале")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при отправке: {str(e)}")

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