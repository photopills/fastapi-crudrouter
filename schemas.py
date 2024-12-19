from pydantic import BaseModel

class ItemSchema(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class UserSchema(BaseModel):
    id: int
    name: str
    email: str | None = None
