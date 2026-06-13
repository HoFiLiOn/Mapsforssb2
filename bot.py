import requests
import json
import time

BOT_TOKEN = "8649154788:AAFQRZ2Cwg8n73AOPu3og46GFEtSwjUpsjU"
ADMIN_ID = 7040677455

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = 0
reply_target = None

# ============= RICH MESSAGE БЛОКИ =============
def rich_start_blocks():
    return [
        {
            "type": "heading",
            "level": 1,
            "children": [{"type": "text", "text": "🎯 Бот для приема карт"}]
        },
        {
            "type": "paragraph",
            "children": [{"type": "text", "text": "Отправь мне фото или скриншот — я перешлю админу."}]
        },
        {
            "type": "table",
            "rows": [
                {"cells": [
                    {"children": [{"type": "text", "text": "📦 Тип"}]},
                    {"children": [{"type": "text", "text": "✅ Статус"}]}
                ]},
                {"cells": [
                    {"children": [{"type": "text", "text": "🃏 Карты"}]},
                    {"children": [{"type": "text", "text": "Прием"}]}
                ]},
                {"cells": [
                    {"children": [{"type": "text", "text": "📸 Фото"}]},
                    {"children": [{"type": "text", "text": "Прием"}]}
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
                    "children": [{"type": "text", "text": "1️⃣ Нажми на скрепку\n2️⃣ Выбери фото\n3️⃣ Отправь"}]
                }
            ]
        }
    ]

def rich_stats_blocks(stats):
    return [
        {
            "type": "heading",
            "level": 2,
            "children": [{"type": "text", "text": "📊 Статистика бота"}]
        },
        {
            "type": "table",
            "rows": [
                {"cells": [
                    {"children": [{"type": "text", "text": "Параметр"}]},
                    {"children": [{"type": "text", "text": "Значение"}]}
                ]},
                {"cells": [
                    {"children": [{"type": "text", "text": "👥 Пользователей"}]},
                    {"children": [{"type": "text", "text": str(stats['users'])}]}
                ]},
                {"cells": [
                    {"children": [{"type": "text", "text": "🃏 Принято карт"}]},
                    {"children": [{"type": "text", "text": str(stats['accepted'])}]}
                ]},
                {"cells": [
                    {"children": [{"type": "text", "text": "❌ Отклонено"}]},
                    {"children": [{"type": "text", "text": str(stats['rejected'])}]}
                ]}
            ]
        }
    ]

# ============= ФУНКЦИИ ОТПРАВКИ =============
def send_rich_message(chat_id, blocks):
    payload = {"chat_id": chat_id, "rich_message": {"blocks": blocks}}
    return requests.post(f"{API_URL}/sendRichMessage", json=payload)

def send_photo(chat_id, photo_id, caption=""):
    return requests.post(f"{API_URL}/sendPhoto", json={"chat_id": chat_id, "photo": photo_id, "caption": caption})

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return requests.post(f"{API_URL}/sendMessage", json=data)

def admin_buttons(user_id):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Принять", "callback_data": f"accept_{user_id}"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{user_id}"}
            ],
            [{"text": "✏️ Ответить", "callback_data": f"reply_{user_id}"}]
        ]
    }

# ============= ОБРАБОТЧИКИ =============
stats = {"users": set(), "accepted": 0, "rejected": 0}

def process_message(message):
    global reply_target
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("username", "")
    text = message.get("text", "")
    
    stats["users"].add(user_id)
    
    # ========== СЕКРЕТНЫЕ КОМАНДЫ ==========
    if text == "/ping":
        send_message(chat_id, "🏓 Pong!")
        return
    elif text == "/time":
        send_message(chat_id, f"🕐 {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return
    elif text == "/id":
        send_message(chat_id, f"🆔 Твой ID: `{user_id}`")
        return
    elif text == "/stats":
        if user_id == ADMIN_ID:
            send_rich_message(chat_id, rich_stats_blocks({
                "users": len(stats["users"]),
                "accepted": stats["accepted"],
                "rejected": stats["rejected"]
            }))
        else:
            send_message(chat_id, "❌ Нет доступа")
        return
    elif text == "/broadcast":
        if user_id == ADMIN_ID:
            send_message(chat_id, "📢 Напиши текст для рассылки:")
            reply_target = ("broadcast", chat_id)
        else:
            send_message(chat_id, "❌ Нет доступа")
        return
    elif text == "/restart":
        if user_id == ADMIN_ID:
            send_message(chat_id, "🔄 Перезапуск...")
            import sys
            sys.exit(0)
        return
    
    # Обычные команды
    if text == "/start":
        send_rich_message(chat_id, rich_start_blocks())
        return
    
    # Прием фото
    if message.get("photo"):
        photo_id = message["photo"][-1]["file_id"]
        username_str = f"@{username}" if username else f"id{user_id}"
        send_photo(ADMIN_ID, photo_id, f"🃏 Новая карта от {username_str}")
        send_message(ADMIN_ID, "👇 Выбери действие:", admin_buttons(user_id))
        send_message(chat_id, "✅ Карта отправлена админу")
        return
    
    if text:
        send_message(chat_id, "📸 Отправь фото (скриншот или карту)")

def process_callback(call):
    global reply_target
    user_id = call["from"]["id"]
    data = call["data"]
    message = call.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    
    if user_id != ADMIN_ID:
        requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": call["id"], "text": "⛔ Не для тебя"})
        return
    
    if data.startswith("accept_"):
        uid = int(data.split("_")[1])
        stats["accepted"] += 1
        send_message(chat_id, "✅ Принято")
        send_message(uid, "✅ Твоя карта принята")
    
    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])
        stats["rejected"] += 1
        send_message(chat_id, "❌ Отклонено")
        send_message(uid, "❌ Твоя карта отклонена")
    
    elif data.startswith("reply_"):
        uid = int(data.split("_")[1])
        send_message(chat_id, "✏️ Напиши ответ:")
        reply_target = ("reply", uid, chat_id)
    
    requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": call["id"]})

# ============= ЗАПУСК =============
def main():
    global last_update_id, reply_target
    print("✅ Бот запущен")
    print("📋 Секретные команды: /ping, /time, /id, /stats, /broadcast, /restart")
    
    while True:
        try:
            resp = requests.get(f"{API_URL}/getUpdates", params={"offset": last_update_id + 1, "timeout": 30})
            data = resp.json()
            
            if data.get("ok") and data.get("result"):
                for upd in data["result"]:
                    if "callback_query" in upd:
                        process_callback(upd["callback_query"])
                    elif "message" in upd:
                        msg = upd["message"]
                        # Обработка ответов админа
                        if reply_target and reply_target[0] == "reply" and msg.get("text") and msg["chat"]["id"] == ADMIN_ID:
                            _, uid, admin_chat = reply_target
                            send_message(uid, f"📨 Ответ админа:\n{msg['text']}")
                            send_message(admin_chat, "✅ Ответ отправлен")
                            reply_target = None
                        elif reply_target and reply_target[0] == "broadcast" and msg.get("text") and msg["chat"]["id"] == ADMIN_ID:
                            _, admin_chat = reply_target
                            text = msg["text"]
                            count = 0
                            for uid in stats["users"]:
                                try:
                                    send_message(uid, f"📢 Рассылка:\n{text}")
                                    count += 1
                                except:
                                    pass
                            send_message(admin_chat, f"✅ Отправлено {count} пользователям")
                            reply_target = None
                        else:
                            process_message(msg)
                    last_update_id = upd["update_id"]
            
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()