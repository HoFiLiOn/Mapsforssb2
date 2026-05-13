import json
import random
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ---------- КОНФИГ ----------
TOKEN = "8709046161:AAGXiDMY_Z5VeCQ6366fUyyVOhrxTkTYysE"
ADMIN_ID = 7040677455

# ---------- ИНИЦИАЛИЗАЦИЯ ----------
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---------- JSON-БАЗА ----------
DB_FILE = "giveaways.json"

def load_data():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"giveaways": {}, "users": {}}  # giveaways: {id: {...}, users: {user_id: {wins: 0}}}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- СОСТОЯНИЯ ДЛЯ СОЗДАНИЯ РОЗЫГРЫША ----------
class GiveawayForm(StatesGroup):
    waiting_for_text = State()
    waiting_for_winners = State()
    waiting_for_time = State()

# ---------- КЛАВИАТУРЫ ----------
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 Создать розыгрыш", callback_data="create_giveaway")],
        [InlineKeyboardButton(text="📋 Активные розыгрыши", callback_data="active_giveaways")],
        [InlineKeyboardButton(text="🏆 Мои победы", callback_data="my_wins")]
    ])

def participate_keyboard(giveaway_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Участвовать!", callback_data=f"join_{giveaway_id}")],
        [InlineKeyboardButton(text="👥 Участники", callback_data=f"members_{giveaway_id}")]
    ])

# ---------- КОМАНДЫ ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎁 *Бот розыгрышей*\n\n"
        "Создавай розыгрыши, участвуй, побеждай!\n\n"
        "Используй кнопки ниже:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Только для админа")
    await message.answer(
        "🔧 *Админ-панель*\n\n"
        "/end [id] — завершить розыгрыш\n"
        "/cancel [id] — отменить розыгрыш\n"
        "/stats — статистика бота",
        parse_mode="Markdown"
    )

