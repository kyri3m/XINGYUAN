"""API composition root."""
from fastapi import APIRouter
from .routes import auth_routes, users, personnel, tasks, sampling, dashboard
router = APIRouter()
router.include_router(auth_routes.router)
router.include_router(users.router)
router.include_router(personnel.router)
router.include_router(tasks.router)
router.include_router(sampling.router)
router.include_router(dashboard.router)
