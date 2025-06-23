# fastapi_backend/main.py
from fastapi import FastAPI
from .Router import event_router, auth_router
from .core.database import Base, engine
from starlette.middleware.sessions import SessionMiddleware
from .core.auth import SECRET_KEY
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from .Services.lifespan import app_lifespan

Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=app_lifespan)


app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_cookie",
    max_age=3600
)

app.include_router(event_router.router)
app.include_router(auth_router.router)