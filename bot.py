import telebot
from telebot import types
import os
from flask import Flask
import threading
import json

# ========== ТОКЕН ==========
TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
bot = telebot.TeleBot(TOKEN)

# ========== ID ЧАТА КУДА ПЕРЕСЫЛАТЬ ==========
CHAT_ID = -1003578745710  # Твой ID чата

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
    if message.chat.id == message.from_user.id:
        welcome_text = "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту, и это появится в чате 👇"
        bot.send_message(message.chat.id, welcome_text)
    else:
        bot.send_message(message.chat.id, "✅ Бот работает! Пиши мне в личку")

# ========== ПОЛЬЗОВАТЕЛЬ ПИШЕТ В ЛИЧКУ ==========
@bot.message_handler(func=lambda message: message.chat.id == message.from_user.id, 
                    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 
                                 'video_note', 'sticker', 'animation'])
def handle_user_message(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        # Формируем подпись с ID пользователя для ответов
        caption = f"📨 От: {username}\n🆔 {user.id}"
        
        sent_message = None
        
        # Пересылаем в чат в зависимости от типа
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
        
        # Сохраняем связь между сообщением в чате и ID пользователя
        if sent_message:
            message_links[str(sent_message.message_id)] = user.id
            save_links(message_links)
        
        bot.reply_to(message, "✅ Ваше сообщение отправлено в чат!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при отправке")

# ========== ОТВЕТЫ ИЗ ЧАТА ==========
@bot.message_handler(func=lambda message: message.chat.id == CHAT_ID and message.reply_to_message)
def handle_reply(message):
    try:
        # Получаем ID оригинального сообщения, на которое ответили
        original_msg_id = message.reply_to_message.message_id
        
        # Ищем пользователя по связи
        if str(original_msg_id) in message_links:
            user_id = message_links[str(original_msg_id)]
            
            # Отправляем ответ пользователю
            bot.send_message(user_id, f"📨 Ответ от администратора:\n\n{message.text}")
            bot.reply_to(message, "✅ Ответ отправлен пользователю!")
        else:
            bot.reply_to(message, "❌ Не могу найти пользователя для этого сообщения")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка с ответами запущен...")
    bot.infinity_polling()