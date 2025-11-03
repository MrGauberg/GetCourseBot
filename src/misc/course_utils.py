from typing import Dict, List
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext


def is_id_in_item(item: Dict, id: int) -> bool:
    return item.get('id') == id


def receive_item(items: List, item_id: int) -> Dict:
    item = filter(lambda item: is_id_in_item(item, item_id), items)
    return next(item, None)


async def get_item(call: CallbackQuery, items: List):
    item_id = int(call.data.split()[1])

    item = receive_item(items, item_id)
    return item



def get_item_text(texts: Dict, lesson: Dict) -> str:
    text = texts['lesson_details'].format(
        lesson['title'],
        lesson['content'],
    )

    files = lesson.get("files_from_storage", [])
    # Фильтруем файлы - оставляем только документы (исключаем type "video")
    documents = [file for file in files if file.get("type") != "video"]
    if documents:
        materials = "\n".join(
            [f"📄 <a href=\"{doc['url']}\"><b>{doc['name']}</b></a>" for doc in documents]
        )
        text = f"{text}\n\n{texts['materials']}\n{materials}"

    video = lesson.get("video_url")
    if video:
        text = f"{text}\n\n{texts['video'].format(video)}"

    return text





async def get_course_id(call: CallbackQuery,
                        state: FSMContext):
    data = await state.get_data()
    try:
        course_id = int(call.data.split()[1])
    except AttributeError:
        course_id = data['course_id']
    return course_id


async def get_course(call: CallbackQuery,
                     state: FSMContext):
    data = await state.get_data()

    course_id = await get_course_id(call, state)
    course = receive_item(data['courses'], course_id)
    return course
