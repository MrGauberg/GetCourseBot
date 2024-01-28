from aiogram import types
from aiogram.fsm.context import FSMContext
from typing import Callable, Union
from aiogram.fsm.state import State
from aiogram.exceptions import TelegramBadRequest
from src.core.config import bot


def create_page_hanler(group: dict):
    async def page_handler(call: types.CallbackQuery, state: FSMContext):

        page = int(call.data.split()[1])
        await group[call.data.split()[0]](call, state, page)
    return page_handler


def create_back_button_handler(back_list: dict):
    async def back_button_handler(call: types.CallbackQuery,
                                  state: FSMContext):

        suffix = call.data.replace("back_to_", "")
        handler = back_list.get(suffix)
        await handler(call, state)
    return back_button_handler


async def process_step(
        message: Union[types.Message, types.CallbackQuery],
        state: FSMContext,
        text_msg: str,
        model_name: str,
        field: str,
        next_state: State,
        back_to: str,
        keyboard: Callable,
        validator: Callable = None,
        curent_state: State = None,
        not_valid_message: str = None
):
    data = await state.get_data()

    if validator and not validator(message.text.strip()):

        try:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=data['bot_message_id'],
                text=not_valid_message,
                reply_markup=await keyboard(back_to)
            )
            await state.set_state(curent_state)
            await message.delete()
            return

        except TelegramBadRequest:
            bot_message = await bot.send_message(
                chat_id=message.from_user.id,
                text=not_valid_message,
                reply_markup=await keyboard(back_to)
            )
            await bot.delete_message(chat_id=message.from_user.id,
                                     message_id=data['bot_message_id'])
            await state.update_data(bot_message_id=bot_message.message_id)
            await state.set_state(curent_state)
            await message.delete()
            return
    model_data = data[model_name]
    if is_callback(message, 'back_to'):
        await message.message.edit_text(
            text_msg,
            reply_markup=await keyboard(back_to)
            )

        await state.set_state(next_state)
        return

    if isinstance(message, types.Message):
        model_data[field] = message.text.strip()
        await state.update_data(model_name=model_data)
        await message.delete()

    else:
        model_data[field] = message.data
        await state.update_data(model_name=model_data)

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=data['bot_message_id'],
        text=text_msg,
        reply_markup=await keyboard(back_to)
        )
    await state.set_state(next_state)


def is_callback(message: Union[types.Message, types.CallbackQuery],
                callback_data: str):
    if (
        isinstance(message, types.CallbackQuery) and
        message.data.startswith(callback_data)
    ):
        return True
    return False
