from datetime import datetime
from typing import NewType

from aioinject import Container, Transient
from aioinject.extensions import OnInitExtension


Now = NewType("Now", datetime)


class TimeExtension(OnInitExtension):
    def on_init(
        self,
        container: Container,
    ) -> None:
        container.register(Transient(datetime.now, Now))


container = Container(extensions=[TimeExtension()])
with container.sync_context() as ctx:
    print(ctx.resolve(Now))
