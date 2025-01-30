import logging
from typing import TypeVar

from aioinject import InjectionContext, Provider
from aioinject.extensions import OnResolveExtension


T = TypeVar("T")


class MyExtension(OnResolveExtension):
    async def on_resolve(
        self,
        context: InjectionContext,  # noqa: ARG002
        provider: Provider[T],
        instance: T,  # noqa: ARG002
    ) -> None:
        logging.info("%s type was provided!", provider.type_)
