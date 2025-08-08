import os
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sys

print(f"🔧 Python version: {sys.version}")

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# 📌 Базовые настройки для REST API
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ====== Функции сохранения ======
def save_user_info(user, chat_id):
    try:
        payload = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "is_premium": getattr(user, "is_premium", False),
            "chat_id": chat_id
        }
        r = requests.post(f"{SUPABASE_URL}/rest/v1/users", json=payload, headers=HEADERS)
        if r.status_code in (200, 201):
            print("✅ Пользователь сохранён в Supabase.")
        else:
            print(f"❌ Ошибка сохранения пользователя: {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")

def save_location(user_id, latitude, longitude, address):
    try:
        payload = {
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "address": address
        }
        r = requests.post(f"{SUPABASE_URL}/rest/v1/locations", json=payload, headers=HEADERS)
        if r.status_code in (200, 201):
            print("📍 Геолокация сохранена в Supabase.")
        else:
            print(f"❌ Ошибка сохранения геолокации: {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Ошибка сохранения геолокации: {e}")

def save_activity(user_id, message):
    try:
        payload = {
            "user_id": user_id,
            "message": message
        }
        r = requests.post(f"{SUPABASE_URL}/rest/v1/activity_log", json=payload, headers=HEADERS)
        if r.status_code in (200, 201):
            print("💬 Сообщение сохранено в Supabase.")
        else:
            print(f"❌ Ошибка сохранения сообщения: {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Ошибка сохранения сообщения: {e}")

# ====== Геокодирование ======
def get_address_from_coords(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"format": "json", "lat": lat, "lon": lon, "zoom": 18, "addressdetails": 1}
        headers = {"User-Agent": "telegram-bot-demo"}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name", "Адрес не найден")
        else:
            return "Ошибка геокодирования"
    except Exception as e:
        return f"Ошибка: {e}"

# ====== Хэндлеры ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    save_user_info(user, chat.id)

    photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    photo_id = photos.photos[0][0].file_id if photos.total_count > 0 else None

    location_button = KeyboardButton("📍 Отправить геолокацию", request_location=True)
    location_keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)

    text = (
        f"👤 <b>Информация о вас:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📛 Имя: {user.first_name or '-'}\n"
        f"👪 Фамилия: {user.last_name or '-'}\n"
        f"🔗 Username: @{user.username or '-'}\n"
        f"🌐 Язык: {user.language_code or '-'}\n"
        f"💎 Premium: {'Да' if getattr(user, 'is_premium', False) else 'Нет'}\n"
        f"💬 Chat ID: {chat.id}\n\n"
        f"📍 Пожалуйста, отправьте свою геолокацию 👇"
    )

    if photo_id:
        await update.message.reply_photo(photo=photo_id, caption=text, parse_mode="HTML", reply_markup=location_keyboard)
    else:
        await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=location_keyboard)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user = update.effective_user

    latitude = location.latitude
    longitude = location.longitude
    address = get_address_from_coords(latitude, longitude)

    save_location(user.id, latitude, longitude, address)

    await update.message.reply_text(
        f"📍 Спасибо, {user.first_name}!\n"
        f"<b>Ваша геолокация:</b>\n"
        f"🧭 Широта: <code>{latitude}</code>\n"
        f"🧭 Долгота: <code>{longitude}</code>\n"
        f"🏠 Адрес: <i>{address}</i>",
        parse_mode="HTML"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text
    save_activity(user.id, message)
    await update.message.reply_text(f"Вы сказали: {message}")

# ====== Запуск бота ======
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("✅ Бот запущен...")
    app.run_polling()
