import inspect
import typing
from typing import Any, Callable, TypeVar

from aioinject.markers import Inject

_T = TypeVar("_T", bound=Callable[..., None])


def clear_wrapper(wrapper: _T) -> _T:
    inject_annotations = get_inject_annotations(wrapper)
    signature = inspect.signature(wrapper)
    new_params = tuple(
        p
        for p in signature.parameters.values()
        if p.name not in inject_annotations
    )
    wrapper.__signature__ = signature.replace(parameters=new_params)  # type: ignore[attr-defined]
    for name in inject_annotations:
        del wrapper.__annotations__[name]
    return wrapper


def get_inject_annotations(function: Callable[..., Any]) -> dict[str, Any]:
    return {
        name: annotation
        for name, annotation in typing.get_type_hints(
            function, include_extras=True
        ).items()
        if any(
            isinstance(arg, Inject) or arg is Inject
            for arg in typing.get_args(annotation)
        )
    }
