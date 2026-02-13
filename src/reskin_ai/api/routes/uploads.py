import hashlib

from fastapi import APIRouter, Depends, File, Form, UploadFile

from reskin_ai.core.config import settings
from reskin_ai.core.errors import ApiError
from reskin_ai.dependencies import ActorContext, get_current_actor, get_repo, get_storage
from reskin_ai.repository import InMemoryRepository
from reskin_ai.schemas import Role, UploadCreateRequest, UploadResponse
from reskin_ai.services.storage import LocalStorageService

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


def _assert_user_with_consent(
    *,
    actor: ActorContext,
    consent_id: str,
    repo: InMemoryRepository,
) -> None:
    if actor.role != Role.user:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only end users can upload scar images.")
    consent = repo.get_consent(consent_id)
    if consent is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Consent record not found.")
    if consent["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Cannot use consent owned by another actor.")


@router.post("", response_model=UploadResponse)
def create_upload(
    payload: UploadCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
) -> UploadResponse:
    _assert_user_with_consent(actor=actor, consent_id=payload.consent_id, repo=repo)
    if payload.content_type not in settings.allowed_upload_types:
        raise ApiError(
            status_code=400,
            code="UNSUPPORTED_MEDIA_TYPE",
            message="Unsupported upload content type.",
            details={"allowed_types": sorted(settings.allowed_upload_types)},
        )
    record = repo.create_upload(actor.actor_id, payload.model_dump())
    return UploadResponse(**record)


@router.post("/file", response_model=UploadResponse)
async def create_upload_file(
    consent_id: str = Form(...),
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
    storage: LocalStorageService = Depends(get_storage),
) -> UploadResponse:
    _assert_user_with_consent(actor=actor, consent_id=consent_id, repo=repo)
    if file.content_type not in settings.allowed_upload_types:
        raise ApiError(
            status_code=400,
            code="UNSUPPORTED_MEDIA_TYPE",
            message="Unsupported upload content type.",
            details={"allowed_types": sorted(settings.allowed_upload_types)},
        )
    content = await file.read()
    if not content:
        raise ApiError(status_code=400, code="VALIDATION_ERROR", message="Empty file upload is not allowed.")
    if len(content) > settings.max_upload_size_bytes:
        raise ApiError(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message="Uploaded file exceeds size limit.",
            details={"max_upload_size_bytes": settings.max_upload_size_bytes},
        )
    saved = storage.save_upload(filename=file.filename or "upload.bin", content_type=file.content_type, content=content)
    payload = {
        "consent_id": consent_id,
        "filename": file.filename or "upload.bin",
        "content_type": file.content_type,
        "size_bytes": saved["size_bytes"],
        "checksum": hashlib.sha256(content).hexdigest(),
        "storage_uri": saved["storage_uri"],
        "local_path": saved["local_path"],
    }
    record = repo.create_upload(actor.actor_id, payload)
    return UploadResponse(**record)


@router.post("/{upload_id}/mask")
async def upload_scar_mask(
    upload_id: str,
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_current_actor),
    repo: InMemoryRepository = Depends(get_repo),
    storage: LocalStorageService = Depends(get_storage),
) -> dict[str, object]:
    if actor.role != Role.user:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Only end users can upload scar masks.")
    upload = repo.get_upload(upload_id)
    if upload is None:
        raise ApiError(status_code=404, code="NOT_FOUND", message="Upload not found.")
    if upload["actor_id"] != actor.actor_id:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Upload does not belong to current actor.")
    if file.content_type != "image/png":
        raise ApiError(
            status_code=400,
            code="UNSUPPORTED_MEDIA_TYPE",
            message="Mask must be a PNG image.",
        )
    content = await file.read()
    if not content:
        raise ApiError(status_code=400, code="VALIDATION_ERROR", message="Empty mask upload is not allowed.")
    if len(content) > settings.max_upload_size_bytes:
        raise ApiError(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message="Uploaded mask exceeds size limit.",
            details={"max_upload_size_bytes": settings.max_upload_size_bytes},
        )
    saved = storage.save_upload_mask(upload_id=upload_id, content=content)
    return {
        "upload_id": upload_id,
        "storage_uri": saved["storage_uri"],
        "size_bytes": saved["size_bytes"],
        "checksum": saved["checksum"],
    }
