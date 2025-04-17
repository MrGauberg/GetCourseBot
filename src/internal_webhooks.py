import logging
from aiohttp import web
from aiogram import Bot, types

log = logging.getLogger(__name__)

async def send_message_to_chat(request: web.Request) -> web.Response:
    """
    POST /internal/send-message/
    {
      "chat_id": int,
      "text": str,
      "parse_mode": "HTML|MarkdownV2|None"
    }
    """
    bot: Bot = request.app["bot"]
    try:
        data       = await request.json()
        chat_id    = int(data["chat_id"])
        text       = data["text"]
        parse_mode = data.get("parse_mode") or None

        await bot.send_message(chat_id, text, parse_mode=parse_mode)
        return web.json_response({"status": "ok"})
    except Exception as e:
        log.exception("send_message_to_chat error")
        return web.json_response({"status": "error", "detail": str(e)}, status=500)

async def send_revision(request: web.Request) -> web.Response:
    """
    POST /internal/send-revision/
    {
      chat_id: int,
      assignment_id: int,
      text: str,              
      video_url?: str,
      files?: string[]         
    }

    """
    bot: Bot = request.app["bot"]

    try:
        data          = await request.json()
        chat_id       = int(data["chat_id"])
        assignment_id = int(data["assignment_id"])
        full_text     = data["text"]          

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(
                    text="Отправить новое решение",
                    callback_data=f"pull_assignment {assignment_id} wb"
                )
            ]]
        )

        await bot.send_message(
            chat_id,
            full_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=kb,
        )

        return web.json_response({"status": "ok"})

    except Exception as e:
        log.exception("send_revision error")
        return web.json_response({"status": "error", "detail": str(e)}, status=500)


