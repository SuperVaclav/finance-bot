import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

# Импортируем всё необходимое для БД
from src.database import init_db, async_session, Transaction 
# Импортируем наш обновленный сервис (убедись, что ai_service.py обновлен!)
from src.ai_service import parse_expense

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот для учета финансов (v2.1 - AI Logic Updated!).\nНапиши трату, например: '15 евро кофе'.")

@dp.message(F.text)
async def process_text(message: types.Message):
    # Показываем, что бот "печатает" (думает)
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # 1. Парсим через AI
    data = await parse_expense(message.text)
    
    # Если сервис вернул None (техническая ошибка)
    if not data:
        await message.answer("Ошибка AI сервиса :( Попробуй позже.")
        return

    # 2. НОВАЯ ЛОГИКА: Проверяем, нужно ли уточнение
    # Если AI не понял запрос или нужны детали -> отправляем его вопрос и выходим
    if data.get("clarification_needed") is True:
        # Берем текст ответа из JSON (например: "Понял 100, а чего?")
        response_text = data.get("bot_response", "Не понял. Уточните данные.")
        await message.answer(response_text)
        return  # ВАЖНО: Прерываем функцию, в базу не пишем!

    # 3. Если всё понятно -> Сохраняем в Базу Данных
    try:
        async with async_session() as session:
            # Превращаем строку даты (YYYY-MM-DD) в объект date
            tx_date = datetime.strptime(data.get('date'), "%Y-%m-%d").date()
            
            # Создаем объект транзакции
            new_tx = Transaction(
                amount=data.get('amount'),
                currency=data.get('currency'),
                category=data.get('category'), # Теперь здесь может быть "Music" или "Hobby"!
                description=data.get('description'),
                type=data.get('type', 'EXPENSE'),
                date=tx_date
            )
            
            session.add(new_tx)
            await session.commit()
            
            # 4. Отправляем подтверждение
            # Используем готовый красивый ответ от AI (например: "✅ Записал 500 руб в Еду")
            final_response = data.get("bot_response", "✅ Сохранено!")
            await message.answer(final_response)

    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        await message.answer(f"Ошибка при сохранении в базу: {e}")

# Объединенная функция main
async def main():
    print("⏳ Ожидание запуска базы данных...")
    
    # Retry Loop для базы
    while True:
        try:
            await init_db()
            print("✅ База данных найдена! Таблицы проверены.")
            break
        except Exception as e:
            print(f"❌ База еще не готова ({e}). Ждем 5 секунд...")
            await asyncio.sleep(5)

    print("🚀 Бот запускается...")
    # Запускаем поллинг (убрал дубликат строки)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")