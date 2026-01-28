# Используем базовый образ Python (slim версия весит меньше)
FROM python:3.11-slim

# Отключаем создание кэша __pycache__ и буферизацию вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Сначала копируем зависимости (для кэширования слоев Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Команда запуска
CMD ["python", "bot.py"]