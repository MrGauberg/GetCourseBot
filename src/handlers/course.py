from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, LabeledPrice, PreCheckoutQuery, Message, ContentType
)
from src.core.config import texts, bot
from src.keyboards.main_menu_kb import (
    buyed_course_details, course_details_kb
)
from src.keyboards.pagination_kb import generate_db_items_keyboard
from src.misc.course_utils import get_course
from src.misc.fabrics import create_page_hanler
from src.services.application_client import application_client
from src.core.settings import user_settings
from aiogram.exceptions import TelegramBadRequest


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

    course = await get_course(call, state)
    data = await state.get_data()

    text = texts['course_details'].format(
        course['title'],
        course['description'],
        course['price']
    )
    is_buyed = await application_client.check_payment(call.from_user.id,
                                                      course['id'])
    await call.message.edit_text(
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
    course = await get_course(call, state)
    data = await state.get_data()

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
async def process_ukassa(call: CallbackQuery, state: FSMContext):
    course = await get_course(call, state)

    bot_invoice = await bot.send_invoice(
        chat_id=call.from_user.id,
        title=texts['invoice_title'].format(course['title']),
        description=texts['invoice_description'],
        payload=f'ukassa_pay {course["id"]}',
        provider_token=user_settings.UKASSA_TOKEN,
        currency='RUB',
        start_parameter=f'bot_user_{user_settings.USER_ID}',
        prices=[LabeledPrice(label="Руб", amount=int(float(course['price'])) * 100)]
    )

    await state.update_data(bot_invoice=bot_invoice,
                            current_call_id=call.message.message_id)


async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):

    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def process_success_pay(message: Message, state: FSMContext):

    success_pay = message.successful_payment.invoice_payload
    data = await state.get_data()

    if not success_pay.startswith('ukassa_pay'):
        return
    course_id = int(success_pay.split()[1])
    api_data = {'student': message.from_user.id, 'course': course_id}
    await application_client.create_student_paymant(api_data)

    try:
        await data['bot_invoice'].delete()
    except (TelegramBadRequest, KeyError):
        pass

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=data['current_call_id'],
        text=texts['payments_succesful'],
        reply_markup=await main_menu()
    )
    await message.delete()
# ==============================UKASSA=========================================

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
    view_router.pre_checkout_query.register(
        process_pre_checkout
    )
    view_router.message.register(
        process_success_pay,
        F.content_type == ContentType.SUCCESSFUL_PAYMENT
    )
