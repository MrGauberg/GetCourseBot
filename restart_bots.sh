#!/bin/sh
# Скрипт для пересборки и перезапуска всех контейнеров, имена которых начинаются с "bot_"
# Использование:
# 1. Сделайте скрипт исполняемым: chmod +x restart_bots.sh
# 2. Запустите его: ./restart_bots.sh

# Получаем список контейнеров, начинающихся с "bot_"
containers=$(docker ps --format "{{.Names}}" | grep '^bot_')

# Пересобираем и перезапускаем каждый найденный контейнер
for container in $containers; do
  echo "Останавливаем контейнер: $container"
  docker stop "$container"

  echo "Удаляем контейнер: $container"
  docker rm "$container"

  # Получаем имя образа, из которого был запущен контейнер
  image=$(docker ps -a --filter "name=$container" --format "{{.Image}}")

  echo "Пересоздаем контейнер: $container из образа $image"
  docker run -d --name "$container" "$image"
done

echo "Все контейнеры, начинающиеся на 'bot_', были пересобраны и запущены."
