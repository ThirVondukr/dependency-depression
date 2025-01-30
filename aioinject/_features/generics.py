from __future__ import annotations

import functools
import sys
import textwrap
import types
import typing as t
from collections.abc import Callable
from types import GenericAlias
from typing import TYPE_CHECKING, Any, TypeGuard

from aioinject._utils import is_iterable_generic_collection


if TYPE_CHECKING:
    from aioinject.providers import Dependency


def _is_generic_alias(type_: Any) -> TypeGuard[GenericAlias]:
    return isinstance(
        type_,
        types.GenericAlias | t._GenericAlias,  # type: ignore[attr-defined] # noqa: SLF001
    ) and not is_iterable_generic_collection(type_)


def _get_orig_bases(type_: type) -> tuple[type, ...] | None:
    return getattr(type_, "__orig_bases__", None)


def _get_generic_arguments(type_: Any) -> list[t.TypeVar] | None:
    """
    Returns generic arguments of given class, e.g. Class[T] would return [~T]
    """
    if _is_generic_alias(type_):
        args = t.get_args(type_)
        return [arg for arg in args if isinstance(arg, t.TypeVar)]
    return None


@functools.cache
def _get_generic_args_map(type_: type[object]) -> dict[str, type[object]]:
    if _is_generic_alias(type_):
        params: dict[str, Any] = {
            param.__name__: param
            for param in type_.__origin__.__parameters__  # type: ignore[attr-defined]
        }
        return dict(zip(params, type_.__args__, strict=True))

    args_map = {}
    if orig_bases := _get_orig_bases(type_):
        # find the generic parent
        for base in orig_bases:
            if _is_generic_alias(base):  # noqa: SIM102
                if params := {
                    param.__name__: param
                    for param in getattr(base.__origin__, "__parameters__", ())
                }:
                    args_map.update(
                        dict(zip(params, base.__args__, strict=True)),
                    )
    return args_map


@functools.cache
def get_generic_parameter_map(
    provided_type: type[object],
    dependencies: tuple[Dependency[Any], ...],
) -> dict[str, type[object]]:
    args_map = _get_generic_args_map(provided_type)  # type: ignore[arg-type]
    result = {}
    for dependency in dependencies:
        inner_type = dependency.inner_type
        if args_map and (
            generic_arguments := _get_generic_arguments(inner_type)
        ):
            # This is a generic type, we need to resolve the type arguments
            # and pass them to the provider.
            resolved_args = tuple(
                args_map[arg.__name__] for arg in generic_arguments
            )
            #  We can use `[]` when we drop support for 3.10
            result[dependency.name] = _py310_compat_resolve_generics(
                inner_type, resolved_args
            )
    return result


def is_py_gt3_311() -> bool:  # pragma: no cover
    return sys.version_info >= (3, 11)


def _py310_compat_resolve_generics_factory() -> (
    Callable[[type, tuple[type, ...]], type]
):  # pragma: no cover
    # we need to exec a string to avoid syntax errors
    # we will create a function that will return the resolved generic
    # for python 3.11 and later we can use `generic_alias[*args]` which will consider
    # see `test_partially_resolved_generic` for more details

    if is_py_gt3_311():
        fn_impl = textwrap.dedent("""
        def _resolve_generic(
            generic_alias: type,
            args: tuple[type, ...],
        ) -> type:
            return generic_alias[*args]
        """)
    else:
        fn_impl = textwrap.dedent("""
        def _resolve_generic(
            generic_alias: type,
            args: tuple[type, ...],
        ) -> type:
            return generic_alias.__getitem__(*args)
        """)
    exec_globals: dict[str, Any] = {}
    exec(fn_impl, exec_globals)  # noqa: S102
    return exec_globals["_resolve_generic"]


_py310_compat_resolve_generics = _py310_compat_resolve_generics_factory()
