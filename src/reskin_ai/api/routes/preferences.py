from fastapi import APIRouter, Depends

from reskin_ai.core.errors import ApiError
from reskin_ai.dependencies import ActorContext, get_current_actor, get_repo
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import PreferenceCreateRequest, PreferenceResponse, Role

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


@router.post("", response_model=PreferenceResponse)
def create_preference(
    payload: PreferenceCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> PreferenceResponse:
    if actor.role != Role.user:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only end users can create preferences.")
    record = repo.create_preference(actor.actor_id, payload.model_dump())
    return PreferenceResponse(**record)


@router.put("/{preference_id}", response_model=PreferenceResponse)
def update_preference(
    preference_id: str,
    payload: PreferenceCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> PreferenceResponse:
    existing = repo.get_preference(preference_id)
    if existing is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Preference record not found.")
    if existing["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot modify this preference.")
    new_record = repo.create_preference(actor.actor_id, payload.model_dump())
    return PreferenceResponse(**new_record)

