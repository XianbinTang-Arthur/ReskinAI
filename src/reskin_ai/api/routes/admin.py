from fastapi import APIRouter, Depends

from reskin_ai.dependencies import ActorContext, get_repo, require_roles
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import GenerationDisableRequest, MetricsResponse, Role

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/generation/disable", response_model=MetricsResponse)
def set_generation_disabled(
    payload: GenerationDisableRequest,
    _: ActorContext = Depends(require_roles(Role.admin)),
    repo: InMemoryRepository = Depends(get_repo),
) -> MetricsResponse:
    repo.set_generation_disabled(payload.disabled)
    snapshot = repo.metrics_snapshot()
    return MetricsResponse(**snapshot)


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    _: ActorContext = Depends(require_roles(Role.admin)),
    repo: InMemoryRepository = Depends(get_repo),
) -> MetricsResponse:
    snapshot = repo.metrics_snapshot()
    return MetricsResponse(**snapshot)

