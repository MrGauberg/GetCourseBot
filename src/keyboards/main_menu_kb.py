from typing import List
from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton)

from src.core.config import texts, TG_SUPPORT
from aiogram.utils.keyboard import ReplyKeyboardBuilder


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


async def lesson_details_kb(page: int, assignments: List):
    btns = [
        [
            InlineKeyboardButton(
                text=texts["homework"].format(i+1),
                callback_data=f"homework {assignment['id']}"
            )
        ] for i, assignment in enumerate(assignments)
    ]
    btns.extend([
        [InlineKeyboardButton(text=texts["back_button"], callback_data=f"page_view_lessons {page}")],
        [InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def assignment_kb(lesson_id: int, assignment_id, exists):

    btns = [
        [
            InlineKeyboardButton(text=texts["pull_assignment"],
                                 callback_data=f"pull_assignment {assignment_id}") 
            if not exists else
            InlineKeyboardButton(text=texts["pull_assignment_not"],
                                 callback_data=" ")
        ],
        [InlineKeyboardButton(text=texts["back_button"], callback_data=f"lessons {lesson_id}")],
        [InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def assignment_respones_kb(back_call, back_button=True, skip_button=True, submit_button=False, finish_assignment=False):
    btns = [
        [InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")],
    ]

    if skip_button:
        btns.insert(0, [InlineKeyboardButton(text=texts["skip_btn"], callback_data="skip_btn")])

    if submit_button:
        btns.append([InlineKeyboardButton(text=texts["pull_assignment"], callback_data=back_call)])

    if finish_assignment:
        btns.insert(0, [InlineKeyboardButton(text=texts["finish_assignment"], callback_data="finish_assignment")])

    if back_button:
        btns.append([InlineKeyboardButton(text=texts["back_button"], callback_data=back_call)])

    return InlineKeyboardMarkup(inline_keyboard=btns)




async def phone_number_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=texts["phone_number_btn"],
                   request_contact=True)
    return builder


async def registeration_kb(back_call):
    btns = [
        [InlineKeyboardButton(text=texts["back_button"], callback_data=back_call)],
        [InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)
