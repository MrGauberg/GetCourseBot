from typing import Dict, List
from aiogram.types import CallbackQuery


def is_id_in_item(item: Dict, id: int) -> bool:
    return item.get('id') == id


def receive_item(items: List, item_id: int) -> Dict:
    item = filter(lambda item: is_id_in_item(item, item_id), items)
    return next(item, None)


async def get_item(call: CallbackQuery, items: List):
    item_id = int(call.data.split()[1])

    item = receive_item(items, item_id)
    return item


def get_item_text(texts: Dict, lesson: Dict):
    video = texts['video'].format(lesson.get("video_url")) \
        if lesson.get("video_url") else ""
    document = texts['document'].format(lesson.get("document")) \
        if lesson.get("document") else ""

    text = texts['lesson_details'].format(
        lesson['title'],
        lesson['content'],
    )
    text = f"{text}\n\n{video}\n\n{document}"

    return text
