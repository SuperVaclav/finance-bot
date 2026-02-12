import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

# Импортируем базу и AI сервис
from src.database import init_db, async_session, Transaction 
from src.ai_service import parse_expense

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот для учета финансов (v2.2 - Structured Output).\nНапиши трату, например: '15 евро кофе' или просто '500'.")

@dp.message(F.text)
async def process_text(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # 1. Парсим через AI
    data = await parse_expense(message.text)
    
    if not data:
        await message.answer("Ошибка AI сервиса :( Попробуй позже.")
        return

    # 2. ПРОВЕРКА НА УТОЧНЕНИЕ
    # Если AI вернул clarification_needed = True, мы выводим его вопрос и НЕ сохраняем
    if data.get("clarification_needed") is True:
        question_text = data.get("bot_response", "Не понял. Уточните данные.")
        await message.answer(question_text)
        return

    # 3. СОХРАНЕНИЕ (Если уточнение не нужно)
    try:
        async with async_session() as session:
            tx_date = datetime.strptime(data.get('date'), "%Y-%m-%d").date()
            
            new_tx = Transaction(
                amount=data.get('amount'),
                currency=data.get('currency'),
                category=data.get('category'),
                description=data.get('description'),
                type=data.get('type', 'EXPENSE'),
                date=tx_date
            )
            
            session.add(new_tx)
            await session.commit()
            
            # 4. ФОРМИРУЕМ КРАСИВЫЙ ОТВЕТ (как тебе нравится)
            # Мы берем сырые данные из JSON и подставляем в шаблон
            
            # Выбираем эмодзи для типа
            if data.get('type') == 'INCOME':
                icon = "🤑"
            else:
                icon = "💸"

            response_text = (
                f"✅ **Сохранено!**\n"
                f"📂 {data.get('category')}: {data.get('amount')} {data.get('currency')}\n"
                f"{icon} {data.get('description', '')}"
            )
            
            await message.answer(response_text)

    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        await message.answer(f"Ошибка при сохранении в базу: {e}")

async def main():
    print("⏳ Ожидание запуска базы данных...")
    while True:
        try:
            await init_db()
            print("✅ База данных найдена!")
            break
        except Exception as e:
            print(f"❌ Ждем базу... ({e})")
            await asyncio.sleep(5)

    print("🚀 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")