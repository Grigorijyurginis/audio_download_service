import re

from typing import Annotated, List, Optional
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from audio_download_service.models import User, AudioFile
from database import engine, Base, get_async_session

from .schemas import AudioFileResponse, AudioFileListResponse, ErrorResponse

app = FastAPI(title='Audio Files Api', contact={'name': 'Grigory Yurginis'})

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]

AUDIO_STORAGE = "audio_storage"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg"}

Path(AUDIO_STORAGE).mkdir(exist_ok=True)


def validate_filename(filename: str) -> str:
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    return filename.strip()


def serialize_audio_file(audio_file: AudioFile) -> dict:
    """
    Преобразует SQLAlchemy объект AudioFile в словарь.
    Здесь выбираются необходимые поля для ответа.
    """
    return {
        "id": audio_file.id,
        "user_id": audio_file.user_id,
        "name": audio_file.name,
        "path": audio_file.path,
        "created_at": audio_file.created_at,
        "updated_at": audio_file.updated_at,
    }


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def save_audio_file(
        session: AsyncSession,
        user_id: int,
        file: UploadFile,
        name: Optional[str] = None
) -> AudioFile:
    """
    Сохраняет аудиофайл на диск и добавляет запись в БД.

    Проверяет расширение файла, его размер и сохраняет в папку пользователя.
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_name = validate_filename(name if name else file.filename)
    user_audio_dir = Path(AUDIO_STORAGE) / str(user_id)
    user_audio_dir.mkdir(exist_ok=True)
    file_path = user_audio_dir / f"{file_name}{file_ext}"

    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    finally:
        await file.close()

    audio_file = AudioFile(user_id=user_id, name=file_name, path=str(file_path))
    session.add(audio_file)
    return audio_file


@app.post("/files/upload", tags=["AudioFiles"], response_model=AudioFileResponse, responses={
        404: {"model": ErrorResponse, "description": "Пользователь не найден"},
        400: {"model": ErrorResponse, "description": "Некорректный запрос"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
    })
async def upload_audio(session: SessionDep, user_id: int, name: str = None, file: UploadFile = File(...)):
    """
    Загружает один аудиофайл для указанного пользователя.

    - **user_id**: идентификатор пользователя
    - **name**: опциональное название файла; если не задано, используется оригинальное имя файла
    - **file**: загружаемый аудиофайл
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    audio_file = await save_audio_file(session, user_id, file, name)
    await session.commit()
    await session.refresh(audio_file)
    return AudioFileResponse(**serialize_audio_file(audio_file))


@app.post("/files/upload_multiple", tags=["AudioFiles"], response_model=List[AudioFileResponse], responses={
    400: {"model": ErrorResponse, "description": "Некорректный запрос"},
    413: {"model": ErrorResponse, "description": "Один или несколько файлов слишком большие"},
    401: {"model": ErrorResponse, "description": "Неверные учетные данные"},
})
async def upload_multiple_audio(session: SessionDep, user_id: int,  name: Optional[str] = Query(
        None,
        description="Имена для файлов, разделенные запятыми, в том же порядке, что и загружаемые файлы"),
                                files: List[UploadFile] = File(...)):
    """
    Загружает несколько аудиофайлов для указанного пользователя.

    - **files**: список загружаемых аудиофайлов.
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    names_list: Optional[List[str]] = None
    if name:
        names_list = [n.strip() for n in name.split(",")]
        if len(names_list) != len(files):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Количество имен не соответствует количеству файлов"
            )

    audio_files = []
    for index, file in enumerate(files):
        file_name = names_list[index] if names_list else None
        audio_file = await save_audio_file(session, user_id, file, file_name)
        audio_files.append(audio_file)

    await session.commit()
    for audio_file in audio_files:
        await session.refresh(audio_file)

    return [AudioFileResponse(**serialize_audio_file(af)) for af in audio_files]


@app.get("/files", tags=["AudioFiles"], response_model=AudioFileListResponse, responses={
    401: {"model": ErrorResponse, "description": "Неверные учетные данные"},
})
async def get_user_audio_files(user_id: int, session: SessionDep):
    """
    Получает информацию о загруженных аудиофайлах указанного пользователя.

    Возвращает список файлов с названием и путем в локальной файловой системе.
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    result = await session.execute(select(AudioFile).where(AudioFile.user_id == user_id))
    audio_files = result.scalars().all()

    items = [AudioFileResponse(**serialize_audio_file(file)) for file in audio_files]
    return AudioFileListResponse(items=items, count=len(items))


@app.get("/users", tags=["Users"])
async def get_users(session: SessionDep):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users
