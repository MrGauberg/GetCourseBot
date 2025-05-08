from aiogram import Router, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime
from src.keyboards.pagination_kb import generate_calendar_keyboard
from src.services.application_client import application_client
from src.core.config import texts
from src.core.settings import user_settings

router = Router()  # Создаем роутер

async def show_calendar(message: types.Message):
    today = datetime.today()
    calendar_data = await application_client.get_calendar_data(today.year, today.month, user_settings.USER_ID, message.from_user.id)
    keyboard = await generate_calendar_keyboard(today.year, today.month, calendar_data)
    await message.answer("Расписание месяца:", reply_markup=keyboard)

async def show_calendar_callback(callback_query: CallbackQuery):
    today = datetime.today()
    calendar_data = await application_client.get_calendar_data(today.year, today.month, user_settings.USER_ID, callback_query.from_user.id)
    keyboard = await generate_calendar_keyboard(today.year, today.month, calendar_data)
    await callback_query.message.edit_text("Расписание месяца:", reply_markup=keyboard)
    await callback_query.answer()

async def change_month(callback_query: CallbackQuery):
    _, year, month = callback_query.data.split("_")
    year, month = int(year), int(month)

    calendar_data = await application_client.get_calendar_data(year, month, user_settings.USER_ID, callback_query.from_user.id)
    keyboard = await generate_calendar_keyboard(year, month, calendar_data)

    await callback_query.message.edit_text("Расписание месяца:", reply_markup=keyboard)
    await callback_query.answer()


async def show_day_description(callback_query: CallbackQuery):
    _, date_str, idx = callback_query.data.split("_")
    index = int(idx)
    year, month, day = map(int, date_str.split("-"))

    cal = await application_client.get_calendar_data(
        year, month,
        user_settings.USER_ID,
        callback_query.from_user.id
    )
    sel = next((d for d in cal["calendar"] if d["date"] == date_str), None)
    if not sel or not sel.get("events"):
        return await callback_query.answer("Событий нет.", show_alert=True)

    events = sel["events"]
    ev = events[index]
    text = (
        f"📅 {day:02d}.{month:02d}.{year}\n"
        f"🏷 {ev['cource']}\n"
        f"📝 {ev['description']}\n"
        f"⏰ {ev.get('time') or 'не указано'}"
    )

    nav = []
    if index > 0:
        nav.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"day_{date_str}_{index-1}"
            )
        )
    nav.append(
        InlineKeyboardButton(
            text=f"{index+1}/{len(events)}",
            callback_data="none"
        )
    )
    if index < len(events) - 1:
        nav.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"day_{date_str}_{index+1}"
            )
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        nav,
        [
            InlineKeyboardButton(
                text=texts["back_button"],
                callback_data=f"month_{year}_{month}"
            )
        ]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()




# Регистрация обработчиков
router.message.register(show_calendar, Command("calendar"))
router.callback_query.register(show_calendar_callback, lambda c: c.data == "show_calendar")
router.callback_query.register(change_month, lambda c: c.data.startswith("month_"))
router.callback_query.register(show_day_description, lambda c: c.data.startswith("day_"))
