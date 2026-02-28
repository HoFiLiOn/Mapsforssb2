import logging
from aiogram import Bot, Dispatcher, executor, types
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
ADMIN_ID = 8388843828

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Хранилище для связи user_id и message_id
user_messages = {}

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("👋 Привет! Отправь мне сообщение, фото или файл, и я перешлю это админу.\nАдмин сможет ответить тебе прямо в чат.")

@dp.message_handler(content_types=['text', 'photo', 'document', 'video', 'audio', 'voice', 'animation', 'sticker'])
async def handle_user_message(message: types.Message):
    # Сохраняем связь: message_id пересланного сообщения -> user_id
    user_id = message.from_user.id
    
    # Пересылаем админу
    forwarded = await message.forward(ADMIN_ID)
    
    # Сохраняем в память
    user_messages[forwarded.message_id] = user_id
    
    await message.reply("✅ Сообщение отправлено администратору!")

@dp.message_handler()
async def handle_admin_reply(message: types.Message):
    # Проверяем, что сообщение от админа
    if message.from_user.id != ADMIN_ID:
        return
    
    # Проверяем, что это ответ на какое-то сообщение
    if not message.reply_to_message:
        await message.reply("ℹ️ Чтобы ответить пользователю, ответь на его пересланное сообщение")
        return
    
    # Получаем ID оригинального пересланного сообщения
    original_message_id = message.reply_to_message.message_id
    
    # Ищем пользователя в хранилище
    if original_message_id in user_messages:
        user_id = user_messages[original_message_id]
        
        try:
            # Отправляем ответ пользователю
            if message.text:
                await bot.send_message(user_id, f"📝 Ответ от администратора:\n{message.text}")
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=f"📝 Ответ от администратора:\n{message.caption or ''}")
            elif message.document:
                await bot.send_document(user_id, message.document.file_id, caption=f"📝 Ответ от администратора:\n{message.caption or ''}")
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=f"📝 Ответ от администратора:\n{message.caption or ''}")
            elif message.audio:
                await bot.send_audio(user_id, message.audio.file_id, caption=f"📝 Ответ от администратора:\n{message.caption or ''}")
            elif message.voice:
                await bot.send_voice(user_id, message.voice.file_id)
            elif message.sticker:
                await bot.send_sticker(user_id, message.sticker.file_id)
            elif message.animation:
                await bot.send_animation(user_id, message.animation.file_id, caption=f"📝 Ответ от администратора:\n{message.caption or ''}")
            
            await message.reply("✅ Ответ отправлен пользователю!")
        except Exception as e:
            logging.error(f"Ошибка при отправке ответа: {e}")
            await message.reply("❌ Не удалось отправить ответ. Возможно, пользователь заблокировал бота.")
    else:
        await message.reply("❌ Не удалось найти пользователя для этого сообщения")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)