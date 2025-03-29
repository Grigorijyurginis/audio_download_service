import os
from typing import Annotated

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import String
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

str_50 = Annotated[str, 50]


class Base(DeclarativeBase):
    type_annotatiom_map = {
        str_50: String(50)
    }


async def get_async_session() -> AsyncSession:
    async with AsyncSession() as session:
        yield session
