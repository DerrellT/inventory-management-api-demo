from pydantic import BaseModel, Field
from typing import Annotated

class Product(BaseModel):
        sku: Annotated[str, Field(min_length=1, strip_whitespace=True)]
        color: Annotated[str, Field(min_length=1, strip_whitespace=True)]
        quantity: int = Field(ge=0)
        cost_per_item: float = Field(ge=0)
        price: float = Field(ge=0)


class ProductUpdate(BaseModel):
        quantity: int = Field(ge=0)
        cost_per_item: float = Field(ge=0)
        price: float = Field(ge=0)
