from pydantic.dataclasses import dataclass


@dataclass(kw_only=True)
class Cat:
    id: int
    age: int
    name: str
    breed: str


@dataclass(kw_only=True)
class Owner:
    id: int
    name: str
    address: str
    cat_id: int
