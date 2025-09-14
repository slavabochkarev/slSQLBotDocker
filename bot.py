import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from pydub import AudioSegment
from faster_whisper import WhisperModel

# === Конфиги ===
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium

# Webhook настройки (Render сам задаст hostname)
WEBHOOK_HOST = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}"
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# === Инициализация ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загружаем модель при старте (CPU-only)
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("👋 Привет! Я бот с локальным распознаванием речи (faster-whisper).")


@dp.message_handler(content_types=["voice"])
async def voice_message_handler(message: types.Message):
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    # Скачиваем голосовое сообщение
    url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            audio_data = await resp.read()
            with open("voice.ogg", "wb") as f:
                f.write(audio_data)

    # Обрезаем первые 5 секунд
    audio = AudioSegment.from_file("voice.ogg", format="ogg")
    first_5_sec = audio[:5000]
    first_5_sec.export("voice_trimmed.wav", format="wav")

    # Распознаём через faster-whisper
    segments, _ = model.transcribe("voice_trimmed.wav", beam_size=5)
    text = " ".join([seg.text for seg in segments])

    await message.reply(f"📝 Текст: {text if text else 'не удалось распознать'}")


async def on_startup(dp):
    print(">>> Устанавливаем webhook:", WEBHOOK_URL)
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    print(">>> Удаляем webhook")
    await bot.delete_webhook()


if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
