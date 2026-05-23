import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

TOKEN = "8786399001:AAF2GODnsIrCluHiFPH8XYC8uVMuPrDiSss"
ADMIN_ID = 7040677455

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище пользователей
users = {}  # {user_id: {"name": ..., "username": ..., "first_date": ...}}
applications = []  # [{user_id, name, age, contact, skills, experience, about, date, status}]

class Form(StatesGroup):
    name = State()
    age = State()
    contact = State()
    skills = State()
    experience = State()
    about = State()

# Клавиатуры
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Подать заявку", callback_data="apply")
    kb.button(text="ℹ️ О проекте", callback_data="about")
    kb.adjust(1)
    return kb.as_markup()

def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Статистика", callback_data="admin_stats")
    kb.button(text="📋 Заявки", callback_data="admin_applications")
    kb.button(text="👥 Пользователи", callback_data="admin_users")
    kb.button(text="📤 Экспорт", callback_data="admin_export")
    kb.adjust(2)
    return kb.as_markup()

def skills_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск информации", callback_data="skill_search")
    kb.button(text="✅ Проверка фактов", callback_data="skill_facts")
    kb.button(text="✍️ Написание текстов", callback_data="skill_write")
    kb.button(text="🪲 Тестирование", callback_data="skill_test")
    kb.button(text="🌍 Перевод", callback_data="skill_translate")
    kb.button(text="🎨 Дизайн", callback_data="skill_design")
    kb.button(text="Готово ✅", callback_data="skill_done")
    kb.adjust(2)
    return kb.as_markup()

