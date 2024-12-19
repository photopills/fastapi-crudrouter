from typing import Any, cast
from collections.abc import Callable
from . import CRUDGenerator, NOT_FOUND
from ._types import DEPENDENCIES, PAGINATION, PYDANTIC_SCHEMA as SCHEMA

CALLABLE = Callable[..., SCHEMA]
CALLABLE_LIST = Callable[..., list[SCHEMA]]


class MemoryCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        schema: type[SCHEMA],
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
        **kwargs: Any
    ) -> None:
        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix,
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs
        )

        self.models: list[SCHEMA] = []
        self._id = 1

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(pagination: PAGINATION = self.pagination) -> list[SCHEMA]:
            skip, limit = pagination.get("skip"), pagination.get("limit")
            skip = cast(int, skip)

            return (
                self.models[skip:]
                if limit is None
                else self.models[skip : skip + limit]
            )

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: int) -> SCHEMA:
            for model in self.models:
                if model.id == item_id:  # type: ignore
                    return model

            raise NOT_FOUND

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(model: self.create_schema) -> SCHEMA:  # type: ignore
            model_dict = model.dict()
            model_dict["id"] = self._get_next_id()
            ready_model = self.schema(**model_dict)
            self.models.append(ready_model)
            return ready_model

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: int, model: self.update_schema) -> SCHEMA:  # type: ignore
            for ind, model_ in enumerate(self.models):
                if model_.id == item_id:  # type: ignore
                    self.models[ind] = self.schema(
                        **model.dict(), id=model_.id  # type: ignore
                    )
                    return self.models[ind]

            raise NOT_FOUND

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route() -> list[SCHEMA]:
            self.models = []
            return self.models

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: int) -> SCHEMA:
            for ind, model in enumerate(self.models):
                if model.id == item_id:  # type: ignore
                    del self.models[ind]
                    return model

            raise NOT_FOUND

        return route

    def _get_next_id(self) -> int:
        id_ = self._id
        self._id += 1

        return id_
