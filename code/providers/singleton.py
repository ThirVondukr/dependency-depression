import aioinject


container = aioinject.Container()
container.register(aioinject.Singleton(list))

with container.sync_context() as ctx:
    object_1 = ctx.resolve(list)

with container.sync_context() as ctx:
    object_2 = ctx.resolve(list)

assert object_1 is object_2
