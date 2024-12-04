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


#  TODO Payments в России не работает на текущий моментт. Возможно в будущем пригодится.

# async def process_ukassa(call: CallbackQuery, state: FSMContext):

#     user = await application_client.get_tg_user(call.from_user.id)
#     course = await get_course(call, state)

#     if not user['full_name']:
#         await state.update_data(course_id=course['id'])
#         await start_registeration_proccess(call, state)
#         return
#     amount = int(float(course['price'])) * 100
#     bot_invoice = await bot.send_invoice(
#         chat_id=call.from_user.id,
#         title=texts['invoice_title'].format(course['title']),
#         description=texts['invoice_description'],
#         payload=f'ukassa_pay {course["id"]}',
#         provider_token=user_settings.UKASSA_TOKEN,
#         currency='RUB',
#         start_parameter=f'bot_user_{user_settings.USER_ID}',
#         prices=[LabeledPrice(label="Руб", amount=amount)]
#     )
    
#     await state.update_data(bot_invoice=bot_invoice,
#                             current_call_id=call.message.message_id)


# async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):

#     await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# async def process_success_pay(message: Message, state: FSMContext):

#     success_pay = message.successful_payment.invoice_payload
#     data = await state.get_data()

#     if not success_pay.startswith('ukassa_pay'):
#         return
#     course_id = int(success_pay.split()[1])
#     api_data = {'student': message.from_user.id, 'course': course_id}
#     await application_client.create_student_paymant(api_data)

#     try:
#         await data['bot_invoice'].delete()
#     except (TelegramBadRequest, KeyError):
#         pass

#     await bot.edit_message_text(
#         chat_id=message.from_user.id,
#         message_id=data['current_call_id'],
#         text=texts['payments_succesful'],
#         reply_markup=await main_menu()
#     )
#     await message.delete()



from yookassa import Configuration, Payment
from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


async def process_ukassa(call: CallbackQuery, state: FSMContext):
    user = await application_client.get_tg_user(call.from_user.id)
    course = await get_course(call, state)

    if not user['full_name']:
        await state.update_data(course_id=course['id'])
        await start_registeration_proccess(call, state)
        return

    # Настройка конфигурации YooKassa
    Configuration.account_id = user_settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = user_settings.YOOKASSA_SECRET_KEY
    user_tg_name = user_settings.USER_TG_NAME

    # Создание платежа
    payment = Payment.create({
        "amount": {
            "value": f"{course['price']}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/{user_tg_name}"  # Замените на ваш URL
        },
        "capture": True,
        "description": f"Оплата курса {course['title']}",
        "metadata": {
            "user_tg_id": call.from_user.id,
            "course_title": course['title'],
            "admin_id": user_settings.USER_ID
        }
    })

    confirmation_url = payment.confirmation.confirmation_url

    # Сохранение платежа в базе данных через application_client
    await application_client.create_student_paymant({
        "payment_id": payment.id,
        "student": call.from_user.id,
        "course": course['id'],
        "status": payment.status

    })

    # Отправка сообщения пользователю с кнопкой "Оплатить"
    text = f"{texts['invoice_title'].format(course['title'])}\n{texts['invoice_description']}\n{texts['price'].format(course['price'])}"
    button = InlineKeyboardButton(text=texts['pay'], url=confirmation_url)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    await call.message.edit_text(text=text, reply_markup=keyboard)


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
    # view_router.pre_checkout_query.register(
    #     process_pre_checkout
    # )
    # view_router.message.register(
    #     process_success_pay,
    #     F.content_type == ContentType.SUCCESSFUL_PAYMENT
    # )
