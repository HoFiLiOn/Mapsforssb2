import telebot
import os
from flask import Flask
import threading

# ========== ТОКЕН ==========
TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
bot = telebot.TeleBot(TOKEN)

# ========== ТВОЙ ЛИЧНЫЙ ID ==========
ADMIN_ID = 8388843828

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
    welcome_text = "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту 👇"
    bot.send_message(message.chat.id, welcome_text)

# ========== ТЕКСТ ==========
@bot.message_handler(func=lambda message: message.text and not message.photo and message.chat.id != ADMIN_ID)
def handle_text(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        text = f"📨 От: {username}\n\n{message.text}"
        
        bot.send_message(ADMIN_ID, text)
        bot.reply_to(message, "✅ Ваше сообщение отправлено администратору!")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ФОТО + ТЕКСТ ==========
@bot.message_handler(func=lambda message: message.photo and message.chat.id != ADMIN_ID)
def handle_photo(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        file_id = message.photo[-1].file_id
        
        # Если есть текст под фото
        if message.caption:
            caption = f"📨 От: {username}\n\n{message.caption}"
        else:
            caption = f"📨 От: {username}"
        
        bot.send_photo(ADMIN_ID, file_id, caption=caption)
        bot.reply_to(message, "✅ Ваше сообщение отправлено администратору!")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ФАЙЛЫ ==========
@bot.message_handler(func=lambda message: message.document and message.chat.id != ADMIN_ID)
def handle_document(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        if message.caption:
            caption = f"📨 От: {username}\n\n{message.caption}"
        else:
            caption = f"📨 От: {username}"
        
        bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
        bot.reply_to(message, "✅ Ваше сообщение отправлено администратору!")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ВСЁ ОСТАЛЬНОЕ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def handle_other(message):
    bot.reply_to(message, "❌ Можно отправлять только текст, фото или файлы")

print("🤖 Бот предложка запущен...")
bot.infinity_polling()