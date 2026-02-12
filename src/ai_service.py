import os
import json
import logging
import google.generativeai as genai
from datetime import datetime

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        return "Ты финансовый бот. Верни JSON с полями amount, currency, category, type (INCOME/EXPENSE), date, clarification_needed, bot_response."

async def parse_expense(user_text: str):
    try:
        # 1. Загружаем и готовим промпт
        base_prompt = load_prompt()
        current_date = datetime.now().strftime("%Y-%m-%d")
        full_prompt = base_prompt.replace("{current_date}", current_date)
        
        # 2. Отправляем в Gemini
        # Передаем промпт и сообщение пользователя как части контента
        response = await model.generate_content_async(
            contents=[full_prompt, f"User message: {user_text}"]
        )
        
        # 3. Парсим JSON
        # Gemini в JSON-режиме обычно возвращает чистый JSON, но иногда может добавить markdown
        raw_text = response.text.strip()
        
        # Удаляем ```json ... ``` если они есть (на всякий случай)
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json", "").strip()

        parsed_data = json.loads(raw_text)
        return parsed_data
        
    except json.JSONDecodeError:
        logging.error(f"AI returned invalid JSON: {response.text}")
        return {
            "clarification_needed": True,
            "bot_response": "Что-то пошло не так с моим электронным мозгом. Попробуй переформулировать."
        }
    except Exception as e:
        logging.error(f"Error parsing with AI: {e}")
        return {
            "clarification_needed": True,
            "bot_response": "Произошла ошибка при обработке сообщения. Попробуй позже."
        }
