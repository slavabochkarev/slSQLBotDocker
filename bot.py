import os
import sys
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

print(f"🔧 Python version: {sys.version}")

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ BOT_TOKEN, SUPABASE_URL или SUPABASE_KEY не заданы в .env")

# Общие заголовки для Supabase API
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ====== API функции ======

def save_user_info(user, chat_id):
    url = f"{SUPABASE_URL}/rest/v1/users"
    payload = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code,
        "is_premium": getattr(user, "is_premium", False),
        "chat_id": chat_id
    }
    try:
        resp = requests.post(url, json=payload, headers=HEADERS)
        resp.raise_for_status()
        print("✅ Пользователь сохранён в Supabase")
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")

def save_location(user_id, latitude, longitude, address):
    url = f"{SUPABASE_URL}/rest/v1/locations"
    payload = {
        "user_id": user_id,
        "latitude": latitude,
        "longitude": longitude,
        "address": address
    }
    try:
        resp = requests.post(url, json=payload, headers=HEADERS)
        resp.raise_for_status()
        print("📍 Геолокация сохранена в Supabase")
    except Exception as e:
        print(f"❌ Ошибка сохранения геолокации: {e}")

def save_message(user_id, text):
    url = f"{SUPABASE_URL}/rest/v1/activity_log"
    payload = {
        "user_id": user_id,
        "message": text
    }
    try:
        resp = requests.post(url, json=payload, headers=HEADERS)
        resp.raise_for_status()
        print("💬 Сообщение сохранено в Supabase")
    except Exception as e:
        print(f"❌ Ошибка сохранения сообщения: {e}")

# Геокодер через OpenStreetMap
def get_address_from_coords(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "json",
            "lat": lat,
            "lon": lon,
            "zoom": 18,
            "addressdetails": 1
        }
        headers = {"User-Agent": "telegram-bot-demo"}
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("display_name", "Адрес не найден")
        else:
            return "Ошибка геокодирования"
    except Exception as e:
        return f"Ошибка: {e}"

# ====== Telegram Handlers ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    save_user_info(user, chat.id)

    location_button = KeyboardButton("📍 Отправить геолокацию", request_location=True)
    location_keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True)

    text = (
        f"👤 <b>Ваши данные:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📛 Имя: {user.first_name or '-'}\n"
        f"👪 Фамилия: {user.last_name or '-'}\n"
        f"🔗 Username: @{user.username or '-'}\n"
        f"🌐 Язык: {user.language_code or '-'}\n"
        f"💎 Premium: {'Да' if getattr(user, 'is_premium', False) else 'Нет'}\n"
        f"💬 Chat ID: {chat.id}\n\n"
        f"📍 Отправьте свою геолокацию 👇"
    )

    await update.message.reply_text(
        text=text,
        parse_mode="HTML",
        reply_markup=location_keyboard
    )

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user = update.effective_user

    address = get_address_from_coords(location.latitude, location.longitude)
    save_location(user.id, location.latitude, location.longitude, address)

    await update.message.reply_text(
        f"📍 Спасибо, {user.first_name}!\n"
        f"🧭 Широта: <code>{location.latitude}</code>\n"
        f"🧭 Долгота: <code>{location.longitude}</code>\n"
        f"🏠 Адрес: <i>{address}</i>",
        parse_mode="HTML"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    save_message(user.id, text)
    await update.message.reply_text(f"Вы сказали: {text}")

# ====== Запуск ======
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("✅ Бот запущен...")
    app.run_polling()
