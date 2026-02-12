from fastapi import APIRouter, Depends

from reskin_ai.dependencies import ActorContext, get_current_actor, get_repo
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import ActorResponse, SessionCreateRequest, SessionResponse

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/auth/session", response_model=SessionResponse)
def create_session(payload: SessionCreateRequest, repo: InMemoryRepository = Depends(get_repo)) -> SessionResponse:
    session = repo.create_session(payload.role.value)
    return SessionResponse(token=session["token"], actor_id=session["actor_id"], role=payload.role)


@router.get("/users/me", response_model=ActorResponse)
def get_me(actor: ActorContext = Depends(get_current_actor)) -> ActorResponse:
    return ActorResponse(actor_id=actor.actor_id, role=actor.role)

