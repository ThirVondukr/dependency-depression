from types import TracebackType

from typing_extensions import Self

import aioinject
from aioinject import Scoped


class Class:
    def __enter__(self) -> Self:
        print("Startup")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        print("Shutdown")


container = aioinject.Container()
container.register(Scoped(Class))

with container.sync_context() as ctx:
    print(ctx.resolve(Class))  # <__main__.Class object at ...>
