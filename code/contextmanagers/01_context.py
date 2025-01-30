import contextlib
from collections.abc import Iterator

import aioinject
from aioinject import Scoped


@contextlib.contextmanager
def dependency() -> Iterator[int]:
    print("Startup")
    yield 42
    print("Shutdown")


container = aioinject.Container()
container.register(Scoped(dependency))

with container.sync_context() as ctx:
    print(ctx.resolve(int))  # Startup, 42
# Shutdown
