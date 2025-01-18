from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, LabeledPrice, PreCheckoutQuery, Message, ContentType
)
from src.core.config import texts, bot
from src.keyboards.main_menu_kb import (
    buyed_course_details, course_details_kb, main_menu, registeration_kb
)
from src.keyboards.pagination_kb import generate_db_items_keyboard
from src.misc.course_utils import get_course, get_course_id, get_item
from src.misc.fabrics import create_page_hanler

from src.services.application_client import application_client
from src.core.settings import user_settings
from aiogram.exceptions import TelegramBadRequest

from src.states import UserDataState
from aiogram.types import InlineKeyboardMarkup, WebAppInfo, InlineKeyboardButton



async def create_courses_handler(call: CallbackQuery,
                                 state: FSMContext,
                                 model_name: str,
                                 unit_name: str,
                                 data: dict,
                                 page: int):
    await state.update_data(courses=data['results'],
                            courses_page=page)
    course_list_kb = await generate_db_items_keyboard(
        page,
        data['results'],
        data['next'],
        data['previous'],
        model_name,
        "back_to_main_menu",
        unit_name
    )
    await call.message.edit_text(
        text=texts['choose_course'],
        reply_markup=course_list_kb.as_markup()
    )


# ==============================ALL COURSES====================================
async def all_courses_handler(call: CallbackQuery,
                              state: FSMContext,
                              page: int = 1):
    data = await application_client.get_courses_by_user_id(
        user_settings.USER_ID,
        page=page
    )
    await create_courses_handler(call, state, "courses", "view_courses_all", data, page)


async def get_course_handler(call: CallbackQuery,
                             state: FSMContext):

    data = await state.get_data()
    course = await get_course(call, state)

    text = texts['course_details'].format(
        course['title'],
        course['description'],
        course['price']
    )
    is_buyed = await application_client.check_payment(call.from_user.id,
                                                      course['id'])
    msg = call.message if isinstance(call, CallbackQuery) else call

    await msg.edit_text(
        text=text,
        reply_markup=await course_details_kb(
            course['id'], data['courses_page'], is_buyed['exists']
        )
    )
# ==============================ALL COURSES====================================


# ==============================STUDENT COURSES================================
async def student_courses_handler(call: CallbackQuery,
                                  state: FSMContext,
                                  page: int = 1):
    data = await application_client.get_courses_by_student_id(
        call.from_user.id,
        page
    )
    await create_courses_handler(
        call, state, "student_courses", "view_courses_student", data, page
    )


async def student_course_handler(call: CallbackQuery,
                                 state: FSMContext):
    course_id = await get_course_id(call, state)
    data = await state.update_data(course_id=course_id)
    course = await get_item(call, data['courses'])

    text = texts['course_details'].format(
        course['title'],
        course['description'],
        course['price']
    )

    await call.message.edit_text(
        text=text,
        reply_markup=await buyed_course_details(
            course['id'], data['courses_page']
        )
    )

# ==============================STUDENT COURSES================================


# ==============================UKASSA=========================================

async def start_registeration_proccess(
        call: CallbackQuery,
        state: FSMContext):

    data = await state.get_data()

    bot_msg = await call.message.edit_text(
        text=texts['full_name'],
        reply_markup=await registeration_kb(
            f'courses {data["course_id"]}'
        )
    )
    await state.update_data(bot_msg=bot_msg)
    await state.set_state(UserDataState.FullName)


from http.cookies import SimpleCookie

def generate_cookie_string(access_token: str) -> str:
    """
    Формирует строку куков с токеном доступа.
    """
    cookie = SimpleCookie()
    cookie["access_token"] = access_token
    cookie["access_token"]["path"] = "/"
    cookie["access_token"]["httponly"] = True
    cookie["access_token"]["secure"] = True  # Если используется HTTPS
    return cookie.output(header="", sep="").strip()


async def process_ukassa(call: CallbackQuery, state: FSMContext):
    """
    Обработка запроса оплаты с использованием Web App.
    """
    user = await application_client.get_tg_user(call.from_user.id)
    course = await get_course(call, state)

    # Обновляем токен, если он истёк
    await application_client.ensure_authenticated()

    # Генерируем куки с токеном
    cookie_string = generate_cookie_string(application_client.access_token)

    # Формируем URL с передачей куков
    web_app_url = f"https://kl2jbr.ru/lead-create"
    headers = f"Set-Cookie: {cookie_string}"

    # Создаём кнопку с Web App
    text = f"{texts['invoice_title'].format(course['title'])}\n{texts['invoice_description']}\n{texts['price'].format(course['price'])}"
    button = InlineKeyboardButton(
        text=texts['pay'],
        web_app=WebAppInfo(url=web_app_url)  # Web App URL
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    # Отправляем сообщение с кнопкой
    await call.message.edit_text(text=text, reply_markup=keyboard)



COURSE_VIEW_PAGINATION_GROUP = {
    'page_view_courses_all': all_courses_handler,
    'page_view_courses_student': student_courses_handler
}

course_view_pagination_hendler = create_page_hanler(
    COURSE_VIEW_PAGINATION_GROUP
)


def register_handler(view_router: Router):
    view_router.callback_query.register(
        all_courses_handler,
        F.data == 'courses_btn'
    )
    view_router.callback_query.register(
        course_view_pagination_hendler,
        F.data.startswith('page_view_courses')
    )
    view_router.callback_query.register(
        get_course_handler,
        F.data.startswith('courses')
    )
    view_router.callback_query.register(
        student_course_handler,
        F.data.startswith('student_courses')
    )
    view_router.callback_query.register(
        student_courses_handler,
        F.data.startswith('my_courses')
    )
    view_router.callback_query.register(
        process_ukassa,
        F.data.startswith('ukassa_pay_btn')
    )
  