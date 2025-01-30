import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from benchmark.container import create_container

from aioinject import Injected, Object
from aioinject.ext.aiogram import AioInjectMiddleware, inject


async def main() -> None:
    dispatcher = Dispatcher()

    container = create_container()
    container.register(Object(42))

    router = Router()

    @router.message(
        Command(commands=["start"]),
    )
    @inject
    async def start(
        message: Message,
        value: Injected[int],
    ) -> None:
        await message.reply(f"Injected value is {value}")

    middleware = AioInjectMiddleware(container)
    middleware.add_to_router(router)

    dispatcher.include_router(router)

    async with (
        container,
        Bot(token="token-here") as bot,  # noqa: S106
    ):
        await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
