import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# Вставь сюда свой токен из BotFather
API_TOKEN = 8376850903:AAEvWNLCJTA2U_Yblx271ov5JYzGsxA5IJg

# Настройка логирования (чтобы видеть ошибки в консоли)
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. Обработчик команды /start
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я Эхо-бот. Напиши мне что-нибудь, и я повторю.")

# 2. Обработчик всех остальных текстовых сообщений
@dp.message()
async def echo(message: types.Message):
    # Просто отправляем обратно тот же текст, который пришел
    await message.answer(message.text)

# 3. Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())