from typing import Dict, List
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


def is_id_in_course(course: Dict, id: int) -> bool:
    return course.get('id') == id


def receive_course(courses: List, course_id: int) -> Dict:
    item = filter(lambda course: is_id_in_course(course, course_id), courses)
    return next(item, None)


async def get_course(call: CallbackQuery,
                     state: FSMContext):
    course_id = int(call.data.split()[1])

    data = await state.get_data()
    course = receive_course(data['courses'], course_id)
    return course
