import os

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/db_check")
async def db_check():
    return await check_db_connection()


async def check_db_connection():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            return {"db_result": "Connection successful"}
    except OperationalError as e:
        return {"db_result": "Connection failed", "error": str(e)}
