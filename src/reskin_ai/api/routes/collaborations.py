from fastapi import APIRouter, Depends

from reskin_ai.core.errors import ApiError
from reskin_ai.dependencies import ActorContext, get_current_actor, get_repo
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import (
    CollaborationInviteRequest,
    CollaborationNoteCreateRequest,
    CollaborationNoteResponse,
    CollaborationResponse,
    Role,
)

router = APIRouter(prefix="/api/v1/collaborations", tags=["collaborations"])


@router.post("/invite", response_model=CollaborationResponse)
def invite_artist(
    payload: CollaborationInviteRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> CollaborationResponse:
    if actor.role != Role.user:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only users can invite artists.")
    for concept_id in payload.concept_ids:
        concept = repo.get_concept(concept_id)
        if concept is None:
            raise ApiError(status_code=404, code="NOT_FOUND", message=f"Concept not found: {concept_id}")
        if concept["actor_id"] != actor.actor_id:
            raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot share concept not owned by user.")
    record = repo.create_collaboration(
        user_actor_id=actor.actor_id,
        artist_actor_id=payload.artist_actor_id,
        concept_ids=payload.concept_ids,
    )
    return CollaborationResponse(**record)


@router.get("/{collaboration_id}", response_model=CollaborationResponse)
def get_collaboration(
    collaboration_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> CollaborationResponse:
    collab = repo.get_collaboration(collaboration_id)
    if collab is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Collaboration not found.")
    if actor.role != Role.admin and actor.actor_id not in {collab["user_actor_id"], collab["artist_actor_id"]}:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot access this collaboration.")
    return CollaborationResponse(**collab)


@router.post("/{collaboration_id}/notes", response_model=CollaborationNoteResponse)
def add_note(
    collaboration_id: str,
    payload: CollaborationNoteCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> CollaborationNoteResponse:
    collab = repo.get_collaboration(collaboration_id)
    if collab is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Collaboration not found.")
    if collab["status"] != "active":
        raise ApiError(status_code=409, code="COLLABORATION_REVOKED", message="Collaboration is not active.")
    if actor.role != Role.artist or collab["artist_actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only assigned artist can add notes.")
    if payload.concept_id and payload.concept_id not in collab["concept_ids"]:
        raise ApiError(status_code=400, code="VALIDATION_ERROR", message="Concept is not shared in collaboration.")
    note = repo.add_collaboration_note(
        collaboration_id=collaboration_id,
        artist_actor_id=actor.actor_id,
        concept_id=payload.concept_id,
        note_text=payload.note_text,
    )
    return CollaborationNoteResponse(**note)


@router.get("/{collaboration_id}/notes", response_model=list[CollaborationNoteResponse])
def list_notes(
    collaboration_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> list[CollaborationNoteResponse]:
    collab = repo.get_collaboration(collaboration_id)
    if collab is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Collaboration not found.")
    if actor.role != Role.admin and actor.actor_id not in {collab["user_actor_id"], collab["artist_actor_id"]}:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot access collaboration notes.")
    return [CollaborationNoteResponse(**item) for item in repo.list_collaboration_notes(collaboration_id)]


@router.post("/{collaboration_id}/revoke", response_model=CollaborationResponse)
def revoke_collaboration(
    collaboration_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> CollaborationResponse:
    collab = repo.get_collaboration(collaboration_id)
    if collab is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Collaboration not found.")
    if actor.role != Role.admin and collab["user_actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only owner user can revoke collaboration.")
    updated = repo.revoke_collaboration(collaboration_id)
    return CollaborationResponse(**updated)

