from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth import hash_password
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import User
from app.routers import (
    apikey_router,
    audit_router,
    auth_router,
    broker_router,
    dashboard_router,
    data_router,
    policy_router,
)


def _seed_admin():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first():
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A local-first personal data broker that gives you full control over "
        "what AI services can access. Store data, define policies, issue scoped "
        "API keys, and audit every access."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router.router)
app.include_router(data_router.router)
app.include_router(policy_router.router)
app.include_router(apikey_router.router)
app.include_router(broker_router.router)
app.include_router(audit_router.router)
app.include_router(dashboard_router.router)
