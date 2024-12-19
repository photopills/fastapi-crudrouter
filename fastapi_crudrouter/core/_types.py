from typing import TypeVar, Optional, Sequence

from fastapi.params import Depends
from pydantic import BaseModel

PAGINATION = dict[str, Optional[int]]
PYDANTIC_SCHEMA = BaseModel

T = TypeVar("T", bound=BaseModel)
DEPENDENCIES = Sequence[Depends] | None
