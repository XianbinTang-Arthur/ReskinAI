from fastapi import APIRouter, Depends

from reskin_ai.core.errors import ApiError
from reskin_ai.dependencies import ActorContext, get_current_actor, get_repo
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import ConsentCreateRequest, ConsentResponse, Role

router = APIRouter(prefix="/api/v1/consents", tags=["consents"])


@router.post("", response_model=ConsentResponse)
def create_consent(
    payload: ConsentCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> ConsentResponse:
    if actor.role != Role.user:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only end users can create consent.")
    if not payload.disclaimer_accepted:
        raise ApiError(
            status_code=400,
            code="DISCLAIMER_REQUIRED",
            message="Non-medical disclaimer must be accepted before continuing.",
        )
    record = repo.create_consent(
        actor_id=actor.actor_id,
        policy_version=payload.policy_version,
        disclaimer_accepted=payload.disclaimer_accepted,
    )
    return ConsentResponse(**record)


@router.get("/{consent_id}", response_model=ConsentResponse)
def get_consent(
    consent_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> ConsentResponse:
    record = repo.get_consent(consent_id)
    if record is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Consent record not found.")
    if actor.role != Role.admin and record["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Not allowed to view this consent.")
    return ConsentResponse(**record)

