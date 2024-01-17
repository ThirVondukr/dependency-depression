from __future__ import annotations

import asyncio
import collections
import contextlib
import enum
import threading
from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from aioinject.providers import DependencyLifetime
from aioinject.utils import enter_context_maybe, enter_sync_context_maybe


if TYPE_CHECKING:
    from typing_extensions import Self

    from aioinject.providers import Provider


_T = TypeVar("_T")


class NotInCache(enum.Enum):
    sentinel = enum.auto()


class InstanceStore:
    def __init__(self) -> None:
        self._cache: dict[type, Any] = {}
        self._exit_stack = contextlib.AsyncExitStack()
        self._sync_exit_stack = contextlib.ExitStack()

    def get(self, provider: Provider[_T]) -> _T | Literal[NotInCache.sentinel]:
        return self._cache.get(provider.type_, NotInCache.sentinel)

    def add(self, provider: Provider[_T], obj: _T) -> None:
        if provider.lifetime is not DependencyLifetime.transient:
            self._cache[provider.type_] = obj

    def lock(
        self,
        provider: Provider[Any],
    ) -> AbstractAsyncContextManager[bool]:
        return contextlib.nullcontext(provider.type_ not in self._cache)

    def sync_lock(
        self,
        provider: Provider[Any],
    ) -> AbstractContextManager[bool]:
        return contextlib.nullcontext(provider.type_ not in self._cache)

    async def enter_context(
        self,
        obj: _T | AbstractContextManager[_T] | AbstractAsyncContextManager[_T],
    ) -> _T:
        return await enter_context_maybe(obj, self._exit_stack)

    def enter_sync_context(
        self,
        obj: _T | AbstractContextManager[_T],
    ) -> _T:
        return enter_sync_context_maybe(obj, self._sync_exit_stack)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self) -> None:
        await self.__aexit__(None, None, None)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._sync_exit_stack.__exit__(exc_type, exc_val, exc_tb)

    def close(self) -> None:
        self.__exit__(None, None, None)


class SingletonStore(InstanceStore):
    def __init__(self) -> None:
        super().__init__()
        self._locks: dict[type, asyncio.Lock] = collections.defaultdict(
            asyncio.Lock,
        )
        self._sync_locks: dict[type, threading.Lock] = collections.defaultdict(
            threading.Lock,
        )

    @contextlib.asynccontextmanager
    async def lock(self, provider: Provider[Any]) -> AsyncIterator[bool]:
        if provider.type_ not in self._cache:
            async with self._locks[provider.type_]:
                yield provider.type_ not in self._cache
                return
        yield False

    @contextlib.contextmanager
    def sync_lock(
        self,
        provider: Provider[Any],
    ) -> Iterator[bool]:
        if provider.type_ not in self._cache:
            with self._sync_locks[provider.type_]:
                yield provider.type_ not in self._cache
                return
        yield False
