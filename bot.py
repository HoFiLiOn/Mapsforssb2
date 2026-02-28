import telebot
from telebot import types
import os
from flask import Flask
import threading

# ========== ТОКЕН ==========
TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
bot = telebot.TeleBot(TOKEN)

# ========== ID ЧАТА КУДА ПЕРЕСЫЛАТЬ ==========
# ЗДЕСЬ ВСТАВЬ ПРАВИЛЬНЫЙ ID (после @getidsbot)
CHAT_ID = -1003578745710  # Исправь на правильный отрицательный ID

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
    if message.chat.id == message.from_user.id:  # Если это личка
        welcome_text = "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту, и это появится в чате 👇"
        bot.send_message(message.chat.id, welcome_text)
    else:  # Если в группе
        bot.send_message(message.chat.id, "✅ Бот работает! Пиши мне в личку @terminal_trades_bot")

# ========== УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ВСЕХ ТИПОВ ==========
@bot.message_handler(func=lambda message: message.chat.id == message.from_user.id, 
                    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 
                                 'video_note', 'sticker', 'animation'])
def handle_all(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        # Формируем подпись
        caption = f"📨 От: {username}"
        
        # Пересылаем в зависимости от типа
        if message.text:
            bot.send_message(CHAT_ID, f"{caption}\n\n{message.text}")
            
        elif message.photo:
            # Фото с подписью
            file_id = message.photo[-1].file_id
            if message.caption:
                bot.send_photo(CHAT_ID, file_id, caption=f"{caption}\n\n{message.caption}")
            else:
                bot.send_photo(CHAT_ID, file_id, caption=caption)
                
        elif message.video:
            if message.caption:
                bot.send_video(CHAT_ID, message.video.file_id, 
                              caption=f"{caption}\n\n{message.caption}")
            else:
                bot.send_video(CHAT_ID, message.video.file_id, caption=caption)
                
        elif message.document:
            if message.caption:
                bot.send_document(CHAT_ID, message.document.file_id, 
                                 caption=f"{caption}\n\n{message.caption}")
            else:
                bot.send_document(CHAT_ID, message.document.file_id, caption=caption)
                
        elif message.audio:
            if message.caption:
                bot.send_audio(CHAT_ID, message.audio.file_id, 
                              caption=f"{caption}\n\n{message.caption}")
            else:
                bot.send_audio(CHAT_ID, message.audio.file_id, caption=caption)
                
        elif message.voice:
            bot.send_voice(CHAT_ID, message.voice.file_id, caption=caption)
            
        elif message.video_note:  # Кружок
            bot.send_video_note(CHAT_ID, message.video_note.file_id)
            bot.send_message(CHAT_ID, caption)
            
        elif message.sticker:
            bot.send_sticker(CHAT_ID, message.sticker.file_id)
            bot.send_message(CHAT_ID, caption)
            
        elif message.animation:  # GIF
            if message.caption:
                bot.send_animation(CHAT_ID, message.animation.file_id, 
                                  caption=f"{caption}\n\n{message.caption}")
            else:
                bot.send_animation(CHAT_ID, message.animation.file_id, caption=caption)
        
        # Подтверждение пользователю
        bot.reply_to(message, "✅ Ваше сообщение отправлено в чат!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при отправке")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка запущен...")
    bot.infinity_polling()