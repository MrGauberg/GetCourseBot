from typing import List
from src.core.config import texts, TG_SUPPORT
from src.core.settings import application_settings
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


async def main_menu():
    buttons = [
        [InlineKeyboardButton(text=texts["courses_btn"], callback_data="courses_btn")],
        [InlineKeyboardButton(text=texts["my_courses"], callback_data="my_courses")],
        [InlineKeyboardButton(text=texts["calendar"], callback_data="show_calendar")],
        [InlineKeyboardButton(text=texts["support"], url=TG_SUPPORT)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def course_details_kb(
    course_id: int, 
    page: int, 
    is_buyed: bool, 
    bot_id: int, 
    user_name: str,
    user_id: int
) -> InlineKeyboardMarkup:
    buttons = []

    # Добавить кнопку "Подать заявку", только если курс не куплен
    if not is_buyed:
        web_app_url = f"https://{application_settings.WEB_APP_URL}/lead-create?bot_id={bot_id}&user_name={user_name}&course_id={course_id}&user_id={user_id}"
        buttons.append([
            InlineKeyboardButton(
                text=texts["course_request"],
                web_app=WebAppInfo(url=web_app_url)
            )
        ])

    # Кнопка "Назад" всегда присутствует
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data=f"page_view_courses_all {page}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def buyed_course_details(course_id: int, page: int):
    btns = [
        [InlineKeyboardButton(text=texts["course_lessons"], callback_data=f"course_lessons {course_id}")],
        [
            InlineKeyboardButton(text=texts["back_button"], callback_data=f"page_view_courses_student {page}"),
            InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def lesson_details_kb(page: int, assignments: List, lesson: dict = None):
    btns = []
    
    # Добавляем кнопку "Видео" если есть видео
    if lesson and lesson.get("has_video"):
        lesson_id = lesson.get("id")
        if lesson_id:
            btns.append([
                InlineKeyboardButton(
                    text=texts["video_btn"],
                    callback_data=f"show_lesson_videos {lesson_id}"
                )
            ])
    
    # Добавляем кнопки домашних заданий
    btns.extend([
        [
            InlineKeyboardButton(
                text=texts["homework"].format(i+1),
                callback_data=f"homework {assignment['id']}"
            )
        ] for i, assignment in enumerate(assignments)
    ])
    
    btns.append([
        InlineKeyboardButton(text=texts["back_button"], callback_data=f"page_view_lessons {page}"),
        InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def assignment_kb(lesson_id: int, assignment_id, exists, assignment: dict = None):
    btns = []
    
    # Добавляем кнопку "Видео" если есть видео
    if assignment and assignment.get("has_video"):
        btns.append([
            InlineKeyboardButton(
                text=texts["video_btn"],
                callback_data=f"show_assignment_videos {assignment_id}"
            )
        ])
    
    # Добавляем кнопку отправки решения
    btns.append([
        InlineKeyboardButton(text=texts["pull_assignment"],
                             callback_data=f"pull_assignment {assignment_id}") 
        if not exists else
        InlineKeyboardButton(text=texts["pull_assignment_not"],
                             callback_data=" ")
    ])
    
    btns.append([
        InlineKeyboardButton(text=texts["back_button"], callback_data=f"lessons {lesson_id}"),
        InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def assignment_respones_kb(back_call, back_button=True, skip_button=True, submit_button=False, finish_assignment=False):
    btns = []

    if skip_button:
        btns.append([InlineKeyboardButton(text=texts["skip_btn"], callback_data="skip_btn")])

    if submit_button:
        btns.append([InlineKeyboardButton(text=texts["pull_assignment"], callback_data=back_call)])

    if finish_assignment:
        btns.append([InlineKeyboardButton(text=texts["finish_assignment"], callback_data="finish_assignment")])

    # Кнопки "Назад" и "Главное меню" в одну строку
    if back_button:
        btns.append([
            InlineKeyboardButton(text=texts["back_button"], callback_data=back_call),
            InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")
        ])
    else:
        btns.append([InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=btns)


async def phone_number_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=texts["phone_number_btn"], request_contact=True)
    return builder


async def registeration_kb(back_call):
    btns = [
        [
            InlineKeyboardButton(text=texts["back_button"], callback_data=back_call),
            InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)
