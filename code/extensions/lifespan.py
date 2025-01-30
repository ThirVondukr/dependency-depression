import asyncio
import contextlib
from collections.abc import AsyncIterator

from aioinject import Container
from aioinject.extensions import LifespanExtension


class MyLifespanExtension(LifespanExtension):
    @contextlib.asynccontextmanager
    async def lifespan(
        self,
        container: Container,  # noqa: ARG002
    ) -> AsyncIterator[None]:
        print("Enter")
        yield None
        print("Exit")


async def main() -> None:
    container = Container(extensions=[MyLifespanExtension()])
    async with container:
        # print("Enter") is executed.
        pass
        # print("Exit") is executed.


if __name__ == "__main__":
    asyncio.run(main())
