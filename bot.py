import requests
import time
import json

# ============= ВАШИ ДАННЫЕ =============
BOT_TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
ADMIN_ID = 7040677455
# =======================================

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0

# Временное хранилище для ответов админа
reply_storage = {}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "MarkdownV2"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{API_URL}/sendMessage", json=data)

def send_photo(chat_id, photo_id, caption=""):
    requests.post(f"{API_URL}/sendPhoto", json={
        "chat_id": chat_id,
        "photo": photo_id,
        "caption": caption,
        "parse_mode": "MarkdownV2"
    })

def send_document(chat_id, doc_id, caption=""):
    requests.post(f"{API_URL}/sendDocument", json={
        "chat_id": chat_id,
        "document": doc_id,
        "caption": caption,
        "parse_mode": "MarkdownV2"
    })

def send_start_menu(chat_id):
    text = """# 🎯 Бот\-предложка

Привет\! Готов принять твои материалы\.

## Что можно отправлять:
| Тип | Статус |
|-----|--------|
| Текст | ✅ |
| Фото | ✅ |
| Файлы | ✅ |

## Как это работает:
1. Отправляешь файл или текст
2. Админ получает уведомление
3. Админ может ответить тебе

\- \[x\] Анонимно
\- \[x\] 24/7
\- \[x\] Быстро

Просто отправь сообщение 👇"""
    send_message(chat_id, text)

def escape_md(text):
    """Экранирование спецсимволов для MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def process_message(update):
    global last_update_id
    last_update_id = update.get("update_id", last_update_id)
    
    message = update.get("message")
    if not message:
        return
    
    chat_id = message["chat"]["id"]
    user = message.get("from", {})
    user_id = user.get("id")
    username = user.get("username", "нет")
    
    # Обработка ответа от админа
    if user_id == ADMIN_ID and chat_id == ADMIN_ID and reply_storage.get("waiting_for_reply"):
        target_user = reply_storage.pop("waiting_for_reply", None)
        if target_user and message.get("text"):
            reply_text = escape_md(message["text"])
            send_message(target_user, f"📨 **Ответ админа:**\n\n{reply_text}")
            send_message(ADMIN_ID, "✅ Ответ отправлен пользователю\!")
        return
    
    # Команда /start
    if message.get("text") == "/start":
        send_start_menu(chat_id)
        return
    
    # Если сообщение от обычного пользователя (не админа)
    if user_id != ADMIN_ID:
        username_str = f"@{username}" if username != "нет" else "нет username"
        user_text = message.get("text", "")
        
        if user_text:
            # Текстовое сообщение
            admin_msg = f"""# 📬 Новое сообщение

| Поле | Значение |
|------|----------|
| 👤 | {username_str} |
| 🆔 | `{user_id}` |
| 📝 | {escape_md(user_text[:200])} |

\- \[ \] Требует ответа"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "✏️ Ответить", "callback_data": f"reply_{user_id}"}]
                ]
            }
            send_message(ADMIN_ID, admin_msg, keyboard)
            send_message(chat_id, "✅ Отправлено админу\!")
        
        elif message.get("photo"):
            # Фото
            photo = message["photo"][-1]
            photo_id = photo["file_id"]
            caption = message.get("caption", "")
            
            admin_msg = f"""# 🖼️ Новое фото

| Поле | Значение |
|------|----------|
| 👤 | {username_str} |
| 🆔 | `{user_id}` |
| 📝 | {escape_md(caption[:100])} |"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "✏️ Ответить", "callback_data": f"reply_{user_id}"}]
                ]
            }
            send_photo(ADMIN_ID, photo_id, admin_msg)
            send_message(ADMIN_ID, "", keyboard)  # Отправляем кнопки отдельно
            send_message(chat_id, "✅ Фото отправлено\!")
        
        elif message.get("document"):
            # Документ
            doc = message["document"]
            doc_id = doc["file_id"]
            file_name = doc.get("file_name", "файл")
            caption = message.get("caption", "")
            
            admin_msg = f"""# 📎 Новый файл

| Поле | Значение |
|------|----------|
| 👤 | {username_str} |
| 🆔 | `{user_id}` |
| 📄 | {escape_md(file_name)} |
| 📝 | {escape_md(caption[:100])} |"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "✏️ Ответить", "callback_data": f"reply_{user_id}"}]
                ]
            }
            send_document(ADMIN_ID, doc_id, admin_msg)
            send_message(ADMIN_ID, "", keyboard)
            send_message(chat_id, "✅ Файл отправлен\!")
        
        else:
            send_message(chat_id, "❌ Неподдерживаемый тип сообщения")

def process_callback(callback_query):
    data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    
    if data.startswith("reply_"):
        user_id = int(data.split("_")[1])
        reply_storage["waiting_for_reply"] = user_id
        send_message(chat_id, "✏️ **Введите ответ для пользователя:**", parse_mode="MarkdownV2")

def main():
    global last_update_id
    print("✅ Бот запущен!")
    
    while True:
        try:
            response = requests.get(f"{API_URL}/getUpdates", params={
                "offset": last_update_id + 1,
                "timeout": 30
            })
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    if "callback_query" in update:
                        process_callback(update["callback_query"])
                    else:
                        process_message(update)
                    last_update_id = update["update_id"]
            
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()