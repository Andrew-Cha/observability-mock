from pydantic import BaseModel, Field
from typing import Optional


class CreateCat(BaseModel):
    age: int
    name: str
    breed: str


class Cat(CreateCat):
    id: int


class CreateOwner(BaseModel):
    name: str
    address: str
    cat_id: int


class Owner(CreateOwner):
    id: int


class CreateCat(BaseModel):
    age: int
    name: str
    breed: str


class UpdateCat(BaseModel):
    age: Optional[int] = Field(None)
    name: Optional[str] = Field(None)
    breed: Optional[str] = Field(None)


class CreateOwner(BaseModel):
    name: str
    address: str
    cat_id: int


class UpdateOwner(BaseModel):
    name: Optional[str] = Field(None)
    address: Optional[str] = Field(None)
    cat_id: Optional[int] = Field(None)
