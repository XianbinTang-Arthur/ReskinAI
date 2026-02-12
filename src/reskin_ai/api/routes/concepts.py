from fastapi import APIRouter, Depends

from reskin_ai.core.errors import ApiError
from reskin_ai.dependencies import ActorContext, get_current_actor, get_repo
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import ConceptFeedbackRequest, ConceptFeedbackResponse, ConceptSelectResponse, Role

router = APIRouter(prefix="/api/v1/concepts", tags=["concepts"])


def _assert_concept_access(concept_id: str, actor: ActorContext, repo: InMemoryRepository) -> dict:
    concept = repo.get_concept(concept_id)
    if concept is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Concept not found.")
    if actor.role != Role.admin and concept["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot access this concept.")
    return concept


@router.post("/{concept_id}/feedback", response_model=ConceptFeedbackResponse)
def add_feedback(
    concept_id: str,
    payload: ConceptFeedbackRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> ConceptFeedbackResponse:
    _assert_concept_access(concept_id, actor, repo)
    feedback = repo.add_feedback(concept_id, actor.actor_id, payload.model_dump())
    return ConceptFeedbackResponse(**feedback)


@router.post("/{concept_id}/select", response_model=ConceptSelectResponse)
def select_concept(
    concept_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> ConceptSelectResponse:
    _assert_concept_access(concept_id, actor, repo)
    concept = repo.select_concept(concept_id)
    return ConceptSelectResponse(concept_id=concept["id"], selected=concept["selected"])

