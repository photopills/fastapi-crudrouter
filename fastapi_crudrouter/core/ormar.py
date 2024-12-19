from typing import (
    Any,
    cast,
)
from collections.abc import Coroutine, Callable

from fastapi import HTTPException

from . import CRUDGenerator, NOT_FOUND, _utils
from ._types import DEPENDENCIES, PAGINATION

try:
    from ormar import Model, NoMatch
except ImportError:
    Model = None  # type: ignore
    NoMatch = None  # type: ignore
    ormar_installed = False
else:
    ormar_installed = True

CALLABLE = Callable[..., Coroutine[Any, Any, Model]]
CALLABLE_LIST = Callable[..., Coroutine[Any, Any, list[Model] | None]]


class OrmarCRUDRouter(CRUDGenerator[Model]):
    def __init__(
        self,
        schema: type[Model],
        create_schema: type[Model] | None = None,
        update_schema: type[Model] | None = None,
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
        assert ormar_installed, "Ormar must be installed to use the OrmarCRUDRouter."

        self._pk: str = schema.Meta.pkname
        self._pk_type: type = _utils.get_pk_type(schema, self._pk)

        super().__init__(
            schema=schema,
            create_schema=create_schema or schema,
            update_schema=update_schema or schema,
            prefix=prefix or schema.Meta.tablename,
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

        self._INTEGRITY_ERROR = self._get_integrity_error_type()

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        async def route(
            pagination: PAGINATION = self.pagination,
        ) -> list[Model | None]:
            skip, limit = pagination.get("skip"), pagination.get("limit")
            query = self.schema.objects.offset(cast(int, skip))
            if limit:
                query = query.limit(limit)
            return await query.all()  # type: ignore

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(item_id: self._pk_type) -> Model:  # type: ignore
            try:
                filter_ = {self._pk: item_id}
                model = await self.schema.objects.filter(
                    _exclude=False, **filter_
                ).first()
            except NoMatch:
                raise NOT_FOUND from None
            return model

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(model: self.create_schema) -> Model:  # type: ignore
            model_dict = model.dict()
            if self.schema.Meta.model_fields[self._pk].autoincrement:
                model_dict.pop(self._pk, None)
            try:
                return await self.schema.objects.create(**model_dict)
            except self._INTEGRITY_ERROR:
                raise HTTPException(422, "Key already exists") from None

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            item_id: self._pk_type,  # type: ignore
            model: self.update_schema,  # type: ignore
        ) -> Model:
            filter_ = {self._pk: item_id}
            try:
                await self.schema.objects.filter(_exclude=False, **filter_).update(
                    **model.dict(exclude_unset=True)
                )
            except self._INTEGRITY_ERROR as e:
                self._raise(e)
            return await self._get_one()(item_id)

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        async def route() -> list[Model | None]:
            await self.schema.objects.delete(each=True)
            return await self._get_all()(pagination={"skip": 0, "limit": None})

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(item_id: self._pk_type) -> Model:  # type: ignore
            model = await self._get_one()(item_id)
            await model.delete()
            return model

        return route

    def _get_integrity_error_type(self) -> type[Exception]:
        """Imports the Integrity exception based on the used backend"""
        backend = self.schema.db_backend_name()

        try:
            if backend == "sqlite":
                from sqlite3 import IntegrityError
            elif backend == "postgresql":
                from asyncpg import (  # type: ignore
                    IntegrityConstraintViolationError as IntegrityError,
                )
            else:
                from pymysql import IntegrityError  # type: ignore
            return IntegrityError
        except ImportError:
            return Exception
