import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

# Импортируем всё необходимое для БД
from src.database import init_db, async_session, Transaction 
from src.ai_service import parse_expense

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот для учета финансов (v2.0 - CI/CD works!). Напиши трату, например: 
'15 евро кофе'.")

@dp.message(F.text)
async def process_text(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # 1. Парсим через AI
    data = await parse_expense(message.text)
    
    if not data:
        await message.answer("Ошибка AI сервиса :(")
        return

    if "error" in data:
        await message.answer("Не понял. Попробуй перефразировать.")
        return
# Визуальное оформление в зависимости от типа
    if data.get('type') == 'INCOME':
        emoji_sign = "🤑 **Доход!**"
        amount_sign = "+"
    else:
        emoji_sign = "💸 **Трата**"
        amount_sign = "-"

    response_text = (
        f"{emoji_sign}\n"
        f"📂 Категория: {data.get('category')}\n"
        f"💰 Сумма: {amount_sign}{data.get('amount')} {data.get('currency')}\n"
        f"📝 Описание: {data.get('description')}\n"
        f"📅 Дата: {data.get('date')}"
    )
    # 2. Сохраняем в Базу Данных (PostgreSQL)
    try:
        async with async_session() as session:
            # Превращаем строку даты от ИИ в объект даты Python
            tx_date = datetime.strptime(data.get('date'), "%Y-%m-%d").date()
            
            # Создаем объект транзакции
            new_tx = Transaction(
                amount=data.get('amount'),
                currency=data.get('currency'),
                category=data.get('category'),
                description=data.get('description'),
                type=data.get('type', 'EXPENSE'), # По умолчанию Трата
                date=tx_date
            )
            
            # Добавляем и сохраняем
            session.add(new_tx)
            await session.commit()
            
            await message.answer(
                f"✅ **Сохранено в базу!**\n"
                f"📂 {data.get('category')}: {data.get('amount')} {data.get('currency')}"
            )

    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        await message.answer(f"Ошибка при сохранении в базу: {e}")

# Объединенная функция main
async def main():
    print("⏳ Ожидание запуска базы данных...")
    
    # Цикл попыток подключения (Retry Loop)
    while True:
        try:
            await init_db()  # Пытаемся создать таблицы
            print("✅ База данных найдена! Таблицы проверены.")
            break # Если успех — выходим из цикла
        except Exception as e:
            print(f"❌ База еще не готова ({e}). Ждем 5 секунд...")
            await asyncio.sleep(5) # Ждем и пробуем снова

    print("🚀 Бот запускается...")
    await dp.start_polling(bot)
    await dp.start_polling(bot) # Запускаем бота

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
