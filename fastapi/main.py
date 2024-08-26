from fastapi import FastAPI, HTTPException, Depends, status
from sqlite3 import Cursor
from typing import Dict, List, Optional

from database import initialize_database, get_db_cursor
from schema import Cat, Owner

app = FastAPI()
initialize_database()


@app.get("/cats/")
def get_cats(cursor: Cursor = Depends(get_db_cursor)) -> List[Cat]:
    cursor.execute("SELECT * FROM cat")
    cats = cursor.fetchall()

    results = []
    for row in cats:
        id, name, breed, age = row
        cat = Cat(id=id, age=age, name=name, breed=breed)
        results.append(cat)

    return results


@app.post("/cats/")
def create_cat(
    name: str, breed: str, age: int, cursor: Cursor = Depends(get_db_cursor)
) -> Cat:
    cursor.execute(
        "INSERT INTO cat(name, breed, age) VALUES (?, ?, ?)", (name, breed, age)
    )
    cursor.connection.commit()
    cat_id = cursor.lastrowid

    return Cat(id=cat_id, age=age, name=name, breed=breed)


@app.patch("/cats/{cat_id}/")
def update_cat(
    cat_id: int,
    name: Optional[str] = None,
    breed: Optional[str] = None,
    age: Optional[int] = None,
    cursor: Cursor = Depends(get_db_cursor),
) -> Cat:
    cursor.execute("SELECT * FROM cat WHERE id = ?", (cat_id,))
    cat = cursor.fetchone()

    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with id {cat_id} not found",
        )

    updated_name = name if name is not None else cat[1]
    updated_breed = breed if breed is not None else cat[2]
    updated_age = age if age is not None else cat[3]

    cursor.execute(
        "UPDATE cat SET name = ?, breed = ?, age = ? WHERE id = ?",
        (updated_name, updated_breed, updated_age, cat_id),
    )
    cursor.connection.commit()

    return Cat(id=cat_id, name=updated_name, breed=updated_breed, age=updated_age)


@app.get("/owners/")
def get_owners(cursor: Cursor = Depends(get_db_cursor)) -> List[Owner]:
    cursor.execute("SELECT * FROM owner")
    owners = cursor.fetchall()

    results = []
    for row in owners:
        id, name, address, cat_id = row
        owner = Owner(id=id, name=name, address=address, cat_id=cat_id)
        results.append(owner)

    return results


@app.post("/owners/")
def create_owner(
    name: str, address: str, cat_id: int, cursor: Cursor = Depends(get_db_cursor)
) -> Owner:
    cursor.execute("SELECT EXISTS(SELECT 1 FROM cat WHERE id = ?)", (cat_id,))
    cat_exists = cursor.fetchone()[0]

    if not cat_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with id {cat_id} does not exist",
        )

    cursor.execute(
        "INSERT INTO owner(name, address, cat_id) VALUES (?, ?, ?)",
        (name, address, cat_id),
    )
    cursor.connection.commit()
    owner_id = cursor.lastrowid

    return Owner(id=owner_id, name=name, address=address, cat_id=cat_id)


@app.patch("/owners/{owner_id}/")
def update_owner(
    owner_id: int,
    name: Optional[str] = None,
    address: Optional[str] = None,
    cat_id: Optional[int] = None,
    cursor: Cursor = Depends(get_db_cursor),
) -> Owner:
    cursor.execute("SELECT * FROM owner WHERE id = ?", (owner_id,))
    owner = cursor.fetchone()

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with id {owner_id} not found",
        )

    if cat_id is not None:
        cursor.execute("SELECT EXISTS(SELECT 1 FROM cat WHERE id = ?)", (cat_id,))
        cat_exists = cursor.fetchone()[0]

        if not cat_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cat with id {cat_id} does not exist",
            )

    updated_name = name if name is not None else owner[1]
    updated_address = address if address is not None else owner[2]
    updated_cat_id = cat_id if cat_id is not None else owner[3]

    cursor.execute(
        "UPDATE owner SET name = ?, address = ?, cat_id = ? WHERE id = ?",
        (updated_name, updated_address, updated_cat_id, owner_id),
    )
    cursor.connection.commit()

    return Owner(
        id=owner_id, name=updated_name, address=updated_address, cat_id=updated_cat_id
    )
