from src.core.config import texts
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.keyboards.main_menu_kb import assigment_kb, lesson_details_kb
from src.keyboards.pagination_kb import generate_db_items_keyboard
from src.misc.course_utils import get_item, get_item_text
from src.misc.fabrics import create_page_hanler
from src.services.application_client import application_client


async def assigment_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    assigment = await get_item(call, data['assigments'])

    text = get_item_text(texts, assigment)

    await call.message.edit_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=await assigment_kb(assigment['lesson'])
    )


def register_handler(view_router: Router):
    view_router.callback_query.register(
        assigment_handler,
        F.data.startswith('homework')
    )
