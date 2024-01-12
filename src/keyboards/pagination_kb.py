from aiogram.types import (InlineKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from src.core.config import texts


async def generate_db_items_keyboard(page: int,
                                     items: List,
                                     next: str,
                                     previous: str,
                                     model_name: str,
                                     back_call: str,
                                     unit_name: str,
                                     ) -> InlineKeyboardMarkup:
    builder_size = []

    builder = InlineKeyboardBuilder()

    for item in items:

        builder.button(
            text=f"{item['title']}",
            callback_data=f"{model_name} {item['id']}"
        )
        builder_size.append(1)

    builder_size.append(0)
    if previous:
        builder.button(text="<", callback_data=f"page_{unit_name} {page - 1}")
        builder_size[-1] += 1

    builder.button(text=' ', callback_data=f'search_{unit_name}')
    builder_size[-1] += 1

    if next:
        builder.button(text=">", callback_data=f"page_{unit_name} {page + 1}")
        builder_size[-1] += 1

    builder.button(text=texts["back_button"], callback_data=back_call)
    builder.button(text=texts["cancel"], callback_data="back_to_main_menu")
    builder_size.append(2)

    builder.adjust(*builder_size)
    return builder