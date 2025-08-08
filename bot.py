import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from supabase_utils import save_user_info, save_location, save_action

print(f"🔧 Python version: {sys.version}")

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

def get_address_from_coords(lat, lon):
    """Определяет адрес по координатам"""
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
        return "Ошибка геокодирования"
    except Exception as e:
        return f"Ошибка: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    save_user_info(user)
    save_action(user.id, "/start")

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

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=location_keyboard)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user = update.effective_user

    latitude = location.latitude
    longitude = location.longitude
    address = get_address_from_coords(latitude, longitude)

    save_location(user.id, latitude, longitude, address)
    save_action(user.id, "send_location")

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

    save_action(user.id, f"message: {message}")

    await update.message.reply_text(f"Вы сказали: {message}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("✅ Бот запущен...")
    app.run_polling()
