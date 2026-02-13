import logging
import time

from fastapi import APIRouter, Depends

from reskin_ai.core.config import settings
from reskin_ai.core.errors import ApiError
from reskin_ai.dependencies import ActorContext, get_current_actor, get_model_provider, get_repo, get_storage
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import ConceptResponse, GenerationCreateRequest, GenerationResponse, Role
from reskin_ai.services.generation import build_prompt_text, compute_prompt_hash
from reskin_ai.services.model_provider import ModelGenerationError, ResilientModelProvider
from reskin_ai.services.safety import SafetyEngine
from reskin_ai.services.storage import LocalStorageService

router = APIRouter(prefix="/api/v1/generations", tags=["generations"])
safety_engine = SafetyEngine()
logger = logging.getLogger(__name__)


@router.post("", response_model=GenerationResponse)
def create_generation(
    payload: GenerationCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
    storage: LocalStorageService = Depends(get_storage),
    model_provider: ResilientModelProvider = Depends(get_model_provider),
) -> GenerationResponse:
    started = time.perf_counter()
    if actor.role != Role.user:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only end users can generate concepts.")
    if repo.generation_disabled:
        raise ApiError(
            status_code=503,
            code="GENERATION_DISABLED",
            message="Generation is temporarily disabled by operations.",
        )
    upload = repo.get_upload(payload.upload_id)
    if upload is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Upload not found.")
    if upload["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Upload does not belong to current actor.")
    preference = repo.get_preference(payload.preference_id)
    if preference is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Preference not found.")
    if preference["actor_id"] != actor.actor_id:
        raise ApiError(
            status_code=403,
            code="FORBIDDEN",
            message="Preference does not belong to current actor.",
        )
    upload_bytes = storage.read_upload(local_path=upload.get("local_path"))
    upload_content_type = str(upload.get("content_type", "")) or None
    variant_count = min(payload.variant_count, settings.max_generation_variants)
    prompt_text = build_prompt_text(preference)
    safety_result = safety_engine.evaluate(prompt_text)
    if safety_result.blocked:
        repo.create_safety_event(
            actor_id=actor.actor_id,
            payload={
                "rule_id": safety_result.rule_id,
                "reason": safety_result.reason,
                "severity": "SEV1",
                "request_type": "generation",
            },
        )
        raise ApiError(
            status_code=422,
            code="SAFETY_BLOCKED",
            message="Prompt blocked by safety policy.",
            details={"rule_id": safety_result.rule_id},
        )

    try:
        batch = model_provider.generate(
            prompt_text=prompt_text,
            variant_count=variant_count,
            input_image=upload_bytes,
            input_content_type=upload_content_type,
        )
    except ModelGenerationError as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        repo.record_generation_observation(
            success=False,
            latency_ms=latency_ms,
            provider=exc.provider,
            retries_used=exc.retries_used,
            provider_failures=exc.provider_failures,
            used_fallback=False,
            count_as_request=True,
        )
        raise ApiError(
            status_code=502,
            code="MODEL_PROVIDER_ERROR",
            message="Concept generation provider failed.",
            details={"provider": exc.provider},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.perf_counter() - started) * 1000)
        repo.record_generation_observation(
            success=False,
            latency_ms=latency_ms,
            provider="unknown",
            retries_used=0,
            provider_failures=1,
            used_fallback=False,
            count_as_request=True,
        )
        raise ApiError(
            status_code=502,
            code="MODEL_PROVIDER_ERROR",
            message="Unexpected provider failure during concept generation.",
        ) from exc

    metadata = {
        "model_version": batch.model_version,
        "prompt_version": settings.prompt_version,
        "safety_policy_version": settings.safety_policy_version,
        "prompt_hash": compute_prompt_hash(prompt_text),
    }
    generation = repo.create_generation(
        actor_id=actor.actor_id,
        upload_id=payload.upload_id,
        preference_id=payload.preference_id,
        metadata=metadata,
        variant_count=variant_count,
    )
    concepts_payload = repo.list_generation_concepts(generation["id"])
    if len(batch.assets) != len(concepts_payload):
        latency_ms = int((time.perf_counter() - started) * 1000)
        repo.record_generation_observation(
            success=False,
            latency_ms=latency_ms,
            provider=batch.provider,
            retries_used=batch.retries_used,
            provider_failures=batch.provider_failures,
            used_fallback=batch.used_fallback,
        )
        raise ApiError(
            status_code=502,
            code="MODEL_PROVIDER_ERROR",
            message="Provider returned inconsistent concept count.",
        )
    for concept, asset in zip(concepts_payload, batch.assets, strict=False):
        saved = storage.save_concept_asset(
            concept_id=concept["id"],
            content=asset.content,
            extension=asset.extension,
        )
        repo.update_concept_storage(
            concept["id"],
            storage_uri=str(saved["storage_uri"]),
            local_path=str(saved["local_path"]),
        )
    latency_ms = int((time.perf_counter() - started) * 1000)
    repo.record_generation_observation(
        success=True,
        latency_ms=latency_ms,
        provider=batch.provider,
        retries_used=batch.retries_used,
        provider_failures=batch.provider_failures,
        used_fallback=batch.used_fallback,
    )
    logger.info(
        "generation.completed actor_id=%s generation_id=%s provider=%s latency_ms=%s fallback=%s retries=%s",
        actor.actor_id,
        generation["id"],
        batch.provider,
        latency_ms,
        batch.used_fallback,
        batch.retries_used,
    )
    concepts = [ConceptResponse(**item) for item in repo.list_generation_concepts(generation["id"])]
    return GenerationResponse(**generation, concepts=concepts)


@router.get("/{generation_id}", response_model=GenerationResponse)
def get_generation(
    generation_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> GenerationResponse:
    generation = repo.get_generation(generation_id)
    if generation is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Generation not found.")
    if actor.role != Role.admin and generation["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot access this generation.")
    concepts = [ConceptResponse(**item) for item in repo.list_generation_concepts(generation_id)]
    return GenerationResponse(**generation, concepts=concepts)


@router.get("/{generation_id}/concepts", response_model=list[ConceptResponse])
def list_concepts(
    generation_id: str,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> list[ConceptResponse]:
    generation = repo.get_generation(generation_id)
    if generation is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Generation not found.")
    if actor.role != Role.admin and generation["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot access concepts for this generation.")
    return [ConceptResponse(**item) for item in repo.list_generation_concepts(generation_id)]
