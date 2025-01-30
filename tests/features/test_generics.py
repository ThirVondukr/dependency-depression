import abc
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

import pytest

from aioinject import Container, Object, Scoped
from aioinject.providers import Dependency, Transient
from tests.utils_ import py_gte_311


T = TypeVar("T")
U = TypeVar("U")
ReqT = TypeVar("ReqT")
ResT = TypeVar("ResT")


class UnusedGeneric(Generic[T]):
    def __init__(self, dependency: str) -> None:
        self.dependency = dependency


class SimpleGeneric(Generic[T]):
    def __init__(self, dependency: T) -> None:
        self.dependency = dependency


class SimpleGenericExtended(SimpleGeneric[int]):
    pass


class MultipleSimpleGeneric(Generic[T, U]):
    def __init__(self, service: T, b: U) -> None:
        self.service = service
        self.b = b


class NestedGeneric(Generic[T, U]):
    def __init__(self, simple_gen: MultipleSimpleGeneric[T, U], u: U) -> None:
        self.simple_gen = simple_gen
        self.u = u


class Something:
    def __init__(self) -> None:
        self.a = MEANING_OF_LIFE_INT


MEANING_OF_LIFE_INT = 42
MEANING_OF_LIFE_STR = "42"


async def test_generic_dependency() -> None:
    assert Scoped(UnusedGeneric[int]).collect_dependencies() == (
        Dependency(
            name="dependency",
            type_=str,
        ),
    )

    assert Scoped(SimpleGeneric[int]).collect_dependencies() == (
        Dependency(
            name="dependency",
            type_=int,
        ),
    )
    assert Scoped(SimpleGenericExtended).collect_dependencies() == (
        Dependency(
            name="dependency",
            type_=int,
        ),
    )


@pytest.mark.parametrize(
    ("type_", "instanceof"),
    [
        (UnusedGeneric, UnusedGeneric),
        (SimpleGeneric[int], SimpleGeneric),
        (SimpleGenericExtended, SimpleGenericExtended),
    ],
)
async def test_resolve_generics(
    type_: type[object],
    instanceof: type[object],
) -> None:
    container = Container()
    container.register(Scoped(type_))
    container.register(Object(42))
    container.register(Object("42"))

    async with container.context() as ctx:
        instance = await ctx.resolve(type_)
        assert isinstance(instance, instanceof)


@py_gte_311("""
            prior to 3.11 using generic_alias[] considered a syntax error
            its very hard to overcome this due to `test_partially_resolved_generic`
            """)
async def test_nested_generics() -> None:
    container = Container()
    container.register(
        Scoped(NestedGeneric[int, str]),
        Scoped(MultipleSimpleGeneric[int, str]),
        Object(MEANING_OF_LIFE_INT),
        Object(MEANING_OF_LIFE_STR),
    )

    async with container.context() as ctx:
        instance = await ctx.resolve(NestedGeneric[int, str])
        assert isinstance(instance, NestedGeneric)
        assert isinstance(instance.simple_gen, MultipleSimpleGeneric)
        assert instance.simple_gen.service == MEANING_OF_LIFE_INT
        assert instance.simple_gen.b == MEANING_OF_LIFE_STR
        assert instance.u == MEANING_OF_LIFE_STR


async def test_nested_unresolved_generic() -> None:
    @dataclass
    class NestedUnresolvedGeneric:
        service: SimpleGeneric  # type: ignore[type-arg]

    container = Container()
    obj = SimpleGeneric(MEANING_OF_LIFE_INT)
    container.register(
        Scoped(NestedUnresolvedGeneric),
        Object(obj, type_=SimpleGeneric),
    )

    async with container.context() as ctx:
        instance = await ctx.resolve(NestedUnresolvedGeneric)
        assert isinstance(instance, NestedUnresolvedGeneric)
        assert isinstance(instance.service, SimpleGeneric)
        assert instance.service.dependency == MEANING_OF_LIFE_INT


async def test_partially_resolved_generic() -> None:
    K = TypeVar("K")

    class TwoGeneric(Generic[T, K]):
        def __init__(self, a: SimpleGeneric[T], b: SimpleGeneric[K]) -> None:
            self.a = a
            self.b = b

    class UsesTwoGeneric(Generic[T]):
        def __init__(self, service: TwoGeneric[T, str]) -> None:
            self.service = service

    container = Container()
    container.register(
        Scoped(UsesTwoGeneric[int]),
        Scoped(TwoGeneric[int, str]),
        Scoped(SimpleGeneric[int]),
        Scoped(SimpleGeneric[str]),
        Object(MEANING_OF_LIFE_INT),
        Object("42"),
    )

    async with container.context() as ctx:
        instance = await ctx.resolve(UsesTwoGeneric[int])
        assert isinstance(instance, UsesTwoGeneric)
        assert isinstance(instance.service, TwoGeneric)
        assert isinstance(instance.service.a, SimpleGeneric)
        assert isinstance(instance.service.b, SimpleGeneric)
        assert instance.service.a.dependency == MEANING_OF_LIFE_INT
        assert instance.service.b.dependency == MEANING_OF_LIFE_STR


async def test_can_resolve_generic_class_without_parameters() -> None:
    class GenericClass(Generic[T]):
        def __init__(self, a: int) -> None:
            self.a = a

        def so_generic(self) -> T:  # pragma: no cover
            raise NotImplementedError

    container = Container()
    container.register(Scoped(GenericClass), Object(MEANING_OF_LIFE_INT))

    async with container.context() as ctx:
        instance = await ctx.resolve(GenericClass)
        assert isinstance(instance, GenericClass)
        assert instance.a == MEANING_OF_LIFE_INT


async def test_can_resolve_generic_iterable() -> None:
    class MiddlewareBase(abc.ABC, Generic[ReqT, ResT]):
        @abc.abstractmethod
        async def __call__(
            self,
            request: ReqT,
            handle: Callable[[ReqT], Awaitable[ResT]],
        ) -> ResT:
            pass

    class FirstMiddleware(MiddlewareBase[ReqT, ResT]):
        async def __call__(
            self,
            request: ReqT,
            handle: Callable[[ReqT], Awaitable[ResT]],
        ) -> ResT:
            return await handle(request)

    class SecondMiddleware(MiddlewareBase[ReqT, ResT]):
        async def __call__(
            self,
            request: ReqT,
            handle: Callable[[ReqT], Awaitable[ResT]],
        ) -> ResT:
            return await handle(request)

    class ThirdMiddleware(MiddlewareBase[ReqT, ResT]):
        async def __call__(
            self,
            request: ReqT,
            handle: Callable[[ReqT], Awaitable[ResT]],
        ) -> ResT:
            return await handle(request)

    container = Container()
    container.register(
        Transient(FirstMiddleware, MiddlewareBase[str, str]),
        Transient(SecondMiddleware, MiddlewareBase[int, int]),
        Transient(ThirdMiddleware, MiddlewareBase[int, int]),
    )

    async with container.context() as ctx:
        instances = await ctx.resolve_iterable(MiddlewareBase[int, int])  # type: ignore[type-abstract]
        assert len(instances) == 2  # noqa: PLR2004
        assert isinstance(instances[0], SecondMiddleware)
        assert isinstance(instances[1], ThirdMiddleware)
