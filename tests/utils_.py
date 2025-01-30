import functools
import sys
from collections.abc import Callable
from typing import ParamSpec, TypeVar

import pytest


T = TypeVar("T")
P = ParamSpec("P")


def dummy_decorator(func: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(func)
    def decorator(*args: P.args, **kwargs: P.kwargs) -> T:
        return func(*args, **kwargs)

    return decorator


def py_gte_311(reason: str) -> pytest.MarkDecorator:
    return pytest.mark.skipif(
        sys.version_info < (3, 11),
        reason=reason,
    )
