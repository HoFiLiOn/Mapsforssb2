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
# Добавь бота в чат, сделай админом,
# напиши в чат /start и сюда вставь ID чата
CHAT_ID = -1003578745710  # ЗАМЕНИ НА ID СВОЕГО ЧАТА

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
    # Если команда из чата где бот админ
    if message.chat.id == CHAT_ID:
        bot.send_message(CHAT_ID, "✅ Бот работает и готов принимать предложки в личке!")
    else:
        # Если в личке
        welcome_text = "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту, и это появится в чате 👇"
        bot.send_message(message.chat.id, welcome_text)

# ========== ПОЛЬЗОВАТЕЛЬ ПИШЕТ В ЛИЧКУ ==========
@bot.message_handler(func=lambda message: message.chat.id != CHAT_ID and message.chat.type == 'private')
def handle_user_message(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        # Подпись для чата
        signature = f"📨 Предложка от {username}"
        
        # Текст
        if message.text:
            bot.send_message(CHAT_ID, f"{signature}:\n\n{message.text}")
            bot.reply_to(message, "✅ Ваше сообщение отправлено в чат!")
        
        # Фото
        elif message.photo:
            caption = signature
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            bot.send_photo(CHAT_ID, message.photo[-1].file_id, caption=caption)
            bot.reply_to(message, "✅ Ваше фото отправлено в чат!")
        
        # Файлы
        elif message.document:
            caption = signature
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            bot.send_document(CHAT_ID, message.document.file_id, caption=caption)
            bot.reply_to(message, "✅ Ваш файл отправлен в чат!")
        
        # Всё остальное
        else:
            bot.reply_to(message, "❌ Можно отправлять только текст, фото или файлы")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== В ЧАТЕ БОТ НИЧЕГО НЕ ОТВЕЧАЕТ ==========
@bot.message_handler(func=lambda message: message.chat.id == CHAT_ID)
def handle_chat_messages(message):
    # Игнорируем все сообщения в чате
    pass

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка для чата запущен...")
    bot.infinity_polling()