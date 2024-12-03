import asyncio
from aiogram import Bot
from pytz import timezone
from src.handlers import assignment

from src.misc.set_bot_commands import set_commands

moscow = timezone('Europe/Moscow')


async def on_startup(bot: Bot):
    await set_commands(bot)


async def main():
    from src.core.config import (
        dp, bot, form_router, view_router
    )
    from src.handlers import (
        start,
        course,
        lesson,
        registration
    )
    from src.services.application_client import application_client

    start.register_handler(dp)
    course.register_handler(view_router)
    lesson.register_handler(view_router)
    assignment.register_handler(view_router, form_router)
    registration.register_handler(form_router)
    dp.include_router(view_router)
    dp.include_router(form_router)

    # Авторизация для получения токенов
    email = "admin@test.com"
    password = "CoursePassword18645"
    try:
        print("Authenticating...")
        await application_client.authenticate(email, password)
        print("Authentication successful!")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return  

    try:
        await on_startup(bot)
        await dp.start_polling(bot)
    finally:
        await application_client.close()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
