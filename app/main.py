from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.main import get_db
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, status

from app.routers.content import router as content_routes
from app.routers.user import router as user_routes
from app.routers.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("server is starting up...")
    get_db()
    yield 
    print("server is shutting down...")

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            csrf_token = request.headers.get("X-CSRF-Token")
            if csrf_token != request.cookies.get("csrf_token"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token invalid in main.py")
            
        response = await call_next(request)
        return response

app = FastAPI(lifespan=lifespan)

app.add_middleware(CSRFMiddleware)

origins = ["http://localhost:5173", "localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(content_routes)
app.include_router(user_routes)
app.include_router(auth_router)

@app.get("/")
async def pint():
    return {"message": "bobo"}