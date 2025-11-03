# API для работы с видео в Telegram WebApp

## Обзор

Система HLS‑стриминга для уроков и заданий. Видео конвертируются в HLS, доступ ограничен Telegram WebApp initData и `course_access`.

## Архитектура

### Модели данных

**VideoAsset**:
- `lesson` / `assignment` — привязка
- `hls_rel_path` — относительный путь к HLS
- `original_filename` — имя файла
- `status` — `ready` / `processing` / `error`
- `created` — дата загрузки

### Признак наличия видео

В сериализаторах `Lesson` и `Assignment` есть поле `has_video`:
- `true` — есть `VideoAsset` со `status='ready'`
- `false` — нет

### Автоматическое удаление файлов

**Сигналы Django** удаляют файлы при удалении записей:
- `VideoAsset` → удаление HLS-папки `media/hls/course_X/...`
- `MediaFile` → удаление файла документа
- `Lesson/Assignment` → каскадное удаление связанных `VideoAsset` и `MediaFile`

### HLS

Путь: `media/hls/course_{course_id}/{lesson_id}/video_{video_id}/`
Файлы: `playlist.m3u8`, `seg_000.ts`, `seg_001.ts`, …

## API Endpoints

### 1. Получение списка видео урока

**GET** `/api/v1/videos/lesson/<lesson_id>/list`

**Авторизация**: `X-Telegram-Init-Data`

**Параметры**:
- `page` — страница
- `page_size` — элементов на странице

**Ответ** (200):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "filename": "video.mp4",
      "created": "2025-11-01T22:26:58.399164Z"
    }
  ]
}
```

**Ошибки**:
- 403 без доступа к курсу
- 401 без `initData`

### 2. Получение списка видео задания

**GET** `/api/v1/videos/assignment/<assignment_id>/list`

Аналогично списку урока.

### 3. Получение HLS плейлиста урока

**GET** `/api/v1/videos/lesson/<lesson_id>/video/<video_id>/hls/playlist.m3u8`

**Авторизация**: `X-Telegram-Init-Data`

**Проверки**:
- подпись Telegram initData
- доступ к курсу

**Ответ** (200):
Файл `.m3u8`.

**Ошибки**:
- 404 — нет видео
- 403 — нет доступа

### 4. Получение HLS сегмента урока

**GET** `/api/v1/videos/lesson/<lesson_id>/video/<video_id>/hls/<segment>.ts`

**Авторизация**: `X-Telegram-Init-Data`

**Ответ** (200):
Двоичный `.ts`.

**Ошибки**: как у плейлиста

### 5. Получение HLS плейлиста задания

**GET** `/api/v1/videos/assignment/<assignment_id>/video/<video_id>/hls/playlist.m3u8`

Аналогично уроку.

### 6. Получение HLS сегмента задания

**GET** `/api/v1/videos/assignment/<assignment_id>/video/<video_id>/hls/<segment>.ts`

Аналогично уроку.

## Процесс авторизации

### Telegram initData

```
X-Telegram-Init-Data: auth_date=1234567890&user={"id":123456}&hash=abc123...
```

Проверка подписи:
- `bot_token` владельца курса
- HMAC‑SHA256

### Проверка доступа

```
Payment.objects.filter(
    student_id=tg_user_id,
    course_id=course_id,
    status="1",
    course_access=True
).exists()
```

## Примеры для Telegram бота

### Использование поля has_video

В API курсов/уроков/ДЗ поле `has_video` показывает, есть ли видео:

```python
# При получении списка уроков
response = requests.get(f'https://your-domain.com/api/v1/courses/{course_id}/lessons/')
lessons = response.json()

for lesson in lessons:
    if lesson['has_video']:
        # Есть видео — показываем кнопку просмотра
        pass
```

### Шаг 1: Получение списка видео

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Получение initData из WebApp контекста
init_data = update.effective_user.init_data  # пример

headers = {
    'X-Telegram-Init-Data': init_data
}

# Запрос списка видео
response = requests.get(
    f'https://your-domain.com/api/v1/videos/lesson/{lesson_id}/list',
    headers=headers
)

videos = response.json()['results']

# Создание кнопок для каждого видео
buttons = []
for video in videos:
    buttons.append([
        InlineKeyboardButton(
            text=video['filename'],
            web_app=WebAppInfo(
                url=f"https://your-domain.com/player/?lesson={lesson_id}&video_id={video['id']}"
            )
        )
    ])

keyboard = InlineKeyboardMarkup(buttons)
await context.bot.send_message(
    chat_id=chat_id,
    text="Выберите видео:",
    reply_markup=keyboard
)
```

### Шаг 2: Открытие плеера

Бот открывает WebApp с:

```
https://your-domain.com/player/?lesson=123&video_id=456
```

Плеер:
- получает `initData` от Telegram
- запрашивает плейлист
- стримит HLS

