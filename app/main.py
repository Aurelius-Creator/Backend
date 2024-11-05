from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.main import get_db
from app.routers.content import router as content_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("server is starting up...")
    get_db()
    yield 
    print("server is shutting down...")

app = FastAPI(lifespan=lifespan)
app.include_router(content_routes)

@app.get("/")
async def pint():
    return {"message": "bobo"}