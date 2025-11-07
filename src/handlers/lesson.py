import logging
from urllib.parse import quote
from src.core.config import texts
from src.core.settings import application_settings, user_settings
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from src.keyboards.main_menu_kb import lesson_details_kb
from src.keyboards.pagination_kb import generate_db_items_keyboard
from src.misc.course_utils import get_item, get_item_text
from src.misc.fabrics import create_page_hanler
from src.misc.init_data_generator import generate_telegram_initdata
from src.services.application_client import application_client

logger = logging.getLogger(__name__)


async def lessons_handler(call: CallbackQuery,
                          state: FSMContext,
                          page: int = 1):
    data = await state.get_data()
    lessons = await application_client.get_lessons_by_course_id(
        data['course_id'], page, call.from_user.id
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

    text = get_item_text(texts, lesson, call.from_user.id, item_type="lesson")

    assignments = await application_client.get_assignments_by_lesson_id(
        lesson['id'], call.from_user.id
    )
    await state.update_data(assignments=assignments, lesson=lesson)
    await call.message.edit_text(
        text=text,
        reply_markup=await lesson_details_kb(
            data['lessons_page'], assignments, lesson),
        disable_web_page_preview=True
    )

LESSON_VIEW_PAGINATION_GROUP = {
    'page_view_lessons': lessons_handler,
}

lesson_view_pagination_hendler = create_page_hanler(
    LESSON_VIEW_PAGINATION_GROUP
)


async def lesson_videos_pagination_handler(call: CallbackQuery, state: FSMContext):
    """Обработчик пагинации для видео уроков"""
    parts = call.data.split()
    lesson_id = int(parts[1])
    page = int(parts[2])
    await show_lesson_videos_handler(call, state, page)


async def show_lesson_videos_handler(call: CallbackQuery, state: FSMContext, page: int = 1):
    """Обработчик для отображения списка видео урока с пагинацией"""
    lesson_id = int(call.data.split()[1])
    
    # Получаем данные урока для возврата назад
    data = await state.get_data()
    lesson = data.get('lesson')
    if not lesson:
        # Если урока нет в state, пытаемся получить из списка уроков
        lessons = data.get('lessons', [])
        lesson = next((l for l in lessons if l['id'] == lesson_id), None)
    
    # Callback для возврата назад к уроку
    back_callback = f"lessons {lesson_id}"
    
    try:
        # Проверяем, есть ли уже сохраненные видео в state для этого урока
        saved_lesson_id = data.get('lesson_id')
        all_videos = data.get('lesson_videos', [])
        
        # Если это первый запрос или другой урок - загружаем видео
        if not all_videos or saved_lesson_id != lesson_id:
            # Генерируем initData для API запроса (без query_id и signature - для этого достаточно)
            init_data = generate_telegram_initdata(call.from_user.id, user_settings.BOT_TOKEN)
            logger.info(f"[show_lesson_videos_handler] Загружаем видео для lesson_id={lesson_id}, user_id={call.from_user.id}")
            
            # Получаем список всех видео
            videos_response = await application_client.get_videos_by_lesson_id(lesson_id, init_data)
            
            # Обрабатываем как словарь с results, так и список
            if isinstance(videos_response, dict):
                all_videos = videos_response.get('results', [])
            elif isinstance(videos_response, list):
                all_videos = videos_response
            else:
                all_videos = []
            
            # Сохраняем все видео в state
            await state.update_data(lesson_videos=all_videos, lesson_id=lesson_id)
        else:
            # Используем сохраненные видео
            logger.info(f"[show_lesson_videos_handler] Используем сохраненные видео для lesson_id={lesson_id}, страница {page}")
        
        if len(all_videos) == 0:
            # Нет видео
            await call.message.edit_text(
                text=texts['video_not_found'],
                reply_markup=None
            )
        else:
            # Генерируем initData для URL плеера
            init_data = generate_telegram_initdata(call.from_user.id, user_settings.BOT_TOKEN)
            
            # Пагинация: показываем по 4 видео на странице
            videos_per_page = 4
            start_idx = (page - 1) * videos_per_page
            end_idx = start_idx + videos_per_page
            videos = all_videos[start_idx:end_idx]
            
            # Создаем кнопки для видео (максимум 4)
            buttons = []
            for video in videos:
                # Убираем расширение из названия файла
                video_name = video['filename'].rsplit('.', 1)[0] if '.' in video['filename'] else video['filename']
                # Передаем initData и back_callback через URL параметр для плеера
                web_app_url = f"https://{application_settings.WEB_APP_URL}/player/?lesson={lesson_id}&video_id={video['id']}&init_data={quote(init_data)}&back_callback={quote(back_callback)}"
                logger.info(f"[show_lesson_videos_handler] URL плеера для video_id={video['id']} с initData и back_callback: {web_app_url}")
                buttons.append([
                    InlineKeyboardButton(
                        text=video_name,
                        web_app=WebAppInfo(url=web_app_url)
                    )
                ])
            
            # Заполняем остаток пустыми кнопками до 4
            while len(buttons) < videos_per_page:
                buttons.append([
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="none"
                    )
                ])
            
            # Добавляем кнопки навигации
            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton(text="<", callback_data=f"page_view_lesson_videos {lesson_id} {page - 1}"))
            nav_buttons.append(InlineKeyboardButton(text=" ", callback_data="none"))
            if end_idx < len(all_videos):
                nav_buttons.append(InlineKeyboardButton(text=">", callback_data=f"page_view_lesson_videos {lesson_id} {page + 1}"))
            
            if nav_buttons:
                buttons.append(nav_buttons)
            
            # Добавляем кнопку "Назад" для возврата к уроку
            buttons.append([
                InlineKeyboardButton(
                    text=texts['back_button'],
                    callback_data=back_callback
                )
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await call.message.edit_text(
                text=texts['choose_video'],
                reply_markup=keyboard
            )
    except Exception as e:
        await call.message.edit_text(
            text=f"Ошибка при получении видео: {str(e)}",
            reply_markup=None
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
    view_router.callback_query.register(
        show_lesson_videos_handler,
        F.data.startswith('show_lesson_videos')
    )
    view_router.callback_query.register(
        lesson_videos_pagination_handler,
        F.data.startswith('page_view_lesson_videos')
    )
