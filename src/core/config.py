import logging
import socket
import aiohttp
from aiogram import Bot, Dispatcher, Router
from .settings import user_settings, redis_settings
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from src.core.text import get_text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.session.aiohttp import AiohttpSession

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

connector = aiohttp.TCPConnector(family=socket.AF_INET)
session = AiohttpSession(connector=connector)
bot = Bot(
    token=user_settings.BOT_TOKEN,
    parse_mode='HTML',
    session=session,
)
dp = Dispatcher(storage=storage)
TG_SUPPORT = f"https://t.me/{user_settings.TECH_SUPPORT_TG_NAME}"
scheduler = AsyncIOScheduler()

texts = get_text("texts.json")
