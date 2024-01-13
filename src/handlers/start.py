from aiogram.fsm.context import FSMContext
from aiogram import Router, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from src.core.config import texts
from src.core.settings import user_settings
from src.keyboards.main_menu_kb import main_menu
from src.services.application_client import application_client
from typing import Union


async def on_start(message: Message):
    tg_user_data = {
        'tg_id': message.from_user.id,
        'user_name': message.from_user.username,
        'teacher_id': user_settings.USER_ID
    }
    await application_client.create_students(tg_user_data)
    await message.answer(
        text=texts['start_text'],
        reply_markup=await main_menu()
    )


async def start_cmd_handler(message: Union[Message, CallbackQuery],
                            state: FSMContext):

    await state.clear()
    if isinstance(message, Message):
        await on_start(message)
    else:
        await message.message.edit_text(
            text=texts['start_text'],
            reply_markup=await main_menu()
        )


def register_handler(dp: Dispatcher):
    dp.message.register(
        start_cmd_handler,
        CommandStart()
    )
    dp.callback_query.register(
        start_cmd_handler,
        F.data == "back_to_main_menu"
    )
