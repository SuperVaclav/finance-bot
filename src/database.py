from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Date
import os

# Получаем URL БД из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Скрываем пароль для логов, чтобы не "светить" его
    safe_url = DATABASE_URL.split("@")[-1] 
    print(f"🕵️ DEBUG: Попытка подключения к хосту: {safe_url}")
else:
    print("❌ ERROR: Переменная DATABASE_URL пустая!")

# Создаем движок
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# Описание нашей таблицы
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(20)) # EXPENSE или INCOME
    date: Mapped[str] = mapped_column(Date)

# Функция для создания таблиц при старте
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)