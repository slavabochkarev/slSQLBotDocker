FROM python:3.10-slim

# ffmpeg нужен для конвертации аудио
RUN apt-get update && apt-get install -y ffmpeg wget unzip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скачиваем модель Vosk (пример: русская маленькая)
RUN mkdir -p models && \
    cd models && \
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip && \
    unzip vosk-model-small-ru-0.22.zip && \
    rm vosk-model-small-ru-0.22.zip

COPY . .

CMD ["python", "bot.py"]
