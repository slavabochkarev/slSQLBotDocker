import os
import wave
import re
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from vosk import Model, KaldiRecognizer

API_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

WEBHOOK_HOST = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}"
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# Загружаем модель Vosk (скачай заранее и положи в ./models/)
MODEL_PATH = "models/vosk-model-small-ru-0.22"
model = Model(MODEL_PATH)

async def convert_to_wav(input_file: str, output_file: str):
    """Конвертация ogg -> wav 16kHz mono"""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-ar", "16000",
        "-ac", "1",
        output_file,
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def recognize_digits(wav_path: str) -> str:
    """Распознавание речи и извлечение только цифр"""
    wf = wave.open(wav_path, "rb")
    rec = KaldiRecognizer(model, 16000)

    result_text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = rec.Result()
            result_text += res

    res = rec.FinalResult()
    result_text += res

    # Вытаскиваем цифры
    digits = re.sub(r"\D", "", result_text)
    return digits if digits else "Цифры не найдены"

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("Привет 👋 Пришли мне голосовое с цифрами, и я их распознаю!")

@dp.message_handler(content_types=types.ContentType.VOICE)
async def voice_handler(message: types.Message):
    file = await bot.get_file(message.voice.file_id)
    file_path = file.file_path
    file_name = "voice.ogg"
    wav_name = "voice.wav"

    # Скачиваем голосовое
    await bot.download_file(file_path, file_name)

    # Конвертируем в wav
    await convert_to_wav(file_name, wav_name)

    # Распознаём
    digits = recognize_digits(wav_name)

    await message.reply(f"Распознанные цифры: {digits}")

async def on_startup(dp):
    print(">>> Устанавливаем webhook:", WEBHOOK_URL)
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
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
