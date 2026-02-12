from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Role(StrEnum):
    user = "user"
    artist = "artist"
    admin = "admin"


class Sentiment(StrEnum):
    like = "like"
    dislike = "dislike"


class SessionCreateRequest(BaseModel):
    role: Role
    actor_name: str | None = None


class SessionResponse(BaseModel):
    token: str
    actor_id: str
    role: Role


class ActorResponse(BaseModel):
    actor_id: str
    role: Role


class ConsentCreateRequest(BaseModel):
    policy_version: str = "consent-v1"
    disclaimer_accepted: bool


class ConsentResponse(BaseModel):
    id: str
    actor_id: str
    policy_version: str
    disclaimer_accepted: bool
    accepted_at: str


class PreferenceCreateRequest(BaseModel):
    style: str = Field(min_length=1, max_length=100)
    motifs: list[str] = Field(default_factory=list)
    meaning_keywords: list[str] = Field(default_factory=list)
    avoid_list: list[str] = Field(default_factory=list)
    mood: str | None = None


class PreferenceResponse(BaseModel):
    id: str
    actor_id: str
    version: int
    style: str
    motifs: list[str]
    meaning_keywords: list[str]
    avoid_list: list[str]
    mood: str | None


class UploadCreateRequest(BaseModel):
    consent_id: str
    filename: str
    content_type: str
    size_bytes: int = Field(gt=0)
    checksum: str | None = None


class UploadResponse(BaseModel):
    id: str
    actor_id: str
    consent_id: str
    storage_uri: str
    content_type: str
    size_bytes: int


class GenerationCreateRequest(BaseModel):
    upload_id: str
    preference_id: str
    variant_count: int = Field(default=3, ge=1, le=5)


class ConceptResponse(BaseModel):
    id: str
    generation_id: str
    actor_id: str
    storage_uri: str
    selected: bool = False


class GenerationResponse(BaseModel):
    id: str
    actor_id: str
    upload_id: str
    preference_id: str
    status: str
    model_version: str
    prompt_version: str
    safety_policy_version: str
    prompt_hash: str
    concepts: list[ConceptResponse]


class ConceptFeedbackRequest(BaseModel):
    sentiment: Sentiment
    reason_tags: list[str] = Field(default_factory=list)


class ConceptFeedbackResponse(BaseModel):
    id: str
    concept_id: str
    actor_id: str
    sentiment: Sentiment
    reason_tags: list[str]


class ConceptSelectResponse(BaseModel):
    concept_id: str
    selected: bool


class DeletionCreateRequest(BaseModel):
    reason: str | None = None


class DeletionResponse(BaseModel):
    id: str
    actor_id: str
    status: str
    requested_at: str
    completed_at: str | None


class GenerationDisableRequest(BaseModel):
    disabled: bool
    reason: str | None = None


class MetricsResponse(BaseModel):
    generation_disabled: bool
    counters: dict[str, int]
    diagnostics: dict[str, str] = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: str
    severity: str
    payload: dict[str, Any]


class CollaborationInviteRequest(BaseModel):
    artist_actor_id: str
    concept_ids: list[str] = Field(default_factory=list)


class CollaborationResponse(BaseModel):
    id: str
    user_actor_id: str
    artist_actor_id: str
    concept_ids: list[str]
    status: str
    granted_at: str
    revoked_at: str | None


class CollaborationNoteCreateRequest(BaseModel):
    concept_id: str | None = None
    note_text: str = Field(min_length=1, max_length=1000)


class CollaborationNoteResponse(BaseModel):
    id: str
    collaboration_id: str
    artist_actor_id: str
    concept_id: str | None
    note_text: str
    created_at: str
