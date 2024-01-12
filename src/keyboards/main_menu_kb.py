from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton)

from src.core.config import texts, TG_SUPPORT


async def main_menu():

    buttons = [
        [InlineKeyboardButton(text=texts["courses_btn"],
                              callback_data="courses_btn")],
        [InlineKeyboardButton(text=texts["support"],
                              url=TG_SUPPORT)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
