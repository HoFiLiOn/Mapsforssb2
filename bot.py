import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8786399001:AAF2GODnsIrCluHiFPH8XYC8uVMuPrDiSss"
ADMIN_ID = 7040677455

# Состояния
NAME, AGE, CONTACT, SKILLS, EXPERIENCE, ABOUT = range(6)

# Хранилище
users = {}
applications = []
temp_skills = {}

# Клавиатуры
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📝 Подать заявку", callback_data="apply")],
        [InlineKeyboardButton("ℹ️ О проекте", callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton("📋 Заявки", callback_data="admin_apps")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
         InlineKeyboardButton("📤 Экспорт", callback_data="admin_export")]
    ]
    return InlineKeyboardMarkup(keyboard)

def skills_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск информации", callback_data="skill_search")],
        [InlineKeyboardButton("✅ Проверка фактов", callback_data="skill_facts")],
        [InlineKeyboardButton("✍️ Написание текстов", callback_data="skill_write")],
        [InlineKeyboardButton("🪲 Тестирование", callback_data="skill_test")],
        [InlineKeyboardButton("🌍 Перевод", callback_data="skill_translate")],
        [InlineKeyboardButton("🎨 Дизайн", callback_data="skill_design")],
        [InlineKeyboardButton("Готово ✅", callback_data="skill_done")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name
    
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "first_date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
    
    await update.message.reply_text(
        f"<b>👋 Привет, {update.effective_user.full_name}!</b>\n\n"
        "Я бот для набора в команду <b>SSB2 Archives</b>.\n"
        "Помогай проекту выбираться из бета-версии!",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# О проекте
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
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
async def apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    await query.message.answer(
        "<b>📝 Заявка в команду</b>\n\nДавай заполним анкету. Как тебя зовут (ник или имя)?",
        parse_mode="HTML"
    )
    return NAME

# Имя
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Сколько тебе лет?")
    return AGE

# Возраст
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Твой Telegram для связи (или Discord)?")
    return CONTACT

# Контакт
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    temp_skills[update.effective_user.id] = []
    await update.message.reply_text(
        "<b>Что умеешь?</b>\nВыбери навыки (можно несколько):",
        reply_markup=skills_menu(update.effective_user.id),
        parse_mode="HTML"
    )
    return SKILLS

# Навыки
async def skill_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    skill_map = {
        "skill_search": "🔍 Поиск информации",
        "skill_facts": "✅ Проверка фактов",
        "skill_write": "✍️ Написание текстов",
        "skill_test": "🪲 Тестирование",
        "skill_translate": "🌍 Перевод",
        "skill_design": "🎨 Дизайн"
    }
    
    skill = skill_map.get(query.data)
    if skill in temp_skills.get(user_id, []):
        temp_skills[user_id].remove(skill)
    else:
        temp_skills[user_id].append(skill)
    
    skills_text = ", ".join(temp_skills[user_id]) if temp_skills[user_id] else "не выбраны"
    await query.answer(f"Выбрано: {skills_text}")

async def skill_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    context.user_data["skills"] = ", ".join(temp_skills.get(user_id, [])) or "Не выбрано"
    temp_skills.pop(user_id, None)
    
    await query.message.edit_text(
        "<b>Твой опыт в Simple Sandbox 2</b>\n\nНапиши, как давно играешь и в каких режимах:",
        parse_mode="HTML"
    )
    return EXPERIENCE

# Опыт
async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text
    await update.message.reply_text(
        "<b>Последний шаг!</b>\n\nРасскажи о себе: почему хочешь помогать, какие идеи есть для проекта?",
        parse_mode="HTML"
    )
    return ABOUT

# Финал
async def get_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["about"] = update.message.text
    user_id = update.effective_user.id
    data = context.user_data
    
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
    
    admin_msg = (
        f"<b>📩 НОВАЯ ЗАЯВКА</b>\n"
        f"├ <b>Имя:</b> {data['name']}\n"
        f"├ <b>Возраст:</b> {data['age']}\n"
        f"├ <b>Контакт:</b> {data['contact']}\n"
        f"├ <b>Навыки:</b> {data['skills']}\n"
        f"├ <b>Опыт:</b> {data['experience']}\n"
        f"├ <b>О себе:</b> {data['about']}\n"
        f"└ <b>Дата:</b> {application['date']}"
    )
    
    idx = len(applications) - 1
    keyboard = [
        [InlineKeyboardButton("✅ Принять", callback_data=f"accept_{idx}"),
         InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{idx}")]
    ]
    
    await context.bot.send_message(ADMIN_ID, admin_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    
    await update.message.reply_text(
        "<b>✅ Заявка отправлена!</b>\n\nЯ свяжусь с тобой. Спасибо! 🔥",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    return ConversationHandler.END

# Админка
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "<b>⚙️ Админ-панель</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        return await query.answer("⛔ Нет доступа")
    await query.answer()
    
    total_users = len(users)
    total_apps = len(applications)
    pending = sum(1 for a in applications if a["status"] == "⏳ На рассмотрении")
    accepted = sum(1 for a in applications if a["status"] == "✅ Принят")
    rejected = sum(1 for a in applications if a["status"] == "❌ Отклонён")
    
    await query.message.edit_text(
        f"<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"📩 Заявок всего: <b>{total_apps}</b>\n"
        f"⏳ На рассмотрении: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

async def admin_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        return await query.answer("⛔ Нет доступа")
    await query.answer()
    
    if not applications:
        return await query.message.edit_text("Заявок пока нет.", reply_markup=admin_menu())
    
    text = "<b>📋 Заявки</b>\n\n"
    for app in applications[-10:]:
        text += f"{app['status']} | {app['name']} | {app['date']}\n"
    
    await query.message.edit_text(text, reply_markup=admin_menu(), parse_mode="HTML")

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        return await query.answer("⛔ Нет доступа")
    await query.answer()
    
    if not users:
        return await query.message.edit_text("Пользователей пока нет.", reply_markup=admin_menu())
    
    text = "<b>👥 Пользователи</b>\n\n"
    for uid, data in list(users.items())[-10:]:
        text += f"• {data['username']} | {data['first_date']}\n"
    
    await query.message.edit_text(text, reply_markup=admin_menu(), parse_mode="HTML")

async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        return await query.answer("⛔ Нет доступа")
    await query.answer()
    
    if not applications:
        return await query.message.edit_text("Нечего экспортировать.", reply_markup=admin_menu())
    
    text = "Имя;Возраст;Контакт;Навыки;Опыт;О себе;Дата;Статус\n"
    for app in applications:
        text += f"{app['name']};{app['age']};{app['contact']};{app['skills']};{app['experience']};{app['about']};{app['date']};{app['status']}\n"
    
    with open("export.csv", "w", encoding="utf-8") as f:
        f.write(text)
    
    await context.bot.send_document(ADMIN_ID, open("export.csv", "rb"), caption="📤 Экспорт заявок")
    await query.message.edit_text("Экспорт отправлен в личку!", reply_markup=admin_menu())

async def handle_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        return await query.answer("⛔ Нет доступа")
    
    action, index = query.data.split("_")
    index = int(index)
    
    if index >= len(applications):
        return await query.answer("Заявка не найдена")
    
    if action == "accept":
        applications[index]["status"] = "✅ Принят"
        await query.answer("✅ Принято")
    else:
        applications[index]["status"] = "❌ Отклонён"
        await query.answer("❌ Отклонено")
    
    await query.message.edit_reply_markup(reply_markup=None)

# Выход из анкеты
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено", reply_markup=main_menu())
    return ConversationHandler.END

# Запуск
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Анкета
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(apply, "apply")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            SKILLS: [
                CallbackQueryHandler(skill_select, pattern="^skill_(?!done)"),
                CallbackQueryHandler(skill_done, pattern="^skill_done$")
            ],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_about)]
        },
        fallbacks=[Command("cancel", cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(about, "about"))
    app.add_handler(CallbackQueryHandler(admin_stats, "admin_stats"))
    app.add_handler(CallbackQueryHandler(admin_applications, "admin_apps"))
    app.add_handler(CallbackQueryHandler(admin_users_list, "admin_users"))
    app.add_handler(CallbackQueryHandler(admin_export, "admin_export"))
    app.add_handler(CallbackQueryHandler(handle_decision, pattern="^(accept|reject)_"))
    app.add_handler(conv_handler)
    
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()