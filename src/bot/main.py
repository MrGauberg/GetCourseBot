from __future__ import annotations

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiohttp import web

from internal_webhooks import send_revision, send_message_to_chat
from src.core.config import dp, bot, form_router, view_router
from src.handlers import start, course, lesson, registration, calendar, assignment
from src.misc.set_bot_commands import set_commands
from src.services.application_client import application_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

async def start_webhook_server(dp: Dispatcher, bot: Bot) -> None:
    host = os.getenv("INTERNAL_HOST", "0.0.0.0")
    port = int(os.getenv("INTERNAL_PORT", 8090))

    app = web.Application()
    app["dp"], app["bot"] = dp, bot
    app.router.add_post("/internal/send-message/", send_message_to_chat)
    app.router.add_post("/internal/request-revision/", send_revision)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    log.info(f"Internal webhook server http://{host}:{port}")

async def on_startup(bot: Bot) -> None:
    await set_commands(bot)

def register_routers() -> None:
    start.register_handler(dp)
    course.register_handler(view_router)
    lesson.register_handler(view_router)
    assignment.register_handler(view_router, form_router)
    registration.register_handler(form_router)

    dp.include_router(calendar.router)
    dp.include_router(view_router)
    dp.include_router(form_router)

async def main() -> None:
    register_routers()

    log.info("Authenticating application client…")
    await application_client.authenticate()
    log.info("Auth ok")

    await on_startup(bot)

    try:
        await asyncio.gather(
            dp.start_polling(bot),
            start_webhook_server(dp, bot),
        )
    except asyncio.CancelledError:
        pass
    finally:
        await application_client.close()
        await bot.session.close()
        log.info("Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
