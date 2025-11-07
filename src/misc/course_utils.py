from typing import Dict, List, Optional
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from urllib.parse import quote

from src.core.settings import application_settings


def is_id_in_item(item: Dict, id: int) -> bool:
    return item.get('id') == id


def receive_item(items: List, item_id: int) -> Dict:
    item = filter(lambda item: is_id_in_item(item, item_id), items)
    return next(item, None)


async def get_item(call: CallbackQuery, items: List):
    item_id = int(call.data.split()[1])

    item = receive_item(items, item_id)
    return item



REDIRECT_ENDPOINT = "/api/v1/courses/link/redirect/"


def build_redirect_url(raw_url: str,
                       user_id: Optional[int],
                       item_type: str) -> str:
    """Формирует redirect-ссылку с логированием."""
    if not raw_url or user_id is None or not item_type:
        return raw_url

    encoded_url = quote(raw_url, safe="")
    base_url = application_settings.APPLICATION_URL.rstrip("/")
    return (
        f"{base_url}{REDIRECT_ENDPOINT}?url={encoded_url}"
        f"&user_id={user_id}&type={item_type}"
    )


def get_item_text(texts: Dict,
                  item: Dict,
                  user_id: Optional[int] = None,
                  item_type: str = "lesson") -> str:
    text = texts['lesson_details'].format(
        item['title'],
        item['content'],
    )

    files = item.get("files_from_storage", [])
    # Фильтруем файлы - оставляем только документы (исключаем type "video")
    documents = [file for file in files if file.get("type") != "video"]
    if documents:
        materials = []
        for doc in documents:
            file_url = build_redirect_url(doc['url'], user_id, item_type)
            materials.append(f"📄 <a href=\"{file_url}\"><b>{doc['name']}</b></a>")
        text = f"{text}\n\n{texts['materials']}\n" + "\n".join(materials)

    video = item.get("video_url")
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
