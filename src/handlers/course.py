from aiogram.fsm.context import FSMContext
from aiogram import Router, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from src.core.config import texts
from src.keyboards.main_menu_kb import main_menu
from src.keyboards.pagination_kb import generate_db_items_keyboard
from src.misc.fabrics import create_page_hanler
from src.services.application_client import application_client
from src.core.settings import user_settings


async def get_courses_handler(call: CallbackQuery,
                              state: FSMContext,
                              page: int = 1):
    data = await application_client.get_courses_by_user_id(
        user_settings.USER_ID,
        page=page
    )
    await state.update_data(course_details=data['results'])
    course_list_kb = await generate_db_items_keyboard(
        page,
        data['results'],
        data['next'],
        data['previous'],
        "courses",
        "back_to_main_menu",
        "view_courses"
    )
    await call.message.edit_text(
        text=texts['choose_course'],
        reply_markup=course_list_kb.as_markup()
    )


COURSE_VIEW_PAGINATION_GROUP = {
    'page_view_courses': get_courses_handler
}

course_view_pagination_hendler = create_page_hanler(
    COURSE_VIEW_PAGINATION_GROUP
)


def register_handler(view_router: Router):
    view_router.callback_query.register(
        get_courses_handler,
        F.data == 'courses_btn'
    )
    view_router.callback_query.register(
        course_view_pagination_hendler,
        F.data.startswith('page_view_courses')
    )
