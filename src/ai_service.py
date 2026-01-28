import os
import json
import logging
import google.generativeai as genai
from datetime import datetime

# Настройка API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={"response_mime_type": "application/json"}
)

# Путь к файлу промпта (внутри контейнера)
PROMPT_PATH = "config/system_prompt.txt"

def load_prompt():
    """Читает системный промпт из файла"""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Файл промпта не найден по пути {PROMPT_PATH}!")
        # Возвращаем аварийный промпт, чтобы бот не упал
        return "Ты финансовый бот. Верни JSON с полями amount, currency, category, type (INCOME/EXPENSE), date."

async def parse_expense(user_text: str):
    try:
        # 1. Загружаем текст промпта
        base_prompt = load_prompt()
        
        # 2. Подставляем дату
        current_date = datetime.now().strftime("%Y-%m-%d")
        full_prompt = base_prompt.replace("{current_date}", current_date)
        
        # 3. Отправляем в Gemini
        response = await model.generate_content_async([full_prompt, user_text])
        
        # 4. Парсим JSON
        parsed_data = json.loads(response.text)
        return parsed_data
        
    except Exception as e:
        logging.error(f"Error parsing with AI: {e}")
        return None
