import requests
import json
import time

BOT_TOKEN = "8649154788:AAFBV_80D5A4SuHPP7IrplC25ALSW-3GqKo"
ADMIN_ID = 7040677455

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0

def send_rich_message(chat_id, text_blocks):
    payload = {
        "chat_id": chat_id,
        "rich_message": {
            "blocks": text_blocks
        }
    }
    response = requests.post(f"{API_URL}/sendRichMessage", json=payload)
    return response.json()

def send_photo(chat_id, photo_id, caption=""):
    requests.post(f"{API_URL}/sendPhoto", json={
        "chat_id": chat_id,
        "photo": photo_id,
        "caption": caption
    })

def send_message(chat_id, text):
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def start_blocks():
    return [
        {
            "type": "heading",
            "level": 1,
            "children": [{"type": "text", "text": "🎯 Бот для приема карт"}]
        },
        {
            "type": "paragraph",
            "children": [{"type": "text", "text": "Отправь мне фото или скриншот, я перешлю админу."}]
        },
        {
            "type": "table",
            "rows": [
                {"cells": [
                    {"children": [{"type": "text", "text": "Тип"}]},
                    {"children": [{"type": "text", "text": "Статус"}]}
                ]},
                {"cells": [
                    {"children": [{"type": "text", "text": "Карты"}]},
                    {"children": [{"type": "text", "text": "✅ Прием"}]}
                ]},
                {"cells": [
                    {"children": [{"type": "text", "text": "Фото"}]},
                    {"children": [{"type": "text", "text": "✅ Прием"}]}
                ]}
            ]
        },
        {
            "type": "list",
            "items": [
                {"type": "list_item", "checked": True, "children": [{"type": "text", "text": "Бот запущен"}]},
                {"type": "list_item", "checked": True, "children": [{"type": "text", "text": "Прием карт работает"}]},
                {"type": "list_item", "checked": False, "children": [{"type": "text", "text": "Ожидание ответа"}]}
            ]
        },
        {
            "type": "details",
            "summary": "📌 Как отправить карту",
            "blocks": [
                {
                    "type": "paragraph",
                    "children": [{"type": "text", "text": "1. Нажми на скрепку\n2. Выбери фото\n3. Отправь"}]
                }
            ]
        }
    ]

def admin_buttons(user_id):
    return {
        "inline_keyboard": [
            [
                {"text": "Принять", "callback_data": f"accept_{user_id}"},
                {"text": "Отклонить", "callback_data": f"reject_{user_id}"}
            ],
            [{"text": "Ответить", "callback_data": f"reply_{user_id}"}]
        ]
    }

def process_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("username", "нет")
    
    # /start
    if message.get("text") == "/start":
        send_rich_message(chat_id, start_blocks())
        return
    
    # Фото
    if message.get("photo"):
        photo_id = message["photo"][-1]["file_id"]
        
        # Админу с кнопками
        send_photo(ADMIN_ID, photo_id, f"Новая карта от @{username} (id: {user_id})")
        send_message(ADMIN_ID, "Действия:")
        # Кнопки отправляем отдельным сообщением (пока API не поддерживает reply_markup в sendRichMessage)
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": ADMIN_ID,
            "text": "Выбери действие:",
            "reply_markup": admin_buttons(user_id)
        })
        
        send_message(chat_id, "Карта отправлена админу")
        return
    
    send_message(chat_id, "Отправь фото")

def process_callback(call):
    user_id = call["from"]["id"]
    data = call["data"]
    message = call.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    
    if user_id != ADMIN_ID:
        requests.post(f"{API_URL}/answerCallbackQuery", json={
            "callback_query_id": call["id"],
            "text": "Не для тебя"
        })
        return
    
    if data.startswith("accept_"):
        uid = int(data.split("_")[1])
        send_message(chat_id, "Принято")
        send_message(uid, "Твоя карта принята")
    
    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])
        send_message(chat_id, "Отклонено")
        send_message(uid, "Твоя карта отклонена")
    
    elif data.startswith("reply_"):
        uid = int(data.split("_")[1])
        send_message(chat_id, "Напиши ответ:")
        # Сохраняем user_id для следующего шага (упрощённо)
        global reply_target
        reply_target = uid
    
    requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": call["id"]})

def main():
    global last_update_id, reply_target
    reply_target = None
    print("Бот запущен. Использует sendRichMessage")
    
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
                        process_callback(upd["callback_query"])
                    elif "message" in upd:
                        msg = upd["message"]
                        # Если есть ожидание ответа админа
                        if reply_target and msg.get("text") and msg["chat"]["id"] == ADMIN_ID:
                            send_message(reply_target, f"Ответ админа: {msg['text']}")
                            send_message(ADMIN_ID, "Ответ отправлен")
                            reply_target = None
                        else:
                            process_message(msg)
                    last_update_id = upd["update_id"]
            
            time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()