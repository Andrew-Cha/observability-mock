from sqlite3 import Cursor
from time import time
from typing import List
from os import environ

from fastapi import FastAPI, HTTPException, Depends, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as OTLPSpanExporterHTTP,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from backend.api.database import initialize_database, get_db_cursor
from backend.api.schema import (
    CreateCat,
    CreateOwner,
    Cat,
    Owner,
    UpdateCat,
    UpdateOwner,
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time()
        print(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        process_time = time() - start_time
        print(
            f"Response status: {response.status_code}, Time taken: {process_time:.4f} seconds"
        )

        return response


def setup_tracer_instrumentation(app: FastAPI) -> None:
    port = environ.get("OTEL_JAEGER_TRACE_PORT")
    endpoint = f"http://jaeger:{port}/v1/traces"

    tracer = TracerProvider()
    trace.set_tracer_provider(tracer)

    tracer.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporterHTTP(endpoint=endpoint))
    )
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)


app = FastAPI()
app.add_middleware(LoggingMiddleware)
setup_tracer_instrumentation(app)
initialize_database()

#
# Cats
#


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
def create_cat(cat: CreateCat, cursor: Cursor = Depends(get_db_cursor)) -> Cat:
    cursor.execute(
        "INSERT INTO cat(name, breed, age) VALUES (?, ?, ?)",
        (cat.name, cat.breed, cat.age),
    )
    cursor.connection.commit()
    cat_id = cursor.lastrowid

    return Cat(id=cat_id, age=cat.age, name=cat.name, breed=cat.breed)


@app.patch("/cats/{cat_id}/")
def patch_cat(
    cat_id: int,
    cat: UpdateCat,
    cursor: Cursor = Depends(get_db_cursor),
) -> Cat:
    cursor.execute("SELECT * FROM cat WHERE id = ?", (cat_id,))
    cat_in_db = cursor.fetchone()

    if not cat_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with id {cat_id} not found",
        )

    updated_name = cat.name if cat.name is not None else cat_in_db[1]
    updated_breed = cat.breed if cat.breed is not None else cat_in_db[2]
    updated_age = cat.age if cat.age is not None else cat_in_db[3]

    cursor.execute(
        "UPDATE cat SET name = ?, breed = ?, age = ? WHERE id = ?",
        (updated_name, updated_breed, updated_age, cat_id),
    )
    cursor.connection.commit()

    return Cat(id=cat_id, name=updated_name, breed=updated_breed, age=updated_age)


#
# Owners
#


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
def create_owner(owner: CreateOwner, cursor: Cursor = Depends(get_db_cursor)) -> Owner:
    cursor.execute("SELECT EXISTS(SELECT 1 FROM cat WHERE id = ?)", (owner.cat_id,))
    cat_exists = cursor.fetchone()[0]

    if not cat_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cat with id {owner.cat_id} does not exist",
        )

    cursor.execute(
        "INSERT INTO owner(name, address, cat_id) VALUES (?, ?, ?)",
        (owner.name, owner.address, owner.cat_id),
    )
    cursor.connection.commit()
    owner_id = cursor.lastrowid

    return Owner(
        id=owner_id, name=owner.name, address=owner.address, cat_id=owner.cat_id
    )


@app.patch("/owners/{owner_id}/")
def patch_owner(
    owner_id: int,
    owner: UpdateOwner,
    cursor: Cursor = Depends(get_db_cursor),
) -> Owner:
    cursor.execute("SELECT * FROM owner WHERE id = ?", (owner_id,))
    owner_in_db = cursor.fetchone()

    if not owner_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with id {owner_id} not found",
        )

    if owner.cat_id is not None:
        cursor.execute("SELECT EXISTS(SELECT 1 FROM cat WHERE id = ?)", (owner.cat_id,))
        cat_exists = cursor.fetchone()[0]

        if not cat_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cat with id {owner.cat_id} does not exist",
            )

    updated_name = owner.name if owner.name is not None else owner_in_db[1]
    updated_address = owner.address if owner.address is not None else owner_in_db[2]
    updated_cat_id = owner.cat_id if owner.cat_id is not None else owner_in_db[3]

    cursor.execute(
        "UPDATE owner SET name = ?, address = ?, cat_id = ? WHERE id = ?",
        (updated_name, updated_address, updated_cat_id, owner_id),
    )
    cursor.connection.commit()

    return Owner(
        id=owner_id, name=updated_name, address=updated_address, cat_id=updated_cat_id
    )
