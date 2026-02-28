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
    
    welcome_text = "📬 Предложка | Support\n\nСкидывай сюда свой вопрос или карту, и это появится в нашем канале 👇"
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# ========== УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID, content_types=['text', 'photo', 'video', 'voice', 'video_note', 'sticker', 'document', 'audio', 'animation'])
def handle_all(message):
    try:
        user = message.from_user
        username = user.username or f"{user.first_name or 'Аноним'}"
        user_info = f"📨 От: {username} (ID: {user.id})"
        
        # Текст
        if message.text:
            sent = bot.send_message(ADMIN_ID, f"{user_info}\n\n{message.text}")
            message_links[str(sent.message_id)] = message.chat.id
        
        # Фото
        elif message.photo:
            text = message.caption or ""
            caption = f"{user_info}\n\n{text}" if text else user_info
            sent = bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
            message_links[str(sent.message_id)] = message.chat.id
        
        # Видео
        elif message.video:
            text = message.caption or ""
            caption = f"{user_info}\n\n{text}" if text else user