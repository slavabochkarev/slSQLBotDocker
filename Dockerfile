# Используем Python 3.11
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем файлы проекта
COPY requirements.txt .
COPY bot.py .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Указываем переменные окружения (токен будет передаваться через Render)
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "bot.py"]
