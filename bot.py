import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ============= ВАШИ ДАННЫЕ =============
BOT_TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
ADMIN_ID = 7040677455
# =======================================

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Хранилище для ответов (в памяти)
user_data_store = {}

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ============= КОМАНДЫ =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = """# 🎯 Бот-предложка

Привет, готов принять твои материалы!

## Что можно отправлять:
| Тип | Статус |
|-----|--------|
| Текст | ✅ |
| Фото | ✅ |
| Файлы | ✅ |
| Видео | ✅ |

## Как это работает:
1. Отправляешь мне файл/текст
2. Админ получает уведомление
3. Админ может ответить тебе

- [x] Анонимно
- [x] 24/7
- [x] Быстро

Просто отправь сообщение 👇"""
    
    await update.message.reply_text(text, parse_mode="MarkdownV2")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """**📖 Помощь**

Отправь любой файл, фото или текст — всё дойдёт до админа.

**Статусы:**
`✅` — принято
`⏳` — в обработке
`❌` — отклонено"""
    await update.message.reply_text(text, parse_mode="MarkdownV2")

# ============= ПРИЕМ ОТ ПОЛЬЗОВАТЕЛЕЙ =============
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Если админ отвечает пользователю
    if is_admin(user.id) and context.user_data.get("reply_to"):
        user_id = context.user_data["reply_to"]
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📨 **Ответ админа:**\n\n{update.message.text}",
            parse_mode="MarkdownV2"
        )
        await update.message.reply_text("✅ Ответ отправлен!")
        del context.user_data["reply_to"]
        return
    
    # Обычный пользователь → пересылаем админу
    if not is_admin(user.id):
        msg = f"""# 📬 Новое сообщение

| Поле | Значение |
|------|----------|
| 👤 | @{user.username or 'нет username'} |
| 🆔 | `{user.id}` |
| 📝 | {update.message.text[:200]} |

- [ ] Требует ответа
"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Ответить", callback_data=f"reply_{user.id}")]
        ])
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
        await update.message.reply_text("✅ Отправлено админу!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    caption = update.message.caption or "Без описания"
    
    msg = f"""# 🖼️ Новое фото

| Поле | Значение |
|------|----------|
| 👤 | @{user.username or 'нет'} |
| 🆔 | `{user.id}` |
| 📝 | {caption} |
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Ответить", callback_data=f"reply_{user.id}")]
    ])
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption=msg,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
    await update.message.reply_text("✅ Фото отправлено!")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document
    caption = update.message.caption or "Без описания"
    
    msg = f"""# 📎 Новый файл

| Поле | Значение |
|------|----------|
| 👤 | @{user.username or 'нет'} |
| 🆔 | `{user.id}` |
| 📄 | {doc.file_name} |
| 📝 | {caption} |
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Ответить", callback_data=f"reply_{user.id}")]
    ])
    
    await context.bot.send_document(
        chat_id=ADMIN_ID,
        document=doc.file_id,
        caption=msg,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
    await update.message.reply_text("✅ Файл отправлен!")

# ============= КНОПКИ АДМИНА =============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("reply_"):
        user_id = int(query.data.split("_")[1])
        context.user_data["reply_to"] = user_id
        await query.message.reply_text("✏️ **Введите ответ для пользователя:**", parse_mode="MarkdownV2")
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✏️ *Ожидает ответа...*",
            parse_mode="MarkdownV2"
        )

# ============= ЗАПУСК =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Обработчики
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()