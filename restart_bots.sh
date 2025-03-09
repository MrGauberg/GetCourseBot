#!/bin/sh
# Скрипт для перезапуска всех контейнеров, имена которых начинаются с "bot_"
# Использование:
# 1. Сделайте скрипт исполняемым: chmod +x restart_bots.sh
# 2. Запустите его: ./restart_bots.sh

# Получаем список имён контейнеров, начинающихся с "bot_"
containers=$(docker ps --format "{{.Names}}" | grep '^bot_')

# Перезагружаем каждый найденный контейнер
for container in $containers; do
  echo "Перезагружаем контейнер: $container"
  docker restart "$container"
done

echo "Все контейнеры, начинающиеся на 'bot_', были перезапущены."
