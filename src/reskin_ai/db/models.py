from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SessionModel(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[str] = mapped_column(String(64))


class ConsentModel(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    policy_version: Mapped[str] = mapped_column(String(64))
    disclaimer_accepted: Mapped[bool] = mapped_column(Boolean)
    accepted_at: Mapped[str] = mapped_column(String(64))


class PreferenceModel(Base):
    __tablename__ = "preferences"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    style: Mapped[str] = mapped_column(String(100))
    motifs_json: Mapped[str] = mapped_column(Text)
    meaning_keywords_json: Mapped[str] = mapped_column(Text)
    avoid_list_json: Mapped[str] = mapped_column(Text)
    mood: Mapped[str | None] = mapped_column(String(100), nullable=True)


class UploadModel(Base):
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    consent_id: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    storage_uri: Mapped[str] = mapped_column(String(512))
    local_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64))


class GenerationModel(Base):
    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    upload_id: Mapped[str] = mapped_column(String(64), index=True)
    preference_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    model_version: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(128))
    safety_policy_version: Mapped[str] = mapped_column(String(128))
    prompt_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[str] = mapped_column(String(64))


class ConceptModel(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    generation_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    storage_uri: Mapped[str] = mapped_column(String(512))
    local_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    rank: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(64))


class FeedbackModel(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    concept_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    sentiment: Mapped[str] = mapped_column(String(20))
    reason_tags_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(64))


class DeletionModel(Base):
    __tablename__ = "deletions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    requested_at: Mapped[str] = mapped_column(String(64))
    completed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SafetyEventModel(Base):
    __tablename__ = "safety_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16))
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(64))


class CollaborationModel(Base):
    __tablename__ = "collaborations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_actor_id: Mapped[str] = mapped_column(String(64), index=True)
    artist_actor_id: Mapped[str] = mapped_column(String(64), index=True)
    concept_ids_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32))
    granted_at: Mapped[str] = mapped_column(String(64))
    revoked_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CollaborationNoteModel(Base):
    __tablename__ = "collaboration_notes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    collaboration_id: Mapped[str] = mapped_column(String(64), index=True)
    artist_actor_id: Mapped[str] = mapped_column(String(64), index=True)
    concept_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(64))


class SystemStateModel(Base):
    __tablename__ = "system_state"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text)

