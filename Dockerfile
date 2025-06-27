FROM python:3.11-slim


ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/"


WORKDIR /app


RUN python -m pip install --upgrade pip
RUN python -m pip install poetry

COPY . .

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction

# заставляем при DNS-lookup отдавать предпочтение IPv4
RUN echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf

CMD ["poetry", "run", "python", "src/bot/main.py"]
