FROM python:3.11


ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/"


WORKDIR /app


RUN python -m pip install --upgrade pip
RUN python -m pip install poetry

COPY . .

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction


CMD ["poetry", "run", "python", "src/bot/main.py"]
