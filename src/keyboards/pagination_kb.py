import calendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from datetime import datetime
from src.core.config import texts

async def generate_db_items_keyboard(page: int,
                                     items: List,
                                     next: str,
                                     previous: str,
                                     model_name: str,
                                     back_call: str,
                                     unit_name: str,
                                     ) -> InlineKeyboardMarkup:
    builder_size = []
    builder = InlineKeyboardBuilder()

    for item in items:
        builder.button(
            text=f"{item['title']}",
            callback_data=f"{model_name} {item['id']}"
        )
        builder_size.append(1)

    builder_size.append(0)
    if previous:
        builder.button(text="<", callback_data=f"page_{unit_name} {page - 1}")
        builder_size[-1] += 1

    builder.button(text=' ', callback_data=f'search_{unit_name}')
    builder_size[-1] += 1

    if next:
        builder.button(text=">", callback_data=f"page_{unit_name} {page + 1}")
        builder_size[-1] += 1

    builder.button(text=texts["back_button"], callback_data=back_call)
    builder.button(text=texts["cancel"], callback_data="back_to_main_menu")
    builder_size.append(2)

    builder.adjust(*builder_size)
    return builder



async def generate_calendar_keyboard(year, month, calendar_data):
    keyboard = []

    # Извлекаем список дней из API и фильтруем по текущему месяцу и году
    days_data = [
        item for item in calendar_data.get("calendar", [])
        if datetime.strptime(item["date"], "%Y-%m-%d").month == month
        and datetime.strptime(item["date"], "%Y-%m-%d").year == year
    ]

    # Заголовок месяца
    month_name = f"{texts['months_ru'].get(str(month), 'Неизвестный месяц')} {year}"
    keyboard.append([InlineKeyboardButton(text=month_name, callback_data="none")])

    # Заголовок дней недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(text=day, callback_data="none") for day in week_days])

    # Определяем параметры месяца
    first_weekday, total_days = calendar.monthrange(year, month)

    # Определяем количество дней в предыдущем месяце
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    _, prev_month_days = calendar.monthrange(prev_year, prev_month)

    # Создаем массив для 5 недель (35 дней)
    month_calendar = [None] * 35

    # Заполняем дни предыдущего месяца
    start_prev_day = prev_month_days - (first_weekday - 1) if first_weekday != 0 else prev_month_days - 6
    for i in range(first_weekday):
        day = start_prev_day + i
        month_calendar[i] = InlineKeyboardButton(text=f"{day} 🔘", callback_data=f"none")

    # Заполняем текущий месяц
    for item in days_data:
        date_str = item["date"]
        day = int(date_str.split("-")[-1])
        has_events = bool(item.get("events"))
        status = "✅" if has_events else "⚪"
        # всегда передаём индекс 0 — первый из списка
        callback = f"day_{date_str}_0" if has_events else "none"

        index = first_weekday + (day - 1)
        if 0 <= index < 35:
            month_calendar[index] = InlineKeyboardButton(
                text=f"{day} {status}",
                callback_data=callback
            )

    # Заполняем оставшиеся дни следующего месяца
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    next_day = 1
    for i in range(35):
        if month_calendar[i] is None:
            date_str = f"{next_year}-{next_month:02d}-{next_day:02d}"
            month_calendar[i] = InlineKeyboardButton(text=f"{next_day} 🔘", callback_data=f"none")
            next_day += 1

    # Разбиваем на недели и добавляем в `keyboard`
    for i in range(0, 35, 7):
        keyboard.append(month_calendar[i:i+7])

    # Кнопки навигации
    keyboard.append([
        InlineKeyboardButton(text=texts["back"], callback_data=f"month_{prev_year}_{prev_month}"),
        InlineKeyboardButton(text=texts["forward"], callback_data=f"month_{next_year}_{next_month}")
    ])

    keyboard.append([
        InlineKeyboardButton(text=texts["cancel"], callback_data="back_to_main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
