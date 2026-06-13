import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
ADMIN_ID = 7040677455

bot = telebot.TeleBot(BOT_TOKEN)

# Цветные кнопки для админа
def admin_buttons(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    
    btn_accept = InlineKeyboardButton("Принять", callback_data=f"accept_{user_id}")
    btn_accept.style = "success"
    
    btn_reject = InlineKeyboardButton("Отклонить", callback_data=f"reject_{user_id}")
    btn_reject.style = "danger"
    
    btn_reply = InlineKeyboardButton("Ответить", callback_data=f"reply_{user_id}")
    btn_reply.style = "primary"
    
    markup.add(btn_accept, btn_reject)
    markup.add(btn_reply)
    return markup

# Главное меню
def main_menu():
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton("Новый стиль", callback_data="show_style")
    btn.style = "primary"
    markup.add(btn)
    return markup

# Команда старт
@bot.message_handler(commands=['start'])
def start(message):
    text = """Бот для приема карт

Отправь фото или скриншот, я перешлю админу."""
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# Показать новый стиль
@bot.callback_query_handler(func=lambda call: call.data == "show_style")
def show_style(call):
    text = """НОВЫЙ СТИЛЬ

ТАБЛИЦА:
| Тип | Статус |
|-----|--------|
| Карты | Работает |
| Фото | Работает |

ЧЕК-ЛИСТ:
- [x] Прием карт
- [x] Цветные кнопки
- [ ] Обновление

Просто отправь фото"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# Прием фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user = message.from_user
    user_id = user.id
    username = user.username or "нет"
    photo_id = message.photo[-1].file_id
    
    caption = f"Карта от @{username} (id: {user_id})"
    bot.send_photo(ADMIN_ID, photo_id, caption=caption)
    bot.send_message(ADMIN_ID, "Действия:", reply_markup=admin_buttons(user_id))
    
    bot.send_message(message.chat.id, "Карта отправлена админу")

# Обработка кнопок админа
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "show_style":
        return
    
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Не для тебя")
        return
    
    data = call.data
    
    if data.startswith("accept"):
        uid = int(data.split("_")[1])
        bot.send_message(call.message.chat.id, "Принято")
        bot.send_message(uid, "Твоя карта принята")
    
    elif data.startswith("reject"):
        uid = int(data.split("_")[1])
        bot.send_message(call.message.chat.id, "Отклонено")
        bot.send_message(uid, "Твоя карта отклонена")
    
    elif data.startswith("reply"):
        uid = int(data.split("_")[1])
        msg = bot.send_message(call.message.chat.id, "Напиши ответ:")
        bot.register_next_step_handler(msg, lambda m: reply_to_user(m, uid))
    
    bot.answer_callback_query(call.id)

def reply_to_user(message, user_id):
    bot.send_message(user_id, f"Ответ админа: {message.text}")
    bot.send_message(message.chat.id, "Ответ отправлен")

print("Бот запущен")
bot.infinity_polling()