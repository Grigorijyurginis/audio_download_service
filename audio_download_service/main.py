from typing import Annotated

from fastapi import FastAPI, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from audio_download_service.models import User
from database import engine, Base, get_async_session

app = FastAPI()

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@app.get("/users")
async def get_users(session: SessionDep):
    result = await session.execute(select(User))
    users = result.scalars().first()
    return users
