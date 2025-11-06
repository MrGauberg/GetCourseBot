import aiofiles
import logging
from urllib.parse import quote
from src.core.config import texts, bot
from src.handlers.course import start_registeration_proccess
from src.handlers.registration import full_name_proccess
from src.services.application_client import application_client
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ContentType

from src.keyboards.main_menu_kb import (
    assignment_kb, assignment_respones_kb, lesson_details_kb
)
from src.misc.course_utils import get_item, get_item_text
from src.misc.fabrics import create_back_button_handler
from src.misc.validator import is_valid_url, is_all_fields_blank
from src.misc.init_data_generator import generate_telegram_initdata
from src.core.settings import application_settings, user_settings
from src.core.config import texts as config_texts
from src.states import AssignmentState
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import os
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


async def assignment_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(state=None)

    data = await state.get_data()
    assignment = await get_item(call, data['assignments'])
    response = await application_client.check_assignment_response(
        call.from_user.id, assignment['id']
    )

    text = get_item_text(texts, assignment, call.from_user.id)

    await call.message.edit_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=await assignment_kb(assignment['lesson'], assignment['id'], response['exists'], assignment)
    )


async def pull_assignment_process(call: CallbackQuery, state: FSMContext):
    parts         = call.data.split()
    assignment_id = int(parts[1])
    is_webhook    = len(parts) > 2 and parts[2] == "wb"

    const_text = texts["TextState"]
    kb = await assignment_respones_kb(
        f"homework {assignment_id}",
        back_button=not is_webhook
    )

    if is_webhook:
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        bot_message = await call.message.answer(
            const_text,
            reply_markup=kb
        )
    else:
        bot_message = await call.message.edit_text(
            const_text,
            reply_markup=kb
        )

    await state.update_data(
        assignment_model={
            "assignment": assignment_id,
            "student":    call.from_user.id
        },
        bot_message_id=bot_message.message_id
    )
    await state.set_state(AssignmentState.Text)


async def assignment_text_process(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        data['assignment_model']['text'] = message.text.strip()
        await message.delete()
    except AttributeError:
        data['assignment_model']['text'] = None

    await state.update_data(assignment_model=data['assignment_model'])

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=data['bot_message_id'],
        text=texts['VideoState'],
        reply_markup=await assignment_respones_kb(
            f'pull_assignment {data["assignment_model"]["assignment"]}'
        )
    )
    await state.set_state(AssignmentState.Video)


async def assignment_video_process(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        link = message.text.strip()
        if not is_valid_url(link):
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=data['bot_message_id'],
                text=texts["not_true_link"],
                reply_markup=await assignment_respones_kb(
                    'back_to_assignment_text_state'
                )
            )
            await state.set_state(AssignmentState.Video)
            return

        data['assignment_model']['video_url'] = link
        await message.delete()
    except AttributeError:
        data['assignment_model']['video_url'] = None

    data['assignment_model']['bot_msg_text'] = texts['DocumentState']
    await state.update_data(assignment_model=data['assignment_model'])
    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=data['bot_message_id'],
        text=texts['DocumentState'],
        reply_markup=await assignment_respones_kb(
            'back_to_assignment_text_state',
            skip_button=False,
            finish_assignment=True
        )
    )
    await state.set_state(AssignmentState.Documents)