# Старт
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "first_date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
    
    await message.answer(
        f"<b>👋 Привет, {message.from_user.full_name}!</b>\n\n"
        "Я бот для набора в команду <b>SSB2 Archives</b>.\n"
        "Помогай проекту выбираться из бета-версии!",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# О проекте
@dp.callback_query(lambda c: c.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "<b>ℹ️ О проекте</b>\n\n"
        "<b>SSB2 Archives</b> — неофициальный сайт-архив по игре Simple Sandbox 2.\n\n"
        "<b>Что ищем:</b>\n"
        "🔍 Тех, кто найдёт новые пасхалки и факты\n"
        "✍️ Авторов для гайдов и описаний\n"
        "🪲 Тестировщиков сайта\n"
        "🌍 Переводчиков\n\n"
        "<b>Создатель:</b> @HoFiLiOnclkc",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# Начало анкеты
@dp.callback_query(lambda c: c.data == "apply")
async def apply_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>📝 Заявка в команду</b>\n\nДавай заполним анкету. Как тебя зовут (ник или имя)?",
        parse_mode="HTML"
    )
    await state.set_state(Form.name)

# Имя
@dp.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

# Возраст
@dp.message(Form.age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Твой Telegram для связи (или Discord)?")
    await state.set_state(Form.contact)

# Контакт
@dp.message(Form.contact)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await message.answer(
        "<b>Что умеешь?</b>\nВыбери навыки (можно несколько):",
        reply_markup=skills_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Form.skills)

# Навыки (обработка callback)
selected_skills = {}

@dp.callback_query(lambda c: c.data.startswith("skill_") and c.data != "skill_done")
async def skill_select(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    skill_map = {
        "skill_search": "🔍 Поиск информации",
        "skill_facts": "✅ Проверка фактов",
        "skill_write": "✍️ Написание текстов",
        "skill_test": "🪲 Тестирование",
        "skill_translate": "🌍 Перевод",
        "skill_design": "🎨 Дизайн"
    }
    
    skill = skill_map.get(callback.data)
    if user_id not in selected_skills:
        selected_skills[user_id] = []
    
    if skill in selected_skills[user_id]:
        selected_skills[user_id].remove(skill)
    else:
        selected_skills[user_id].append(skill)
    
    skills_text = ", ".join(selected_skills[user_id]) if selected_skills[user_id] else "не выбраны"
    await callback.answer(f"Выбрано: {skills_text}")

@dp.callback_query(lambda c: c.data == "skill_done")
async def skill_done(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    skills = ", ".join(selected_skills.get(user_id, []))
    await state.update_data(skills=skills if skills else "Не выбрано")
    selected_skills.pop(user_id, None)
    
    await callback.message.edit_text(
        "<b>Твой опыт в Simple Sandbox 2</b>\n\nНапиши, как давно играешь и в каких режимах:",
        parse_mode="HTML"
    )
    await state.set_state(Form.experience)

# Опыт
@dp.message(Form.experience)
async def get_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer(
        "<b>Последний шаг!</b>\n\nРасскажи о себе: почему хочешь помогать, какие идеи есть для проекта?",
        parse_mode="HTML"
    )
    await state.set_state(Form.about)

# Финал
@dp.message(Form.about)
async def get_about(message: types.Message, state: FSMContext):
    await state.update_data(about=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    
    application = {
        "user_id": user_id,
        "name": data["name"],
        "age": data["age"],
        "contact": data["contact"],
        "skills": data["skills"],
        "experience": data["experience"],
        "about": data["about"],
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "⏳ На рассмотрении"
    }
    applications.append(application)
    
    # Формируем сообщение админу
    admin_msg = (
        f"<b>📩 НОВАЯ ЗАЯВКА</b>\n"
        f"├ <b>Имя:</b> {data['name']}\n"
        f"├ <b>Возраст:</b> {data['age']}\n"
        f"├ <b>Контакт:</b> {data['contact']}\n"
        f"├ <b>Навыки:</b> {data['skills']}\n"
        f"├ <b>Опыт в SSB2:</b> {data['experience']}\n"
        f"├ <b>О себе:</b> {data['about']}\n"
        f"└ <b>Дата:</b> {application['date']}"
    )
    
    # Кнопки админа
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Принять", callback_data=f"accept_{len(applications)-1}")
    kb.button(text="❌ Отклонить", callback_data=f"reject_{len(applications)-1}")
    kb.adjust(2)
    
    await bot.send_message(ADMIN_ID, admin_msg, reply_markup=kb.as_markup(), parse_mode="HTML")
    
    await message.answer(
        "<b>✅ Заявка отправлена!</b>\n\n"
        "Я свяжусь с тобой в ближайшее время.\n"
        "Спасибо, что хочешь помочь проекту! 🔥",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await state.clear()

# Админ-команда
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "<b>⚙️ Админ-панель</b>",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )

# Статистика
@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Нет доступа")
    
    total_users = len(users)
    total_apps = len(applications)
    pending = sum(1 for a in applications if a["status"] == "⏳ На рассмотрении")
    accepted = sum(1 for a in applications if a["status"] == "✅ Принят")
    rejected = sum(1 for a in applications if a["status"] == "❌ Отклонён")
    
    await callback.message.edit_text(
        f"<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"📩 Заявок всего: <b>{total_apps}</b>\n"
        f"⏳ На рассмотрении: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

# Список заявок
@dp.callback_query(lambda c: c.data == "admin_applications")
async def admin_applications(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Нет доступа")
    
    if not applications:
        return await callback.message.edit_text("Заявок пока нет.", reply_markup=admin_menu())
    
    text = "<b>📋 Заявки</b>\n\n"
    for i, app in enumerate(applications[-10:]):
        text += f"{app['status']} | {app['name']} | {app['date']}\n"
    
    await callback.message.edit_text(text, reply_markup=admin_menu(), parse_mode="HTML")

# Список пользователей
@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Нет доступа")
    
    if not users:
        return await callback.message.edit_text("Пользователей пока нет.", reply_markup=admin_menu())
    
    text = "<b>👥 Пользователи</b>\n\n"
    for uid, data in list(users.items())[-10:]:
        text += f"• {data['username']} | {data['first_date']}\n"
    
    await callback.message.edit_text(text, reply_markup=admin_menu(), parse_mode="HTML")

# Экспорт
@dp.callback_query(lambda c: c.data == "admin_export")
async def admin_export(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Нет доступа")
    
    if not applications:
        return await callback.message.edit_text("Нечего экспортировать.", reply_markup=admin_menu())
    
    text = "Имя;Возраст;Контакт;Навыки;Опыт;О себе;Дата;Статус\n"
    for app in applications:
        text += f"{app['name']};{app['age']};{app['contact']};{app['skills']};{app['experience']};{app['about']};{app['date']};{app['status']}\n"
    
    with open("export.csv", "w", encoding="utf-8") as f:
        f.write(text)
    
    await bot.send_document(ADMIN_ID, types.FSInputFile("export.csv"), caption="📤 Экспорт заявок")
    await callback.message.edit_text("Экспорт отправлен в личку!", reply_markup=admin_menu())

# Принять / отклонить
@dp.callback_query(lambda c: c.data.startswith("accept_") or c.data.startswith("reject_"))
async def handle_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Нет доступа")
    
    action, index = callback.data.split("_")
    index = int(index)
    
    if index >= len(applications):
        return await callback.answer("Заявка не найдена")
    
    if action == "accept":
        applications[index]["status"] = "✅ Принят"
        await callback.answer("Заявка принята ✅")
    else:
        applications[index]["status"] = "❌ Отклонён"
        await callback.answer("Заявка отклонена ❌")
    
    await callback.message.edit_reply_markup(reply_markup=None)

# Запуск
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())