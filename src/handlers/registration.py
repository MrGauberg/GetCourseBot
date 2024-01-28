from aiogram import Router
from src.core.config import texts, bot
from src.handlers.course import get_course_handler, process_ukassa, student_course_handler
from src.keyboards.main_menu_kb import phone_number_keyboard, registeration_kb
from src.misc.validator import is_valid_email
from src.services.application_client import application_client
from src.states import UserDataState
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext


async def full_name_proccess(msg: Message, state: FSMContext):
    data = await state.get_data()

    reply_keyboard = data.pop('reply_keyboard', None)
    try:
        await reply_keyboard.delete()
    except (TelegramBadRequest, AttributeError):
        pass

    try:
        await state.update_data(full_name=msg.text.strip())
    except AttributeError:
        pass

    await data['bot_msg'].edit_text(
        text=texts['email'],
        reply_markup=await registeration_kb(
            'back_to_user_full_name_state'
        )
    )

    await state.set_state(UserDataState.Email)
    await msg.delete()


async def email_proccess(msg: Message, state: FSMContext):
    data = await state.get_data()
    if not is_valid_email(msg.text.strip()):
        await state.set_state(UserDataState.Email)

    else:
        await data['bot_msg'].edit_text(
            text=texts['phone_number'],
            reply_markup=await registeration_kb(
                'back_to_user_email_state'
            )
        )
        phone_keyboard = await phone_number_keyboard()
        reply_keyboard = await bot.send_message(chat_id=msg.from_user.id, text="\u2063", reply_markup=phone_keyboard.as_markup())
        await state.update_data(reply_keyboard=reply_keyboard)

        await state.update_data(email=msg.text.strip())
        await state.set_state(UserDataState.PhoneNumber)

    await msg.delete()


async def phone_number_proccess(msg: Message, state: FSMContext):
    data = await state.update_data(
        phone_number='+' + msg.contact.phone_number
    )
    reply_keyboard = data.pop('reply_keyboard')
    await reply_keyboard.delete()

    await execut_proccess(msg.from_user.id, state)
    await msg.delete()


async def execut_proccess(user_id: int, state: FSMContext):
    data = await state.get_data()

    user_data = {
        'full_name': data['full_name'],
        'phone_number': data['phone_number'],
        'email': data['email']
    }
    await application_client.update_tg_user(user_id, user_data)
    await get_course_handler(data['bot_msg'], state)


def register_handler(form_router: Router):

    form_router.message.register(
        full_name_proccess,
        UserDataState.FullName
    )
    form_router.message.register(
        phone_number_proccess,
        UserDataState.PhoneNumber
    )
    form_router.message.register(
        email_proccess,
        UserDataState.Email
    )
