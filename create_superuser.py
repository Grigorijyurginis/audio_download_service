import asyncio
import re
from sqlalchemy.future import select
from audio_download_service.models import User
from database import get_async_session

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


async def create_superuser():
    email = input("Enter email: ").strip()

    if not re.match(EMAIL_REGEX, email):
        print("Error: invalid email!")
        return

    session_gen = get_async_session()
    session = await session_gen.__anext__()
    try:
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()

        if existing_user:
            print("Error: email already exists!")
            return

        superuser = User(email=email, is_superuser=True)
        session.add(superuser)
        await session.commit()
        print(f"The superuser {email} has been successfully created!")
    finally:
        await session_gen.aclose()


if __name__ == "__main__":
    asyncio.run(create_superuser())
