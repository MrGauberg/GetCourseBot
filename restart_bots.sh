#!/bin/sh
# Скрипт для пересборки образа и обновления всех контейнеров, начинающихся с "bot_"
# Использование:
# 1. Сделайте скрипт исполняемым: chmod +x restart_bots.sh
# 2. Запустите его: ./restart_bots.sh

IMAGE_NAME="my-telegram-bot-image"

# Пересобираем образ
echo "Пересобираем образ: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

# Получаем список контейнеров, начинающихся с "bot_"
containers=$(docker ps --format "{{.Names}}" | grep '^bot_')

# Перезапускаем контейнеры с новым образом
for container in $containers; do
  echo "Обновляем контейнер: $container"
  docker stop "$container"
  docker container start "$container"
done

echo "Все контейнеры, начинающиеся на 'bot_', были обновлены и перезапущены."
