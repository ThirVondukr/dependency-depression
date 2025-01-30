import contextlib
from collections.abc import Iterator

import aioinject
from aioinject import Singleton


@contextlib.contextmanager
def dependency() -> Iterator[int]:
    print("Startup")
    yield 42
    print("Shutdown")


container = aioinject.Container()
container.register(Singleton(dependency))

with container:
    with container.sync_context() as ctx:
        print(ctx.resolve(int))  # Startup, 42
    print("Context is closed")
# Shutdown
