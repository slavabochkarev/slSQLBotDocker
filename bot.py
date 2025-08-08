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

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ======= REST-запросы =======
def save_user_info(user):
    try:
        url = f"{SUPABASE_URL}/rest/v1/users"
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code,
            "is_premium": getattr(user, "is_premium", False)
        }
        r = requests.post(url, headers=HEADERS, json=data)
        r.raise_for_status()
        print("✅ Пользователь сохранён в базе.")
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")

def save_location(user_id, latitude, longitude, address):
    try:
        url = f"{SUPABASE_URL}/rest/v1/locations"
        data = {
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "address": address
        }
        r = requests.post(url, headers=HEADERS, json=data, params={"return": "minimal"})
        r.raise_for_status()
        print("📍 Геолокация сохранена.")
    except Exception as e:
        print(f"❌ Ошибка сохранения геолокации: {e}")

def save_activity(user_id, action):
    try:
        url = f"{SUPABASE_URL}/rest/v1/activity_log"
        data = {
            "user_id": user_id,
            "action": action
        }
        r = requests.post(url, headers=HEADERS, json=data, params={"return": "minimal"})
        r.raise_for_status()
        print("💬 Действие сохранено.")
    except Exception as e:
        print(f"❌ Ошибка сохранения действия: {e}")
        
# ======= Вспомогательная функция =======
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
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json().get("display_name", "Адрес не найден")
        else:
            return "Ошибка геокодирования"
    except Exception as e:
        return f"Ошибка: {e}"

# ======= Обработчики =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    save_user_info(user)
    save_activity(user.id, "start command")

    location_button = KeyboardButton("📍 Отправить геолокацию", request_location=True)
    location_keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True)

    text = (
        f"👤 <b>Информация о вас:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📛 Имя: {user.first_name or '-'}\n"
        f"👪 Фамилия: {user.last_name or '-'}\n"
        f"🔗 Username: @{user.username or '-'}\n"
        f"🌐 Язык: {user.language_code or '-'}\n"
        f"💎 Premium: {'Да' if getattr(user, 'is_premium', False) else 'Нет'}\n"
    )

    await update.message.reply_text(
        text=text,
        parse_mode="HTML",
        reply_markup=location_keyboard
    )

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user = update.effective_user

    latitude = location.latitude
    longitude = location.longitude

    address = get_address_from_coords(latitude, longitude)
    save_location(user.id, latitude, longitude, address)
    save_activity(user.id, "sent location")

    await update.message.reply_text(
        f"📍 Спасибо, {user.first_name}!\n"
        f"🧭 Широта: <code>{latitude}</code>\n"
        f"🧭 Долгота: <code>{longitude}</code>\n"
        f"🏠 Адрес: <i>{address}</i>",
        parse_mode="HTML"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text
    save_activity(user.id, f"message: {message}")
    await update.message.reply_text(f"Вы сказали: {message}")

# ======= Запуск =======
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("✅ Бот запущен...")
    app.run_polling()
