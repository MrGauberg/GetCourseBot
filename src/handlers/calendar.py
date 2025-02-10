from aiogram import Router, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime
from src.keyboards.pagination_kb import generate_calendar_keyboard
from src.services.application_client import application_client
from src.core.config import texts

router = Router()  # Создаем роутер

async def show_calendar(message: types.Message):
    today = datetime.today()
    calendar_data = await application_client.get_calendar_data(today.year, today.month)
    keyboard = await generate_calendar_keyboard(today.year, today.month, calendar_data)
    await message.answer("Расписание месяца:", reply_markup=keyboard)

async def show_calendar_callback(callback_query: CallbackQuery):
    today = datetime.today()
    calendar_data = await application_client.get_calendar_data(today.year, today.month)
    keyboard = await generate_calendar_keyboard(today.year, today.month, calendar_data)
    await callback_query.message.edit_text("Расписание месяца:", reply_markup=keyboard)
    await callback_query.answer()

async def change_month(callback_query: CallbackQuery):
    _, year, month = callback_query.data.split("_")
    year, month = int(year), int(month)

    calendar_data = await application_client.get_calendar_data(year, month)
    keyboard = await generate_calendar_keyboard(year, month, calendar_data)

    await callback_query.message.edit_text("Расписание месяца:", reply_markup=keyboard)
    await callback_query.answer()


async def show_day_description(callback_query: CallbackQuery):
    """Показывает описание дня, если оно есть"""
    parts = callback_query.data.split("_")
    date_str = parts[1]
    time_str = parts[2] if len(parts) > 2 else None
    year, month, day = map(int, date_str.split("-"))

    # Получаем календарь для соответствующего месяца
    calendar_data = await application_client.get_calendar_data(year, month)

    # Ищем выбранный день
    selected_day = next((day for day in calendar_data["calendar"] if day["date"] == date_str), None)

    if selected_day and selected_day["is_description"]:
        formatted_date = f"{day:02d}.{month:02d}.{year}"
        text = f"📅 {texts['date']}: {formatted_date} ⏰ {texts['time']}: {time_str or 'не указано'}\n\n📝 {selected_day['description']}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=texts["back_button"], callback_data=f"month_{year}_{month}")]
            ]
        )
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback_query.answer("Для этого дня нет описания.", show_alert=True)


# Регистрация обработчиков
router.message.register(show_calendar, Command("calendar"))
router.callback_query.register(show_calendar_callback, lambda c: c.data == "show_calendar")
router.callback_query.register(change_month, lambda c: c.data.startswith("month_"))
router.callback_query.register(show_day_description, lambda c: c.data.startswith("day_"))