async def assignment_doc_process(message: Message, state: FSMContext):
    data = await state.get_data()
    files = data.get('files', [])
    text = data['assignment_model'].get('bot_msg_text')
    content_type = message.content_type if isinstance(message, Message) else None

    if content_type == ContentType.DOCUMENT:
        document = message.document
        file_id = document.file_id
        original_name = document.file_name  # например "Новый док (18).docx"
        user_id = message.from_user.id

        # Разбиваем имя и расширение
        base_name, ext = os.path.splitext(original_name)
        save_dir = "documents"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Формируем имя с user_id перед расширением
        candidate_name = f"{base_name}_{user_id}{ext}"
        file_path_to_save = os.path.join(save_dir, candidate_name)

        # Если существует — добавляем порядковый номер
        counter = 1
        while os.path.exists(file_path_to_save) or file_path_to_save in files:
            candidate_name = f"{base_name}_{user_id}_{counter}{ext}"
            file_path_to_save = os.path.join(save_dir, candidate_name)
            counter += 1

        # Скачиваем и сохраняем
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=file_path_to_save)

        files.append(file_path_to_save)
        if len(files) == 1:
            text += "\n\n" + texts["file_received"] + "\n\n"

        # показываем пользователю оригинальное имя файла
        text += f"\n{len(files)}. {original_name}"
        data['assignment_model']['bot_msg_text'] = text

        await state.update_data(files=files, assignment_model=data['assignment_model'])
        await message.delete()
        await bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=data['bot_message_id'],
            text=text,
            reply_markup=await assignment_respones_kb(
                'back_to_assignment_text_state',
                finish_assignment=True,
                skip_button=False
            )
        )


async def finish_assignment_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    files = data.get('files', [])
    array = [
        data['assignment_model'].get('text'),
        data['assignment_model'].get('video_url'),
        files
    ]
    if is_all_fields_blank(array):
        # Получаем lesson из state если доступен
        lesson = data.get('lesson')
        await bot.edit_message_text(
            chat_id=call.from_user.id,
            message_id=data['bot_message_id'],
            text=texts['all_element_blank'],
            reply_markup=await lesson_details_kb(
                data['lessons_page'], data['assignments'], lesson),
            disable_web_page_preview=True
        )
        await state.set_state(None)
        return

    # Подготовка массивов для отправки
    file_tuples = []
    for file_path in files:
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            name = os.path.basename(file_path)
            file_tuples.append(('files', (name, content, 'application/octet-stream')))
        await sync_to_async(os.remove)(file_path)

    await application_client.create_assignment_response(
        data['assignment_model'], files=file_tuples
    )
    await state.clear()
    user_id = call.from_user.id
    await bot.edit_message_text(
        chat_id=user_id,
        message_id=data['bot_message_id'],
        text=texts['assignment_created_success'],
        reply_markup=await assignment_respones_kb(
            'back_to_assignment_text_state',
            back_button=False,
            skip_button=False
        )
    )


async def get_files(file_path: str):
    async with aiofiles.open(file_path, 'rb') as file:
        content = await file.read()
        name = os.path.basename(file_path)
        return [('files', (name, content, 'application/octet-stream'))]


BACK_ASSIGNMENT_CALLBACKS = {
    "assignment_text_state": assignment_text_process,
    "user_full_name_state": start_registeration_proccess,
    "user_email_state": full_name_proccess,
}

back_handler = create_back_button_handler(BACK_ASSIGNMENT_CALLBACKS)


async def assignment_videos_pagination_handler(call: CallbackQuery, state: FSMContext):
    """Обработчик пагинации для видео заданий"""
    parts = call.data.split()
    assignment_id = int(parts[1])
    page = int(parts[2])
    await show_assignment_videos_handler(call, state, page)


