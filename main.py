from fastapi import FastAPI
# ...existing code...
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item) -> Item:
    return item

@app.get("/items/", response_model=list[Item])
async def read_items() -> list[Item]:
    return [
        Item(name="Item 1", description="Description 1", price=10.0, tax=1.0),
        Item(name="Item 2", description="Description 2", price=20.0, tax=2.0),
    ]
