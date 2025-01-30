import aioinject


class Database:
    def __init__(self) -> None:
        self._storage = {1: "Username"}

    def get(self, id: int) -> str | None:
        return self._storage.get(id)


class UserService:
    def __init__(
        self,
        database: Database,  # <- Aioinject would try to inject `Database` here
    ) -> None:
        self._database = database

    def get(self, id: int) -> str:
        user = self._database.get(id)
        if user is None:
            raise ValueError
        return user


container = aioinject.Container()
container.register(
    aioinject.Singleton(Database),
    aioinject.Singleton(UserService),
)

with container.sync_context() as ctx:
    service = ctx.resolve(UserService)
    user = service.get(1)
    assert user == "Username"
    print(user)
