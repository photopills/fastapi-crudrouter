from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str | None = None

class Product(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
