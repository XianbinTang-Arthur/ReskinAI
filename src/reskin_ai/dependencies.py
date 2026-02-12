from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Header

from reskin_ai.core.config import settings
from reskin_ai.core.errors import ApiError
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import Role
from reskin_ai.services.model_provider import ResilientModelProvider, build_model_provider
from reskin_ai.services.storage import LocalStorageService

_repo = InMemoryRepository(persist_path=settings.state_file, db_url=settings.resolved_database_url)
_storage = LocalStorageService(settings.storage_root)
_model_provider = build_model_provider(settings)


def get_repo() -> InMemoryRepository:
    return _repo


def get_storage() -> LocalStorageService:
    return _storage


def get_model_provider() -> ResilientModelProvider:
    return _model_provider


def reset_repo() -> None:
    _repo.reset()
    _storage.reset_for_tests()


@dataclass
class ActorContext:
    actor_id: str
    role: Role
    token: str


def _parse_bearer_token(raw: str | None) -> str:
    if not raw:
        raise ApiError(status_code=401, code="UNAUTHORIZED", message="Missing Authorization header.")
    prefix = "bearer "
    if not raw.lower().startswith(prefix):
        raise ApiError(status_code=401, code="UNAUTHORIZED", message="Invalid Authorization header.")
    token = raw[len(prefix) :].strip()
    if not token:
        raise ApiError(status_code=401, code="UNAUTHORIZED", message="Empty bearer token.")
    return token


def get_current_actor(
    authorization: str | None = Header(default=None, alias="Authorization"),
    repo: InMemoryRepository = Depends(get_repo),
) -> ActorContext:
    token = _parse_bearer_token(authorization)
    session = repo.get_session_by_token(token)
    if session is None:
        raise ApiError(status_code=401, code="UNAUTHORIZED", message="Invalid session token.")
    return ActorContext(actor_id=session["actor_id"], role=Role(session["role"]), token=token)


def require_roles(*roles: Role) -> Callable[[ActorContext], ActorContext]:
    allowed = set(roles)

    def checker(actor: ActorContext = Depends(get_current_actor)) -> ActorContext:
        if actor.role not in allowed:
            raise ApiError(status_code=403, code="FORBIDDEN", message="Role is not allowed for this action.")
        return actor

    return checker
