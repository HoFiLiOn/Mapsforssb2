import logging
from aiogram import Bot, Dispatcher, executor, types

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
ADMIN_ID = 8388843828

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Хранилище для ответов
user_messages = {}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Отправь мне сообщение, и я перешлю его админу")

@dp.message_handler()
async def forward_to_admin(message: types.Message):
    user_id = message.from_user.id
    
    # Пересылаем админу
    forwarded = await message.forward(ADMIN_ID)
    
    # Сохраняем ID сообщения и пользователя
    user_messages[forwarded.message_id] = user_id
    
    await message.reply("Отправлено!")

@dp.message_handler()
async def reply_to_user(message: types.Message):
    # Проверяем что это админ и это ответ на сообщение
    if message.from_user.id != ADMIN_ID:
        return
    
    if not message.reply_to_message:
        return
    
    # Получаем ID пользователя
    msg_id = message.reply_to_message.message_id
    user_id = user_messages.get(msg_id)
    
    if user_id:
        if message.text:
            await bot.send_message(user_id, f"Ответ: {message.text}")
        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
        elif message.document:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption)
        
        await message.reply("Доставлено!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)