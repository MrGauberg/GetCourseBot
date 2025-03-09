#!/bin/sh
# Скрипт для пересборки и обновления всех контейнеров, имена которых начинаются с "bot_"
# Использование:
# 1. Сделайте скрипт исполняемым: chmod +x restart_bots.sh
# 2. Запустите его: ./restart_bots.sh

# Получаем список контейнеров, начинающихся с "bot_"
containers=$(docker ps --format "{{.Names}}" | grep '^bot_')

# Пересобираем образы контейнеров
echo "Пересобираем образы..."
docker-compose build

# Перезапускаем контейнеры с новыми образами
for container in $containers; do
  echo "Перезапускаем контейнер: $container"
  docker-compose up -d --no-deps "$container"
done

echo "Все контейнеры, начинающиеся на 'bot_', были пересобраны и запущены с новыми образами."
