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
                                item_type: Optional[str] = None,
                                course_id: Optional[int] = None,
                                lesson_id: Optional[int] = None,
                                assignment_id: Optional[int] = None) -> str:
    """Добавляет параметры user_id и type в query URL (если переданы)."""
    if not url:
        return url

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    if user_id is not None:
        query_params['user_id'] = [str(user_id)]

    if item_type:
        query_params['type'] = [item_type]

    if item_type == "lesson":
        if course_id is not None:
            query_params['course_id'] = [str(course_id)]
        if lesson_id is not None:
            query_params['lesson_id'] = [str(lesson_id)]
    elif item_type == "assignment":
        if assignment_id is not None:
            query_params['assignment_id'] = [str(assignment_id)]

    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)


def build_redirect_url(original_url: str,
                       user_id: int,
                       item_type: str,
                       course_id: Optional[int] = None,
                       lesson_id: Optional[int] = None,
                       assignment_id: Optional[int] = None) -> str:
    base_host = application_settings.WEB_APP_URL.rstrip("/")
    if not base_host.startswith(("http://", "https://")):
        base_host = f"https://{base_host}"

    query_params = {
        "url": original_url,
        "user_id": str(user_id),
        "type": item_type,
    }

    if item_type == "lesson":
        if course_id is not None:
            query_params["course_id"] = str(course_id)
        if lesson_id is not None:
            query_params["lesson_id"] = str(lesson_id)
    elif item_type == "assignment":
        if assignment_id is not None:
            query_params["assignment_id"] = str(assignment_id)

    query_string = urlencode(query_params, quote_via=quote)
    return f"{base_host}/api/v1/courses/link/redirect/?{query_string}"


def get_item_text(texts: Dict,
                  item: Dict,
                  user_id: Optional[int] = None,
                  item_type: str = "lesson",
                  course_id: Optional[int] = None,
                  lesson_id: Optional[int] = None,
                  assignment_id: Optional[int] = None) -> str:
    text = texts['lesson_details'].format(
        item['title'],
        item['content'],
    )

    files = item.get("files_from_storage", [])
    # Фильтруем файлы - оставляем только документы (исключаем type "video")
    documents = [file for file in files if file.get("type") != "video"]
    inferred_lesson_id = lesson_id if lesson_id is not None else (item.get('id') if item_type == "lesson" else None)
    inferred_assignment_id = assignment_id if assignment_id is not None else (item.get('id') if item_type == "assignment" else None)
    if documents:
        materials = []
        for doc in documents:
            file_url = doc['url']
            file_url = _add_tracking_params_to_url(
                file_url,
                user_id,
                item_type,
                course_id=course_id,
                lesson_id=inferred_lesson_id,
                assignment_id=inferred_assignment_id,
            )
            safe_file_url = escape(file_url, quote=True)
            materials.append(f"📄 <a href=\"{safe_file_url}\"><b>{doc['name']}</b></a>")
        text = f"{text}\n\n{texts['materials']}\n" + "\n".join(materials)

    video = item.get("video_url")
    if video:
        video_link = build_redirect_url(
            video,
            user_id,
            item_type,
            course_id=course_id,
            lesson_id=inferred_lesson_id,
            assignment_id=inferred_assignment_id,
        ) if user_id is not None else video
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
