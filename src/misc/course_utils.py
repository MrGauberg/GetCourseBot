from typing import Dict, List, Optional
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse, quote
from html import escape
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



def _add_tracking_params_to_url(url: str,
                                user_id: Optional[int] = None,
                                item_type: Optional[str] = None) -> str:
    """Добавляет параметры user_id и type в query URL (если переданы)."""
    if not url:
        return url

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    if user_id is not None:
        query_params['user_id'] = [str(user_id)]

    if item_type:
        query_params['type'] = [item_type]

    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)


def build_redirect_url(original_url: str, user_id: int, item_type: str) -> str:
    encoded_url = quote(original_url, safe="")
    base_url = application_settings.APPLICATION_URL.rstrip("/")
    return (
        f"{base_url}/courses/link/redirect/?"
        f"url={encoded_url}&user_id={user_id}&type={item_type}"
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
            file_url = doc['url']
            file_url = _add_tracking_params_to_url(file_url, user_id, item_type)
            safe_file_url = escape(file_url, quote=True)
            materials.append(f"📄 <a href=\"{safe_file_url}\"><b>{doc['name']}</b></a>")
        text = f"{text}\n\n{texts['materials']}\n" + "\n".join(materials)

    video = item.get("video_url")
    if video:
        video_link = build_redirect_url(video, user_id, item_type) if user_id is not None else video
        safe_video_link = escape(video_link, quote=True)
        text = f"{text}\n\n{texts['video'].format(safe_video_link)}"

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
