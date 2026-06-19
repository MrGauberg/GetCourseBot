import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .settings import user_settings, redis_settings
from src.core.text import get_text

logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler('bot.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)
logging.getLogger().addHandler(file_handler)

form_router = Router()
view_router = Router()

if redis_settings.REDIS_HOST:
    storage = RedisStorage(
          host=redis_settings.REDIS_HOST, port=redis_settings.REDIS_PORT
    )
else:
    storage = MemoryStorage()

bot_kwargs = {
    'token': user_settings.BOT_TOKEN,
    'parse_mode': 'HTML',
}

if user_settings.TG_PROXY_URL:
    bot_kwargs['session'] = AiohttpSession(proxy=user_settings.TG_PROXY_URL)

bot = Bot(**bot_kwargs)
dp = Dispatcher(storage=storage)
TG_SUPPORT = f"https://t.me/{user_settings.TECH_SUPPORT_TG_NAME}"
scheduler = AsyncIOScheduler()

texts = get_text("texts.json")
