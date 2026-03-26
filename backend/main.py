from fastapi import FastAPI
from src.routes import routes

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

for route in routes:
    app.include_router(route)