### Пример с несколькими видео

```python
# Генерация initData
init_data = generate_telegram_initdata(update.effective_user.id, bot_token)

# Получение списка
response = requests.get(
    f'https://your-domain.com/api/v1/videos/lesson/{lesson_id}/list',
    headers={'X-Telegram-Init-Data': init_data}
)

videos = response.json()['results']

if len(videos) > 1:
    # Показываем список для выбора
    buttons = []
    for video in videos:
        buttons.append([
            InlineKeyboardButton(
                text=video['filename'],
                web_app=WebAppInfo(
                    url=f"https://your-domain.com/player/?lesson={lesson_id}&video_id={video['id']}"
                )
            )
        ])
    
    await message.reply_text(
        "Доступные видео:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
elif len(videos) == 1:
    # Одно видео — открываем сразу
    video = videos[0]
    await message.reply_text(
        "Открываем видео...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="Смотреть",
                web_app=WebAppInfo(
                    url=f"https://your-domain.com/player/?lesson={lesson_id}&video_id={video['id']}"
                )
            )
        ]])
    )
else:
    await message.reply_text("Видео не найдено")
```

## Особенности

### Безопасность

- Все запросы проверяют `initData`
- Токен берётся из `bot_config` владельца курса
- `course_access` проверяется на каждом запросе

### HLS заголовки

Все запросы HLS включают `X-Telegram-Init-Data`.

### Пагинация

Как у уроков: `page`, `page_size`; без параметров — все результаты.

### Status коды

- 200 — ОК
- 401 — нет `initData`
- 403 — нет доступа
- 404 — не найдено

### Ограничения

- Файл до 200 МБ
- `status = ready`
- Сортировка по `created`
- Отключён download

## Примеры ошибок

**403 Forbidden**:
```json
{"detail": "Нет доступа"}
```
Возможные причины:
- нет доступа к курсу
- неверная подпись `initData`

**404 Not Found**:
Возможные причины:
- нет видео/урока/задания
- нет плейлиста или сегмента

## Генерация initData на стороне бота

### Python пример

```python
import hmac
import hashlib
import json
import time
from urllib.parse import quote

def generate_telegram_initdata(tg_user_id: int, bot_token: str) -> str:
    """
    Генерирует валидный initData для Telegram WebApp.
    
    Args:
        tg_user_id: ID пользователя в Telegram
        bot_token: Токен бота (из BotConfig)
    
    Returns:
        Строка query-string: "auth_date=...&user=...&hash=..."
    """
    user_json = json.dumps({"id": tg_user_id})
    auth_date = str(int(time.time()))
    
    pairs = {
        "auth_date": auth_date,
        "user": user_json,
    }
    
    # Формируем data_check_string (все пары кроме hash, отсортированные по ключу)
    data_check_string = "\n".join(
        f"{k}={v}" 
        for k, v in sorted(pairs.items())
    )
    
    # Вычисляем secret_key и hash
    secret_key = hmac.new(
        key=bot_token.encode("utf-8"),
        msg=b"WebAppData",
        digestmod=hashlib.sha256,
    ).digest()
    
    hash_value = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    pairs["hash"] = hash_value
    
    # Формируем финальную query-string
    init_data = "&".join(f"{k}={quote(str(v))}" for k, v in pairs.items())
    return init_data

# Использование
bot_token = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # токен вашего бота
tg_user_id = 123456789

init_data = generate_telegram_initdata(tg_user_id, bot_token)
print(init_data)
# auth_date=1762059289&user=%7B%22id%22%3A123456789%7D&hash=abc123...
```

### Node.js пример

```javascript
const crypto = require('crypto');
const querystring = require('querystring');

function generateTelegramInitData(tgUserId, botToken) {
    const user = JSON.stringify({ id: tgUserId });
    const authDate = Math.floor(Date.now() / 1000);
    
    const pairs = {
        auth_date: authDate.toString(),
        user: user
    };
    
    // Формируем data_check_string
    const dataCheckString = Object.keys(pairs)
        .sort()
        .map(key => `${key}=${pairs[key]}`)
        .join('\n');
    
    // Вычисляем secret_key и hash
    const secretKey = crypto
        .createHmac('sha256', botToken)
        .update('WebAppData')
        .digest();
    
    const hash = crypto
        .createHmac('sha256', secretKey)
        .update(dataCheckString)
        .digest('hex');
    
    pairs.hash = hash;
    
    // Формируем query-string
    return querystring.stringify(pairs);
}

// Использование
const botToken = '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz';
const tgUserId = 123456789;
const initData = generateTelegramInitData(tgUserId, botToken);
console.log(initData);
```

### Тестирование (только DEBUG)

**GET** `/api/v1/videos/test/generate-initdata/?tg_user_id=123456&course_id=1`

Возвращает валидный `initData` для курса.

**ВАЖНО**: только в DEBUG.