@dp.message(Command("end"))
async def cmd_end(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        giveaway_id = message.text.split()[1]
    except IndexError:
        return await message.answer("Использование: /end [id]")
    
    data = load_data()
    if giveaway_id not in data["giveaways"]:
        return await message.answer("❌ Розыгрыш не найден")
    
    await finish_giveaway(giveaway_id, data)

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        giveaway_id = message.text.split()[1]
    except IndexError:
        return await message.answer("Использование: /cancel [id]")
    
    data = load_data()
    if giveaway_id in data["giveaways"]:
        del data["giveaways"][giveaway_id]
        save_data(data)
        await message.answer(f"✅ Розыгрыш `{giveaway_id}` отменён", parse_mode="Markdown")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    active = len(data["giveaways"])
    total_users = len(data["users"])
    total_wins = sum(u.get("wins", 0) for u in data["users"].values())
    await message.answer(
        f"📊 *Статистика*\n\n"
        f"Активных розыгрышей: {active}\n"
        f"Всего пользователей: {total_users}\n"
        f"Всего побед: {total_wins}",
        parse_mode="Markdown"
    )

# ---------- CALLBACK-ОБРАБОТЧИКИ ----------
@dp.callback_query(F.data == "create_giveaway")
async def cb_create_giveaway(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("❌ Только админ может создавать розыгрыши", show_alert=True)
    await callback.message.answer(
        "✏️ Введите описание розыгрыша (поддерживается Markdown):"
    )
    await state.set_state(GiveawayForm.waiting_for_text)
    await callback.answer()

@dp.message(GiveawayForm.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    await message.answer("🔢 Сколько победителей выбрать?")
    await state.set_state(GiveawayForm.waiting_for_winners)

@dp.message(GiveawayForm.waiting_for_winners)
async def process_winners(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        return await message.answer("❌ Введи число больше 0")
    await state.update_data(winners=int(message.text))
    await message.answer("⏱ Через сколько минут завершить розыгрыш?")
    await state.set_state(GiveawayForm.waiting_for_time)

@dp.message(GiveawayForm.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        return await message.answer("❌ Введи число больше 0")
    
    minutes = int(message.text)
    data = await state.get_data()
    text = data["text"]
    winners_count = data["winners"]
    
    # Генерируем ID
    giveaway_id = f"gw_{int(datetime.now().timestamp())}"
    end_time = datetime.now() + timedelta(minutes=minutes)
    
    # Сохраняем
    db = load_data()
    db["giveaways"][giveaway_id] = {
        "text": text,
        "winners_count": winners_count,
        "end_time": end_time.isoformat(),
        "participants": [],
        "creator_id": message.from_user.id,
        "finished": False
    }
    save_data(db)
    
    # Отправляем пост с розыгрышем
    end_time_str = end_time.strftime("%d.%m.%Y %H:%M")
    post = await message.answer(
        f"🎉 *РОЗЫГРЫШ!*\n\n"
        f"{text}\n\n"
        f"🏆 Победителей: {winners_count}\n"
        f"⏳ Завершится: {end_time_str}\n"
        f"🆔 ID: `{giveaway_id}`",
        parse_mode="Markdown",
        reply_markup=participate_keyboard(giveaway_id)
    )
    
    await message.answer(f"✅ Розыгрыш создан! ID: `{giveaway_id}`", parse_mode="Markdown")
    await state.clear()
    
    # Запускаем таймер
    asyncio.create_task(giveaway_timer(giveaway_id, minutes * 60, post.chat.id, post.message_id))

@dp.callback_query(F.data.startswith("join_"))
async def cb_join_giveaway(callback: types.CallbackQuery):
    giveaway_id = callback.data.split("_", 1)[1]
    db = load_data()
    
    if giveaway_id not in db["giveaways"]:
        return await callback.answer("❌ Розыгрыш не найден", show_alert=True)
    
    gw = db["giveaways"][giveaway_id]
    if gw["finished"]:
        return await callback.answer("❌ Розыгрыш завершён", show_alert=True)
    
    user_id = callback.from_user.id
    if user_id in gw["participants"]:
        return await callback.answer("⚠️ Ты уже участвуешь!", show_alert=True)
    
    gw["participants"].append(user_id)
    
    # Обновляем статистику юзера
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {"wins": 0}
    
    save_data(db)
    
    await callback.answer("✅ Ты в игре! Жди результатов")
    
    # Обновляем счётчик в кнопке
    new_markup = callback.message.reply_markup
    for row in new_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data.startswith("members_"):
                btn.text = f"👥 Участники ({len(gw['participants'])})"
    
    await callback.message.edit_reply_markup(reply_markup=new_markup)

@dp.callback_query(F.data.startswith("members_"))
async def cb_members(callback: types.CallbackQuery):
    giveaway_id = callback.data.split("_", 1)[1]
    db = load_data()
    gw = db["giveaways"].get(giveaway_id)
    if not gw:
        return await callback.answer("❌ Розыгрыш не найден", show_alert=True)
    
    count = len(gw["participants"])
    await callback.answer(f"👥 Участников: {count}", show_alert=True)

@dp.callback_query(F.data == "active_giveaways")
async def cb_active_giveaways(callback: types.CallbackQuery):
    db = load_data()
    active = {k: v for k, v in db["giveaways"].items() if not v["finished"]}
    
    if not active:
        return await callback.answer("Нет активных розыгрышей", show_alert=True)
    
    text = "📋 *Активные розыгрыши:*\n\n"
    for gid, gw in active.items():
        end = datetime.fromisoformat(gw["end_time"]).strftime("%H:%M")
        text += f"• `{gid}` — {gw['participants']} уч. (до {end})\n"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "my_wins")
async def cb_my_wins(callback: types.CallbackQuery):
    db = load_data()
    user = db["users"].get(str(callback.from_user.id), {"wins": 0})
    wins = user["wins"]
    await callback.answer(f"🏆 Твоих побед: {wins}", show_alert=True)

# ---------- ЛОГИКА РОЗЫГРЫША ----------
async def giveaway_timer(giveaway_id: str, seconds: int, chat_id: int, message_id: int):
    await asyncio.sleep(seconds)
    
    db = load_data()
    if giveaway_id not in db["giveaways"]:
        return
    
    gw = db["giveaways"][giveaway_id]
    if gw["finished"]:
        return
    
    await finish_giveaway(giveaway_id, db, chat_id, message_id)

async def finish_giveaway(giveaway_id: str, db: dict, chat_id: int = None, message_id: int = None):
    gw = db["giveaways"][giveaway_id]
    gw["finished"] = True
    participants = gw["participants"]
    winners_count = min(gw["winners_count"], len(participants))
    
    if participants and winners_count > 0:
        winners = random.sample(participants, winners_count)
        for w in winners:
            if str(w) in db["users"]:
                db["users"][str(w)]["wins"] += 1
    else:
        winners = []
    
    save_data(db)
    
    # Формируем текст результатов
    winners_mentions = ", ".join([f"[{w}](tg://user?id={w})" for w in winners]) if winners else "Никто не участвовал 😢"
    
    result_text = (
        f"🎉 *РОЗЫГРЫШ ЗАВЕРШЁН!*\n\n"
        f"{gw['text']}\n\n"
        f"🏆 *Победители ({winners_count}):*\n"
        f"{winners_mentions}\n\n"
        f"🆔 `{giveaway_id}`"
    )
    
    # Если есть chat_id — редактируем исходное сообщение
    if chat_id and message_id:
        try:
            await bot.edit_message_text(
                result_text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="Markdown"
            )
        except:
            # Если не можем отредактировать — шлём новым
            await bot.send_message(chat_id, result_text, parse_mode="Markdown")
    
    # Уведомляем победителей в личку
    for winner_id in winners:
        try:
            await bot.send_message(
                winner_id,
                f"🎉 Поздравляем! Ты победил в розыгрыше!\n\n{gw['text']}\n\n🆔 `{giveaway_id}`",
                parse_mode="Markdown"
            )
        except:
            pass  # Юзер мог заблокировать бота

# ---------- ЗАПУСК ----------
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
