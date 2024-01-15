from src.core.config import texts
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.keyboards.main_menu_kb import lesson_details_kb
from src.keyboards.pagination_kb import generate_db_items_keyboard
from src.misc.course_utils import get_item, get_item_text
from src.misc.fabrics import create_page_hanler
from src.services.application_client import application_client


async def lessons_handler(call: CallbackQuery,
                          state: FSMContext,
                          page: int = 1):
    data = await state.get_data()
    lessons = await application_client.get_lessons_by_course_id(
        data['course_id'], page
    )
    await state.update_data(lessons=lessons['results'],
                            lessons_page=page)
    lessons_list_kb = await generate_db_items_keyboard(
        page,
        lessons['results'],
        lessons['next'],
        lessons['previous'],
        "lessons",
        f"student_courses {data['course_id']}",
        "view_lessons"
    )
    await call.message.edit_text(
        text=texts['choose_lessons'],
        reply_markup=lessons_list_kb.as_markup()
    )


async def lesson_handler(call: CallbackQuery,
                         state: FSMContext):
    data = await state.get_data()
    lesson = await get_item(call,  data['lessons'])

    text = get_item_text(texts, lesson)

    assigments = await application_client.get_assignments_by_lesson_id(
        lesson['id']
    )
    await state.update_data(assigments=assigments)
    await call.message.edit_text(
        text=text,
        reply_markup=await lesson_details_kb(
            data['lessons_page'], assigments),
        disable_web_page_preview=True
    )

LESSON_VIEW_PAGINATION_GROUP = {
    'page_view_lessons': lessons_handler,
}

lesson_view_pagination_hendler = create_page_hanler(
    LESSON_VIEW_PAGINATION_GROUP
)


def register_handler(view_router: Router):
    view_router.callback_query.register(
        lessons_handler,
        F.data.startswith('course_lessons')
    )
    view_router.callback_query.register(
        lesson_view_pagination_hendler,
        F.data.startswith('page_view_lessons')
    )
    view_router.callback_query.register(
        lesson_handler,
        F.data.startswith('lessons')
    )
