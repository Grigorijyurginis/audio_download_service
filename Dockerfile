FROM python:3.12-alpine3.21

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root

COPY . .

CMD ["uvicorn", "audio_download_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