async def show_assignment_videos_handler(call: CallbackQuery, state: FSMContext, page: int = 1):
    """Обработчик для отображения списка видео задания с пагинацией"""
    assignment_id = int(call.data.split()[1])
    
    # Получаем данные задания для возврата назад
    data = await state.get_data()
    assignments = data.get('assignments', [])
    assignment = next((a for a in assignments if a['id'] == assignment_id), None)
    
    # Callback для возврата назад к заданию
    back_callback = f"homework {assignment_id}"
    
    try:
        # Проверяем, есть ли уже сохраненные видео в state для этого задания
        saved_assignment_id = data.get('assignment_id')
        all_videos = data.get('assignment_videos', [])
        
        # Если это первый запрос или другое задание - загружаем видео
        if not all_videos or saved_assignment_id != assignment_id:
            # Генерируем initData для API запроса (без query_id и signature - для этого достаточно)
            init_data = generate_telegram_initdata(call.from_user.id, user_settings.BOT_TOKEN)
            logger.info(f"[show_assignment_videos_handler] Загружаем видео для assignment_id={assignment_id}, user_id={call.from_user.id}")
            
            # Получаем список всех видео
            videos_response = await application_client.get_videos_by_assignment_id(assignment_id, init_data)
            
            # Обрабатываем как словарь с results, так и список
            if isinstance(videos_response, dict):
                all_videos = videos_response.get('results', [])
            elif isinstance(videos_response, list):
                all_videos = videos_response
            else:
                all_videos = []
            
            # Сохраняем все видео в state
            await state.update_data(assignment_videos=all_videos, assignment_id=assignment_id)
        else:
            # Используем сохраненные видео
            logger.info(f"[show_assignment_videos_handler] Используем сохраненные видео для assignment_id={assignment_id}, страница {page}")
        
        if len(all_videos) == 0:
            # Нет видео
            await call.message.edit_text(
                text=config_texts['video_not_found'],
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
                web_app_url = f"https://{application_settings.WEB_APP_URL}/player/?assignment={assignment_id}&video_id={video['id']}&init_data={quote(init_data)}&back_callback={quote(back_callback)}"
                logger.info(f"[show_assignment_videos_handler] URL плеера для video_id={video['id']} с initData и back_callback: {web_app_url}")
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
                nav_buttons.append(InlineKeyboardButton(text="<", callback_data=f"page_view_assignment_videos {assignment_id} {page - 1}"))
            nav_buttons.append(InlineKeyboardButton(text=" ", callback_data="none"))
            if end_idx < len(all_videos):
                nav_buttons.append(InlineKeyboardButton(text=">", callback_data=f"page_view_assignment_videos {assignment_id} {page + 1}"))
            
            if nav_buttons:
                buttons.append(nav_buttons)
            
            # Добавляем кнопку "Назад" для возврата к заданию
            buttons.append([
                InlineKeyboardButton(
                    text=config_texts['back_button'],
                    callback_data=back_callback
                )
            ])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await call.message.edit_text(
                text=config_texts['choose_video'],
                reply_markup=keyboard
            )
    except Exception as e:
        await call.message.edit_text(
            text=f"Ошибка при получении видео: {str(e)}",
            reply_markup=None
        )


def register_handler(view_router: Router, form_router: Router):
    view_router.callback_query.register(
        assignment_handler,
        F.data.startswith('homework')
    )
    view_router.callback_query.register(
        pull_assignment_process,
        F.data.startswith('pull_assignment')
    )
    view_router.callback_query.register(
        back_handler,
        F.data.startswith('back_to_')
    )
    form_router.message.register(
        assignment_text_process,
        AssignmentState.Text
    )
    form_router.callback_query.register(
        assignment_text_process,
        AssignmentState.Text
    )
    form_router.message.register(
        assignment_video_process,
        AssignmentState.Video
    )
    form_router.callback_query.register(
        assignment_video_process,
        AssignmentState.Video
    )
    form_router.message.register(
        assignment_doc_process,
        AssignmentState.Document
    )
    form_router.callback_query.register(
        assignment_doc_process,
        AssignmentState.Document
    )
    form_router.message.register(
        assignment_doc_process,
        AssignmentState.Documents
    )
    form_router.callback_query.register(
        assignment_doc_process,
        AssignmentState.Documents
    )
    view_router.callback_query.register(
        finish_assignment_handler,
        F.data == "finish_assignment"
    )
    view_router.callback_query.register(
        show_assignment_videos_handler,
        F.data.startswith('show_assignment_videos')
    )
    view_router.callback_query.register(
        assignment_videos_pagination_handler,
        F.data.startswith('page_view_assignment_videos')
    )
