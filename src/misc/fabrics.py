from aiogram import types
from aiogram.fsm.context import FSMContext


def create_page_hanler(group: dict):
    async def page_handler(call: types.CallbackQuery, state: FSMContext):

        page = int(call.data.split()[1])
        await group[call.data.split()[0]](call, state, page)
    return page_handler
