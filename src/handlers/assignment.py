
import aiofiles
from src.core.config import texts, bot
from src.services.application_client import application_client
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from src.keyboards.main_menu_kb import (
    assignment_kb, assignment_respones_kb, lesson_details_kb
)
from src.misc.course_utils import get_item, get_item_text
from src.misc.fabrics import create_back_button_handler
from src.misc.validator import is_valid_url, is_all_fields_blank
from src.states import AssignmentState
import os
from asgiref.sync import sync_to_async


async def assignment_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(state=None)

    data = await state.get_data()
    assignment = await get_item(call, data['assignments'])
    response = await application_client.check_assignment_response(
        call.from_user.id, assignment['id']
    )

    text = get_item_text(texts, assignment)

    await call.message.edit_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=await assignment_kb(assignment['lesson'], assignment['id'], response['exists'])
    )


async def pull_assignment_process(call: CallbackQuery, state: FSMContext):

    assignment_id = int(call.data.split()[1])
    bot_message = await call.message.edit_text(
        texts["TextState"],
        reply_markup=await assignment_respones_kb(f"homework {assignment_id}")
    )
    await state.update_data(
        assignment_model={
            "assignment": assignment_id,
            "student": call.from_user.id
        },
        bot_message_id=bot_message.message_id)
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

        data['assignment_model']['video'] = link
        await message.delete()
    except AttributeError:
        data['assignment_model']['video'] = None
        pass
    await state.update_data(assignment_model=data['assignment_model'])
    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=data['bot_message_id'],
        text=texts['DocumentState'],
        reply_markup=await assignment_respones_kb(
            'back_to_assignment_text_state'
        )
    )
    await state.set_state(AssignmentState.Document)


async def assignment_doc_process(message: Message, state: FSMContext):
    data = await state.get_data()
    files = None
    try:
        document = message.document
        file_id = document.file_id

        # Получение file_path от Telegram
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_name = file_path.split('/')[-1]
        # Скачивание файла
        file_path_to_save = f"documents/temp_{file_id}_{file_name}"
        await bot.download_file(file_path, destination=file_path_to_save)

        # Подготовка файлов для отправки
        files = await get_files(file_path_to_save)
        await sync_to_async(os.remove)(file_path_to_save)
        await message.delete()
    except AttributeError:
        array = [
            data['assignment_model']['text'],
            data['assignment_model']['video'],
            ]
        if is_all_fields_blank(array):
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=data['bot_message_id'],
                text=texts['all_element_blank'],
                reply_markup=await lesson_details_kb(
                    data['lessons_page'], data['assignments']),
                disable_web_page_preview=True
            )
            return

    await application_client.create_assignment_response(
        data['assignment_model'], files=files
        )
    await state.set_state(state=None)
    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=data['bot_message_id'],
        text=texts['assignment_created_success'],
        reply_markup=await lesson_details_kb(
            data['lessons_page'], data['assignments']),
        disable_web_page_preview=True
    )


async def get_files(file_path: str):

    async with aiofiles.open(file_path, 'rb') as file:
        file_content = await file.read()
        files = {'document': (file_path, file_content,
                              'application/octet-stream')}
        return files

BACK_ASSIGNMENT_CALLBACKS = {
    "assignment_text_state": assignment_text_process
}

back_handler = create_back_button_handler(BACK_ASSIGNMENT_CALLBACKS)


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
