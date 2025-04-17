
import aiofiles
from src.core.config import texts, bot
from src.handlers.course import start_registeration_proccess
from src.handlers.registration import full_name_proccess
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
from aiogram.types import ContentType


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
        pass
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


from aiogram.types import ContentType

async def assignment_doc_process(message: Message, state: FSMContext):
    data = await state.get_data()
    files = data.get('files', [])
    text = data['assignment_model'].get('bot_msg_text')
    content_type = message.content_type if isinstance(message, Message) else None
    if content_type == ContentType.DOCUMENT:
        # Обработка полученного документа
        document = message.document
        file_id = document.file_id
        file_name = document.file_name

        # Получение пути к файлу от Telegram
        file = await bot.get_file(file_id)
        file_path = file.file_path

        # Скачивание файла
        if not os.path.exists("documents"):
            os.makedirs("documents")
        file_path_to_save = f"documents/{file_name}_{message.from_user.id}"
        await bot.download_file(file_path, destination=file_path_to_save)

        # Сохранение пути к файлу
        files.append(file_path_to_save)
        if len(files) == 1:
            text += "\n\n" + texts["file_received"] + "\n\n"

        text += "\n" + f"{len(files)}. {file_name}"
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
    # Проверка состояния
    array = [
        data['assignment_model'].get('text'),
        data['assignment_model'].get('video'),
        files
    ]
    if is_all_fields_blank(array):
        await bot.edit_message_text(
            chat_id=call.from_user.id,
            message_id=data['bot_message_id'],
            text=texts['all_element_blank'],
            reply_markup=await lesson_details_kb(
                data['lessons_page'], data['assignments']),
            disable_web_page_preview=True
        )
        await state.clear()
        return

    # Подготовка файлов для отправки
    file_tuples = []
    for file_path in files:
        async with aiofiles.open(file_path, 'rb') as file:
            file_content = await file.read()
            file_name = os.path.basename(file_path)
            file_tuples.append(('files', (file_name, file_content, 'application/octet-stream')))
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
        file_content = await file.read()
        file_name = os.path.basename(file_path)
        files = [('files', (file_name, file_content, 'application/octet-stream'))]
        return files


BACK_ASSIGNMENT_CALLBACKS = {
    "assignment_text_state": assignment_text_process,
    "user_full_name_state": start_registeration_proccess,
    "user_email_state": full_name_proccess,
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

