from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.config import settings
from sqlalchemy.ext.declarative import declarative_base

async_engine = create_async_engine(url=settings.MYSQL_URL, echo=True)

async_session = sessionmaker(
    bind=async_engine, expire_on_commit=False, class_=AsyncSession
)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        statement = text("SELECT 'Hello Async MySQL...';")
        result = await session.execute(statement)
        print(result.all())
        yield session
        