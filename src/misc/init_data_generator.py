import hmac
import hashlib
import json
import time
import logging
from urllib.parse import quote, parse_qsl

logger = logging.getLogger(__name__)


def generate_telegram_initdata(
    tg_user_id: int,
    bot_token: str,
    original_init_data: str = None
) -> str:
    """
    Генерирует initData для Telegram WebApp. Если передан original_init_data,
    берет оттуда query_id и signature для правильной валидации подписи.
    
    Args:
        tg_user_id: ID пользователя в Telegram
        bot_token: Токен бота (из BotConfig)
        original_init_data: Оригинальный initData от пользователя (если есть из Telegram WebApp)
    
    Returns:
        Строка query-string: "auth_date=...&user=...&query_id=...&signature=...&hash=..."
    """
    # Компактный JSON без пробелов (как у Telegram)
    user_json = json.dumps({"id": tg_user_id}, separators=(',', ':'))
    auth_date = str(int(time.time()))
    
    pairs = {
        "auth_date": auth_date,
        "user": user_json,
    }
    
    # Если есть оригинальный initData - берем оттуда query_id и signature
    if original_init_data:
        try:
            original_pairs = dict(parse_qsl(original_init_data))
            if "query_id" in original_pairs:
                pairs["query_id"] = original_pairs["query_id"]
            if "signature" in original_pairs:
                pairs["signature"] = original_pairs["signature"]
        except Exception:
            # Если не удалось распарсить original_init_data, продолжаем без него
            pass
    
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
    
    # Формируем финальную query-string (отсортированную для консистентности)
    init_data = "&".join(
        f"{k}={quote(str(v))}" 
        for k, v in sorted(pairs.items())
    )
    
    # Логируем сгенерированный initData
    logger.info(f"Сгенерирован initData для user_id={tg_user_id}: {init_data}")
    if original_init_data:
        logger.info(f"Использован original_init_data: {original_init_data}")
        logger.info(f"Извлечены поля: query_id={pairs.get('query_id', 'нет')}, signature={pairs.get('signature', 'нет')}")
    
    return init_data


def validate_and_reuse_telegram_initdata(original_init_data: str, bot_token: str) -> str:
    """
    Если бот получает оригинальный initData от пользователя (из Telegram WebApp),
    его можно переиспользовать, предварительно проверив подпись.
    
    Args:
        original_init_data: Оригинальная строка initData от Telegram WebApp
        bot_token: Токен бота для проверки подписи
    
    Returns:
        Валидный initData (оригинальный, если подпись верна)
    
    Raises:
        ValueError: Если hash отсутствует или подпись не совпадает
    """
    # Парсим оригинальный initData
    pairs = dict(parse_qsl(original_init_data))
    
    # Проверяем подпись (как на бэкенде)
    provided_hash = pairs.get("hash")
    if not provided_hash:
        raise ValueError("hash отсутствует в initData")
    
    # Формируем data_check_string (исключаем hash)
    data_check_string = "\n".join(
        f"{k}={v}"
        for k, v in sorted(pairs.items())
        if k != "hash"
    )
    
    # Проверяем подпись
    secret_key = hmac.new(
        key=bot_token.encode("utf-8"),
        msg=b"WebAppData",
        digestmod=hashlib.sha256,
    ).digest()
    
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(provided_hash, expected_hash):
        raise ValueError("Подпись initData не совпадает")
    
    # Если подпись валидна, возвращаем оригинальный initData
    return original_init_data

