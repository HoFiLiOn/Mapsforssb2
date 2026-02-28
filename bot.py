import telebot
import os
from datetime import datetime
from flask import Flask
import threading

# ========== ТОКЕН ==========
TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
bot = telebot.TeleBot(TOKEN)

# ========== НАСТРОЙКИ ==========
# ID чата/канала, куда будут приходить предложки
# ЗАМЕНИ НА СВОЙ ID ПОСЛЕ ТЕСТА
TARGET_CHAT_ID = -1001234567890

# ========== ВЕБ-СЕРВЕР ДЛЯ ХОСТИНГА ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Suggestion Bot is alive!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_text = """
👋 Привет! Я бот для предложок.

📝 Как это работает:
Ты пишешь мне любое сообщение, а я пересылаю его в общий чат.

💡 Что можно писать:
• Идеи для контента
• Вопросы
• Предложения
• Мемы

Просто напиши что-нибудь!
    """
    bot.reply_to(message, welcome_text)

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
@bot.message_handler(func=lambda message: True)
def forward_to_chat(message):
    try:
        user = message.from_user
        
        # Определяем отправителя
        if user.username:
            sender = f"@{user.username}"
        else:
            sender = f"{user.first_name or 'Аноним'}"
        
        # Формируем сообщение для чата
        caption = f"📨 Новая предложка от {sender}:\n\n{message.text}"
        
        # Отправляем в целевой чат
        bot.send_message(TARGET_CHAT_ID, caption)
        
        # Подтверждение пользователю
        bot.reply_to(message, "✅ Сообщение отправлено в чат! Спасибо!")
        
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при отправке. Попробуй позже.")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🤖 Бот для предложок запущен...")
    bot.infinity_polling()
