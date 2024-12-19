from typing import Any, cast
from collections.abc import Callable, Coroutine

from . import CRUDGenerator, NOT_FOUND
from ._types import DEPENDENCIES, PAGINATION, PYDANTIC_SCHEMA as SCHEMA

try:
    from tortoise.models import Model
except ImportError:
    Model = None  # type: ignore
    tortoise_installed = False
else:
    tortoise_installed = True


CALLABLE = Callable[..., Coroutine[Any, Any, Model]]
CALLABLE_LIST = Callable[..., Coroutine[Any, Any, list[Model]]]


class TortoiseCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        schema: type[SCHEMA],
        db_model: type[Model],
        create_schema: type[SCHEMA] | None = None,
        update_schema: type[SCHEMA] | None = None,
        prefix: str | None = None,
        tags: list[str] | None = None,
        paginate: int | None = None,
        get_all_route: bool | DEPENDENCIES = True,
        get_one_route: bool | DEPENDENCIES = True,
        create_route: bool | DEPENDENCIES = True,
        update_route: bool | DEPENDENCIES = True,
        delete_one_route: bool | DEPENDENCIES = True,
        delete_all_route: bool | DEPENDENCIES = True,
        **kwargs: Any,
    ) -> None:
        assert (
            tortoise_installed
        ), "Tortoise ORM must be installed to use the TortoiseCRUDRouter."

        self.db_model = db_model
        self._pk: str = db_model.describe()["pk_field"]["db_column"]

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.describe()["name"].replace("None.", ""),
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs,
        )

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        async def route(pagination: PAGINATION = self.pagination) -> list[Model]:
            skip, limit = pagination.get("skip"), pagination.get("limit")
            query = self.db_model.all().offset(cast(int, skip))
            if limit:
                query = query.limit(limit)
            return await query

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(item_id: int) -> Model:
            model = await self.db_model.filter(id=item_id).first()

            if model:
                return model
            else:
                raise NOT_FOUND

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(model: self.create_schema) -> Model:  # type: ignore
            db_model = self.db_model(**model.dict())
            await db_model.save()

            return db_model

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            item_id: int,
            model: self.update_schema,  # type: ignore
        ) -> Model:
            await self.db_model.filter(id=item_id).update(
                **model.dict(exclude_unset=True)
            )
            return await self._get_one()(item_id)

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        async def route() -> list[Model]:
            await self.db_model.all().delete()
            return await self._get_all()(pagination={"skip": 0, "limit": None})

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(item_id: int) -> Model:
            model: Model = await self._get_one()(item_id)
            await self.db_model.filter(id=item_id).delete()

            return model

        return route
