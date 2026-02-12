from fastapi import APIRouter

from reskin_ai.api.routes import (
    admin,
    auth,
    collaborations,
    concepts,
    consents,
    deletions,
    generations,
    preferences,
    uploads,
)


def get_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(auth.router)
    router.include_router(consents.router)
    router.include_router(preferences.router)
    router.include_router(uploads.router)
    router.include_router(generations.router)
    router.include_router(concepts.router)
    router.include_router(collaborations.router)
    router.include_router(deletions.router)
    router.include_router(admin.router)
    return router
