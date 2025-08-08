import os
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import sys
print(f"🔧 Python version: {sys.version}")

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Читаем токен из переменной окружения

# Получение адреса по координатам
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

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    location_button = KeyboardButton("📍 Отправить геолокацию", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)

    text = (
        f"Привет, {user.first_name}!\n"
        f"ID: {user.id}\n"
        f"Chat ID: {chat.id}\n"
        "Отправь свою геолокацию 👇"
    )
    await update.message.reply_text(text, reply_markup=keyboard)

# Обработка геолокации
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    address = get_address_from_coords(location.latitude, location.longitude)
    await update.message.reply_text(
        f"📍 Твоя локация:\n"
        f"Широта: {location.latitude}\n"
        f"Долгота: {location.longitude}\n"
        f"Адрес: {address}"
    )

# Echo
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ты сказал: {update.message.text}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Бот запущен...")
    app.run_polling()
