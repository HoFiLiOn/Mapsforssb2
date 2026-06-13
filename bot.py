import requests
import time
import json

BOT_TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
ADMIN_ID = 7040677455

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0

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

# Цветные кнопки для админа
def get_color_buttons(user_id):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Принять", "callback_data": f"accept_{user_id}", "style": "success"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{user_id}", "style": "danger"}
            ],
            [
                {"text": "✏️ Ответить", "callback_data": f"reply_{user_id}", "style": "primary"}
            ]
        ]
    }

# Новый стиль с таблицами и чек-листами
def new_style_menu(chat_id):
    text = r"""# 🎯 Бот для приёма карт

Отправь мне карту или скриншот

## Статус приёма
| Тип | Приём |
|-----|-------|
| Карты | ✅ |
| Скриншоты | ✅ |
| Фото | ✅ |

## Список задач
- [x] Принимаем карты
- [x] Цветные кнопки
- [ ] Обновить клиент Telegram

<details>
<summary>📌 Как отправить карту</summary>

1. Нажми на скрепку
2. Выбери фото
3. Отправь

</details>

Просто отправь изображение 👇"""
    send_message(chat_id, text, {
        "inline_keyboard": [
            [{"text": "📤 Отправить карту", "callback_data": "send_card"}]
        ]
    })

def start(chat_id):
    new_style_menu(chat_id)

def send_to_admin(user_id, username, photo_id):
    name = f"@{username}" if username else f"id{user_id}"
    caption = f"Новая карта от {name}"
    send_photo(ADMIN_ID, photo_id, caption)
    send_message(ADMIN_ID, "Выбери действие:", get_color_buttons(user_id))

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    username = msg["from"].get("username", "")
    text = msg.get("text", "")

    if text == "/start":
        start(chat_id)
        return

    if msg.get("photo"):
        photo_id = msg["photo"][-1]["file_id"]
        send_to_admin(user_id, username, photo_id)
        send_message(chat_id, "✅ Карта отправлена админу")
    else:
        send_message(chat_id, "❌ Отправь фото или скриншот")

def handle_callback(cb):
    data = cb.get("data", "")
    from_id = cb["from"]["id"]
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")

    if data == "send_card":
        send_message(chat_id, "📤 Отправь фото или скриншот")
        return

    if from_id != ADMIN_ID:
        return

    if data.startswith("accept_"):
        uid = int(data.split("_")[1])
        send_message(chat_id, "✅ Принято")
        send_message(uid, "✅ Твоя карта принята")
    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])
        send_message(chat_id, "❌ Отклонено")
        send_message(uid, "❌ Твоя карта отклонена")
    elif data.startswith("reply_"):
        uid = int(data.split("_")[1])
        send_message(chat_id, "✏️ Напиши ответ, я отправлю")
        send_message(uid, "📨 Админ скоро ответит")

def main():
    global last_update_id
    print("Бот запущен")

    while True:
        try:
            resp = requests.get(f"{API_URL}/getUpdates", params={
                "offset": last_update_id + 1,
                "timeout": 30
            })
            data = resp.json()

            if data.get("ok") and data.get("result"):
                for upd in data["result"]:
                    if "callback_query" in upd:
                        handle_callback(upd["callback_query"])
                    elif "message" in upd:
                        handle_message(upd["message"])
                    last_update_id = upd["update_id"]

            time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()