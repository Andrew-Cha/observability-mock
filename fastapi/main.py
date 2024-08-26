from fastapi import FastAPI

app = FastAPI()

@app.get("/foobar")
async def foobar():
    return {"message": "hello world"}
