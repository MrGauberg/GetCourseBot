import logging
from aiohttp import web
from aiogram import Bot

log = logging.getLogger(__name__)

async def send_message_to_chat(request: web.Request) -> web.Response:
    """
    POST /internal/send-message/
    JSON: { "chat_id": int, "text": str, "parse_mode": "HTML|MarkdownV2|None" }
    """
    bot: Bot = request.app["bot"]
    try:
        data = await request.json()
        chat_id   = int(data["chat_id"])
        text      = data["text"]
        parsemode = data.get("parse_mode") or None

        await bot.send_message(chat_id, text, parse_mode=parsemode)
        return web.json_response({"status": "ok"})
    except Exception as e:
        log.exception("send_message_to_chat error")
        return web.json_response({"status": "error", "detail": str(e)}, status=500)
