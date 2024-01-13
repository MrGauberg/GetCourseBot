from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton)

from src.core.config import texts, TG_SUPPORT


async def main_menu():

    buttons = [
        [InlineKeyboardButton(text=texts["courses_btn"],
                              callback_data="courses_btn")],
        [InlineKeyboardButton(text=texts["my_courses"],
                              callback_data="my_courses")],
        [InlineKeyboardButton(text=texts["support"],
                              url=TG_SUPPORT)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def course_details_kb(
        course_id: int, page: int, is_buyed: bool
) -> InlineKeyboardMarkup:
    buttons = []

    # Добавить кнопку "Купить", только если курс не куплен
    if not is_buyed:
        buttons.append([InlineKeyboardButton(
            text=texts["buy_course"],
            callback_data=f"ukassa_pay_btn {course_id}"
        )])
    # Кнопка "Назад" всегда присутствует
    buttons.append([InlineKeyboardButton(
        text=texts["back_button"],
        callback_data=f"page_view_courses_all {page}"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def buyed_course_details(course_id: int, page: int):
    btns = [
        [InlineKeyboardButton(text=texts["course_lessons"],
                              callback_data=f"course_lessons {course_id}")],
        [InlineKeyboardButton(
            text=texts["back_button"],
            callback_data=f"page_view_courses_student {page}")],
        [InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)
