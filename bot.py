import telebot
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

# Загружаем связи сообщений
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
    bot.reply_to(message, """
👋 Привет! Я бот для связи с админом.

📝 Напиши любое сообщение, и оно уйдёт админу.
Админ сможет тебе ответить прямо из чата.
    """)

# ========== ПОЛЬЗОВАТЕЛЬ ПИШЕТ БОТУ ==========
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def forward_to_admin(message):
    try:
        # Пересылаем сообщение админу
        forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        
        # Запоминаем связь: ID сообщения у админа -> ID пользователя
        message_links[str(forwarded.message_id)] = message.chat.id
        save_links(message_links)
        
        # Подтверждение пользователю
        bot.reply_to(message, "✅ Сообщение отправлено админу! Ответ придёт сюда же.")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при отправке")

# ========== АДМИН ОТВЕЧАЕТ ==========
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message)
def reply_to_user(message):
    try:
        # Получаем ID оригинального сообщения, на которое ответил админ
        original_msg_id = message.reply_to_message.message_id
        
        # Ищем пользователя по связи
        if str(original_msg_id) in message_links:
            user_id = message_links[str(original_msg_id)]
            
            # Отправляем ответ пользователю
            bot.send_message(user_id, f"📨 Ответ от админа:\n\n{message.text}")
            bot.reply_to(message, "✅ Ответ отправлен пользователю!")
        else:
            bot.reply_to(message, "❌ Не могу найти пользователя для этого сообщения")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот для связи запущен...")
    bot.infinity_polling()