from typing import Any

from fastapi import Depends, HTTPException
from pydantic import create_model
from pydantic_core.core_schema import model_fields_schema

from ._types import T, PAGINATION, PYDANTIC_SCHEMA


class AttrDict(dict):  # type: ignore
    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def get_pk_type(schema: type[PYDANTIC_SCHEMA], pk_field: str) -> Any:
    try:
        return model_fields_schema[pk_field].type_
    except KeyError:
        return int


def schema_factory(
    schema_cls: type[T], pk_field_name: str = "id", name: str = "Create"
) -> type[T]:
    """
    Is used to create a CreateSchema which does not contain pk
    """

    fields = {
        fname: (finfo.annotation, ...)
        for fname, finfo in schema_cls.model_fields.items()
        if fname != pk_field_name
    }


    name = schema_cls.__name__ + name
    schema: type[T] = create_model(name, **fields)  # type: ignore
    return schema


def create_query_validation_exception(field: str, msg: str) -> HTTPException:
    return HTTPException(
        422,
        detail={
            "detail": [
                {"loc": ["query", field], "msg": msg, "type": "type_error.integer"}
            ]
        },
    )


def pagination_factory(max_limit: int | None = None) -> Any:
    """
    Created the pagination dependency to be used in the router
    """

    def pagination(skip: int = 0, limit: int | None = max_limit) -> PAGINATION:
        if skip < 0:
            raise create_query_validation_exception(
                field="skip",
                msg="skip query parameter must be greater or equal to zero",
            )

        if limit is not None:
            if limit <= 0:
                raise create_query_validation_exception(
                    field="limit", msg="limit query parameter must be greater then zero"
                )

            elif max_limit and max_limit < limit:
                raise create_query_validation_exception(
                    field="limit",
                    msg=f"limit query parameter must be less then {max_limit}",
                )

        return {"skip": skip, "limit": limit}

    return Depends(pagination)
