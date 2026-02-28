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
    btn = types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/mapsinssb2byhofilion")
    markup.add(btn)
    
    welcome_text = "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту 👇"
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# ========== ОБРАБОТКА ТЕКСТА ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.text)
def handle_text(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        text = f"📨 От: {username} (ID: {user.id})\n\n{message.text}"
        
        sent = bot.send_message(ADMIN_ID, text)
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Ваше сообщение отправлено администратору!")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ОБРАБОТКА ФОТО ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.photo)
def handle_photo(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        # Берем только фото, текст не нужен
        caption = f"📨 От: {username} (ID: {user.id})"
        
        sent = bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Ваше сообщение отправлено администратору!")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ОБРАБОТКА ФАЙЛОВ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and message.document)
def handle_document(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        
        caption = f"📨 От: {username} (ID: {user.id})"
        
        sent = bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
        message_links[str(sent.message_id)] = message.chat.id
        save_links(message_links)
        bot.reply_to(message, "✅ Ваше сообщение отправлено администратору!")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== АДМИН ОТВЕЧАЕТ ==========
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message)
def reply_to_user(message):
    try:
        original_msg_id = message.reply_to_message.message_id
        
        if str(original_msg_id) in message_links:
            user_id = message_links[str(original_msg_id)]
            bot.send_message(user_id, f"📨 Ответ от администратора:\n\n{message.text}")
            bot.reply_to(message, "✅ Ответ отправлен пользователю!")
        else:
            bot.reply_to(message, "❌ Не могу найти пользователя")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот предложка запущен...")
    bot.infinity_polling()