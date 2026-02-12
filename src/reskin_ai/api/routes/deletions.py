from fastapi import APIRouter, Depends

from reskin_ai.core.errors import ApiError
from reskin_ai.dependencies import ActorContext, get_current_actor, get_repo
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import DeletionCreateRequest, DeletionResponse, Role

router = APIRouter(prefix="/api/v1/deletions", tags=["deletions"])


@router.post("", response_model=DeletionResponse)
def create_deletion(
    payload: DeletionCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> DeletionResponse:
    if actor.role not in {Role.user, Role.artist}:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only user/artist data can be self-deleted.")
    deletion = repo.create_deletion(actor_id=actor.actor_id, reason=payload.reason)
    completed = repo.execute_deletion(deletion["id"])
    return DeletionResponse(**completed)


@router.get("/{deletion_id}", response_model=DeletionResponse)
def get_deletion(
    deletion_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> DeletionResponse:
    record = repo.get_deletion(deletion_id)
    if record is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Deletion request not found.")
    if actor.role != Role.admin and record["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot access this deletion request.")
    return DeletionResponse(**record)

