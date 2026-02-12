from __future__ import annotations

import json
import math
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from reskin_ai.db.models import (
    Base,
    CollaborationModel,
    CollaborationNoteModel,
    ConceptModel,
    ConsentModel,
    DeletionModel,
    FeedbackModel,
    GenerationModel,
    PreferenceModel,
    SafetyEventModel,
    SessionModel,
    SystemStateModel,
    UploadModel,
)
from reskin_ai.db.session import create_engine_and_session_factory


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class InMemoryRepository:
    """Database-backed repository kept behind existing interface for compatibility."""

    def __init__(self, persist_path: Path | None = None, db_url: str | None = None) -> None:
        self.persist_path = persist_path
        self.engine, self.session_factory = create_engine_and_session_factory(db_url=db_url)
        self.ensure_schema()
        self._ensure_system_state()

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _loads(value: str | None, default: Any) -> Any:
        if not value:
            return default
        return json.loads(value)

    def _session(self) -> Session:
        return self.session_factory()

    def ensure_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def _ensure_system_state(self) -> None:
        with self._session() as session:
            row = session.get(SystemStateModel, "runtime")
            if row is None:
                value = {
                    "generation_disabled": False,
                    "counters": {
                        "generation_requests_total": 0,
                        "generation_success_total": 0,
                        "generation_failures_total": 0,
                        "generation_provider_failures_total": 0,
                        "generation_retries_total": 0,
                        "generation_fallback_total": 0,
                        "generation_latency_ms_last": 0,
                        "generation_latency_ms_avg": 0,
                        "generation_latency_ms_p95": 0,
                        "safety_blocks_total": 0,
                        "deletion_requests_total": 0,
                        "collaboration_invites_total": 0,
                    },
                    "latency_windows": {
                        "generation_ms": [],
                    },
                    "providers": {
                        "last_generation_provider": "",
                    },
                }
                session.add(SystemStateModel(key="runtime", value_json=self._json(value)))
                session.commit()

    def _get_runtime_state(self, session: Session) -> dict[str, Any]:
        row = session.get(SystemStateModel, "runtime")
        if row is None:
            self._ensure_system_state()
            row = session.get(SystemStateModel, "runtime")
        assert row is not None
        return self._loads(row.value_json, {})

    def _set_runtime_state(self, session: Session, state: dict[str, Any]) -> None:
        row = session.get(SystemStateModel, "runtime")
        assert row is not None
        row.value_json = self._json(state)

    def _inc_counter(self, session: Session, key: str, delta: int = 1) -> None:
        state = self._get_runtime_state(session)
        counters = state.setdefault("counters", {})
        counters[key] = int(counters.get(key, 0)) + delta
        self._set_runtime_state(session, state)

    def _record_generation_latency(self, session: Session, latency_ms: int) -> None:
        state = self._get_runtime_state(session)
        windows = state.setdefault("latency_windows", {})
        values = list(windows.get("generation_ms", []))
        values.append(int(latency_ms))
        values = values[-100:]
        windows["generation_ms"] = values
        counters = state.setdefault("counters", {})
        counters["generation_latency_ms_last"] = values[-1]
        counters["generation_latency_ms_avg"] = int(round(sum(values) / len(values)))
        sorted_values = sorted(values)
        index = max(0, math.ceil(len(sorted_values) * 0.95) - 1)
        counters["generation_latency_ms_p95"] = int(sorted_values[index])
        self._set_runtime_state(session, state)

    def reset(self) -> None:
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self._ensure_system_state()

    def create_session(self, role: str) -> dict[str, Any]:
        token = uuid.uuid4().hex
        actor_id = self._new_id(role)
        record = SessionModel(token=token, actor_id=actor_id, role=role, created_at=utc_now_iso())
        with self._session() as session:
            session.add(record)
            session.commit()
        return {"token": token, "actor_id": actor_id, "role": role, "created_at": record.created_at}

    def get_session_by_token(self, token: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(SessionModel, token)
            if row is None:
                return None
            return {"token": row.token, "actor_id": row.actor_id, "role": row.role, "created_at": row.created_at}

    def create_consent(
        self,
        *,
        actor_id: str,
        policy_version: str,
        disclaimer_accepted: bool,
    ) -> dict[str, Any]:
        consent_id = self._new_id("consent")
        accepted_at = utc_now_iso()
        with self._session() as session:
            session.add(
                ConsentModel(
                    id=consent_id,
                    actor_id=actor_id,
                    policy_version=policy_version,
                    disclaimer_accepted=disclaimer_accepted,
                    accepted_at=accepted_at,
                )
            )
            session.commit()
        return {
            "id": consent_id,
            "actor_id": actor_id,
            "policy_version": policy_version,
            "disclaimer_accepted": disclaimer_accepted,
            "accepted_at": accepted_at,
        }

    def get_consent(self, consent_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(ConsentModel, consent_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "actor_id": row.actor_id,
                "policy_version": row.policy_version,
                "disclaimer_accepted": row.disclaimer_accepted,
                "accepted_at": row.accepted_at,
            }

    def create_preference(self, actor_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._session() as session:
            version = (
                session.query(PreferenceModel)
                .filter(PreferenceModel.actor_id == actor_id)
                .count()
                + 1
            )
            pref_id = self._new_id("pref")
            row = PreferenceModel(
                id=pref_id,
                actor_id=actor_id,
                version=version,
                style=str(payload["style"]),
                motifs_json=self._json(payload.get("motifs", [])),
                meaning_keywords_json=self._json(payload.get("meaning_keywords", [])),
                avoid_list_json=self._json(payload.get("avoid_list", [])),
                mood=payload.get("mood"),
            )
            session.add(row)
            session.commit()
        return {
            "id": pref_id,
            "actor_id": actor_id,
            "version": version,
            "style": payload["style"],
            "motifs": payload.get("motifs", []),
            "meaning_keywords": payload.get("meaning_keywords", []),
            "avoid_list": payload.get("avoid_list", []),
            "mood": payload.get("mood"),
        }

    def get_preference(self, pref_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(PreferenceModel, pref_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "actor_id": row.actor_id,
                "version": row.version,
                "style": row.style,
                "motifs": self._loads(row.motifs_json, []),
                "meaning_keywords": self._loads(row.meaning_keywords_json, []),
                "avoid_list": self._loads(row.avoid_list_json, []),
                "mood": row.mood,
            }

    def create_upload(self, actor_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        upload_id = self._new_id("upload")
        created_at = utc_now_iso()
        storage_uri = str(payload.get("storage_uri", f"/media/uploads/{upload_id}.bin"))
        local_path = payload.get("local_path")
        with self._session() as session:
            row = UploadModel(
                id=upload_id,
                actor_id=actor_id,
                consent_id=str(payload["consent_id"]),
                filename=str(payload["filename"]),
                content_type=str(payload["content_type"]),
                size_bytes=int(payload["size_bytes"]),
                checksum=payload.get("checksum"),
                storage_uri=storage_uri,
                local_path=local_path,
                created_at=created_at,
            )
            session.add(row)
            session.commit()
        return {
            "id": upload_id,
            "actor_id": actor_id,
            "consent_id": str(payload["consent_id"]),
            "filename": str(payload["filename"]),
            "content_type": str(payload["content_type"]),
            "size_bytes": int(payload["size_bytes"]),
            "checksum": payload.get("checksum"),
            "storage_uri": storage_uri,
            "local_path": local_path,
            "created_at": created_at,
        }

    def get_upload(self, upload_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(UploadModel, upload_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "actor_id": row.actor_id,
                "consent_id": row.consent_id,
                "filename": row.filename,
                "content_type": row.content_type,
                "size_bytes": row.size_bytes,
                "checksum": row.checksum,
                "storage_uri": row.storage_uri,
                "local_path": row.local_path,
                "created_at": row.created_at,
            }

    def create_generation(
        self,
        *,
        actor_id: str,
        upload_id: str,
        preference_id: str,
        metadata: dict[str, Any],
        variant_count: int,
    ) -> dict[str, Any]:
        generation_id = self._new_id("gen")
        created_at = utc_now_iso()
        with self._session() as session:
            session.add(
                GenerationModel(
                    id=generation_id,
                    actor_id=actor_id,
                    upload_id=upload_id,
                    preference_id=preference_id,
                    status="completed",
                    model_version=str(metadata["model_version"]),
                    prompt_version=str(metadata["prompt_version"]),
                    safety_policy_version=str(metadata["safety_policy_version"]),
                    prompt_hash=str(metadata["prompt_hash"]),
                    created_at=created_at,
                )
            )
            concept_ids: list[str] = []
            for index in range(variant_count):
                concept_id = self._new_id("concept")
                concept_ids.append(concept_id)
                session.add(
                    ConceptModel(
                        id=concept_id,
                        generation_id=generation_id,
                        actor_id=actor_id,
                        storage_uri=f"/media/concepts/{generation_id}_{index + 1}.svg",
                        local_path=None,
                        selected=False,
                        rank=index + 1,
                        created_at=created_at,
                    )
                )
            self._inc_counter(session, "generation_requests_total", 1)
            session.commit()
        return {
            "id": generation_id,
            "actor_id": actor_id,
            "upload_id": upload_id,
            "preference_id": preference_id,
            "status": "completed",
            "concept_ids": concept_ids,
            **metadata,
        }

    def record_generation_observation(
        self,
        *,
        success: bool,
        latency_ms: int,
        provider: str,
        retries_used: int = 0,
        provider_failures: int = 0,
        used_fallback: bool = False,
        count_as_request: bool = False,
    ) -> None:
        with self._session() as session:
            if count_as_request:
                self._inc_counter(session, "generation_requests_total", 1)
            if success:
                self._inc_counter(session, "generation_success_total", 1)
            else:
                self._inc_counter(session, "generation_failures_total", 1)
            if retries_used > 0:
                self._inc_counter(session, "generation_retries_total", retries_used)
            if provider_failures > 0:
                self._inc_counter(session, "generation_provider_failures_total", provider_failures)
            if used_fallback:
                self._inc_counter(session, "generation_fallback_total", 1)
            self._record_generation_latency(session, latency_ms)
            state = self._get_runtime_state(session)
            providers = state.setdefault("providers", {})
            providers["last_generation_provider"] = provider
            self._set_runtime_state(session, state)
            session.commit()

    def update_concept_storage(self, concept_id: str, *, storage_uri: str, local_path: str) -> dict[str, Any]:
        with self._session() as session:
            row = session.get(ConceptModel, concept_id)
            assert row is not None
            row.storage_uri = storage_uri
            row.local_path = local_path
            session.commit()
            return self.get_concept(concept_id) or {}

    def get_generation(self, generation_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(GenerationModel, generation_id)
            if row is None:
                return None
            concept_ids = [
                concept.id
                for concept in session.execute(
                    select(ConceptModel).where(ConceptModel.generation_id == generation_id).order_by(ConceptModel.rank)
                ).scalars()
            ]
            return {
                "id": row.id,
                "actor_id": row.actor_id,
                "upload_id": row.upload_id,
                "preference_id": row.preference_id,
                "status": row.status,
                "concept_ids": concept_ids,
                "model_version": row.model_version,
                "prompt_version": row.prompt_version,
                "safety_policy_version": row.safety_policy_version,
                "prompt_hash": row.prompt_hash,
            }

    def list_generation_concepts(self, generation_id: str) -> list[dict[str, Any]]:
        with self._session() as session:
            rows = session.execute(
                select(ConceptModel).where(ConceptModel.generation_id == generation_id).order_by(ConceptModel.rank)
            ).scalars()
            return [
                {
                    "id": row.id,
                    "generation_id": row.generation_id,
                    "actor_id": row.actor_id,
                    "storage_uri": row.storage_uri,
                    "local_path": row.local_path,
                    "selected": row.selected,
                }
                for row in rows
            ]

    def get_concept(self, concept_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(ConceptModel, concept_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "generation_id": row.generation_id,
                "actor_id": row.actor_id,
                "storage_uri": row.storage_uri,
                "local_path": row.local_path,
                "selected": row.selected,
            }

    def add_feedback(self, concept_id: str, actor_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        feedback_id = self._new_id("feedback")
        created_at = utc_now_iso()
        with self._session() as session:
            session.add(
                FeedbackModel(
                    id=feedback_id,
                    concept_id=concept_id,
                    actor_id=actor_id,
                    sentiment=str(payload["sentiment"]),
                    reason_tags_json=self._json(payload.get("reason_tags", [])),
                    created_at=created_at,
                )
            )
            session.commit()
        return {
            "id": feedback_id,
            "concept_id": concept_id,
            "actor_id": actor_id,
            "sentiment": str(payload["sentiment"]),
            "reason_tags": payload.get("reason_tags", []),
        }

    def select_concept(self, concept_id: str) -> dict[str, Any]:
        with self._session() as session:
            row = session.get(ConceptModel, concept_id)
            assert row is not None
            row.selected = True
            session.commit()
        return self.get_concept(concept_id) or {}

    def create_safety_event(self, *, actor_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        event_id = self._new_id("safety")
        created_at = utc_now_iso()
        with self._session() as session:
            session.add(
                SafetyEventModel(
                    id=event_id,
                    actor_id=actor_id,
                    severity=str(payload.get("severity", "SEV1")),
                    payload_json=self._json(payload),
                    created_at=created_at,
                )
            )
            self._inc_counter(session, "safety_blocks_total", 1)
            self._inc_counter(session, "generation_failures_total", 1)
            session.commit()
        return {
            "id": event_id,
            "actor_id": actor_id,
            "severity": str(payload.get("severity", "SEV1")),
            "payload": payload,
            "created_at": created_at,
        }

    def create_collaboration(
        self,
        *,
        user_actor_id: str,
        artist_actor_id: str,
        concept_ids: list[str],
    ) -> dict[str, Any]:
        collab_id = self._new_id("collab")
        granted_at = utc_now_iso()
        with self._session() as session:
            session.add(
                CollaborationModel(
                    id=collab_id,
                    user_actor_id=user_actor_id,
                    artist_actor_id=artist_actor_id,
                    concept_ids_json=self._json(concept_ids),
                    status="active",
                    granted_at=granted_at,
                    revoked_at=None,
                )
            )
            self._inc_counter(session, "collaboration_invites_total", 1)
            session.commit()
        return {
            "id": collab_id,
            "user_actor_id": user_actor_id,
            "artist_actor_id": artist_actor_id,
            "concept_ids": concept_ids,
            "status": "active",
            "granted_at": granted_at,
            "revoked_at": None,
        }

    def get_collaboration(self, collaboration_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(CollaborationModel, collaboration_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "user_actor_id": row.user_actor_id,
                "artist_actor_id": row.artist_actor_id,
                "concept_ids": self._loads(row.concept_ids_json, []),
                "status": row.status,
                "granted_at": row.granted_at,
                "revoked_at": row.revoked_at,
            }

    def add_collaboration_note(
        self,
        *,
        collaboration_id: str,
        artist_actor_id: str,
        concept_id: str | None,
        note_text: str,
    ) -> dict[str, Any]:
        note_id = self._new_id("note")
        created_at = utc_now_iso()
        with self._session() as session:
            session.add(
                CollaborationNoteModel(
                    id=note_id,
                    collaboration_id=collaboration_id,
                    artist_actor_id=artist_actor_id,
                    concept_id=concept_id,
                    note_text=note_text,
                    created_at=created_at,
                )
            )
            session.commit()
        return {
            "id": note_id,
            "collaboration_id": collaboration_id,
            "artist_actor_id": artist_actor_id,
            "concept_id": concept_id,
            "note_text": note_text,
            "created_at": created_at,
        }

    def list_collaboration_notes(self, collaboration_id: str) -> list[dict[str, Any]]:
        with self._session() as session:
            rows = session.execute(
                select(CollaborationNoteModel).where(CollaborationNoteModel.collaboration_id == collaboration_id)
            ).scalars()
            return [
                {
                    "id": row.id,
                    "collaboration_id": row.collaboration_id,
                    "artist_actor_id": row.artist_actor_id,
                    "concept_id": row.concept_id,
                    "note_text": row.note_text,
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    def revoke_collaboration(self, collaboration_id: str) -> dict[str, Any]:
        with self._session() as session:
            row = session.get(CollaborationModel, collaboration_id)
            assert row is not None
            row.status = "revoked"
            row.revoked_at = utc_now_iso()
            session.commit()
        return self.get_collaboration(collaboration_id) or {}

    def create_deletion(self, *, actor_id: str, reason: str | None) -> dict[str, Any]:
        deletion_id = self._new_id("deletion")
        requested_at = utc_now_iso()
        with self._session() as session:
            session.add(
                DeletionModel(
                    id=deletion_id,
                    actor_id=actor_id,
                    reason=reason,
                    status="pending",
                    requested_at=requested_at,
                    completed_at=None,
                )
            )
            self._inc_counter(session, "deletion_requests_total", 1)
            session.commit()
        return {
            "id": deletion_id,
            "actor_id": actor_id,
            "reason": reason,
            "status": "pending",
            "requested_at": requested_at,
            "completed_at": None,
        }

    @staticmethod
    def _safe_delete_path(path_value: str | None) -> None:
        if not path_value:
            return
        path = Path(path_value)
        if path.exists() and path.is_file():
            path.unlink()

    def execute_deletion(self, deletion_id: str) -> dict[str, Any]:
        with self._session() as session:
            deletion_row = session.get(DeletionModel, deletion_id)
            assert deletion_row is not None
            actor_id = deletion_row.actor_id

            upload_rows = session.execute(select(UploadModel).where(UploadModel.actor_id == actor_id)).scalars().all()
            for row in upload_rows:
                self._safe_delete_path(row.local_path)
                session.delete(row)

            generation_rows = (
                session.execute(select(GenerationModel).where(GenerationModel.actor_id == actor_id)).scalars().all()
            )
            for generation in generation_rows:
                concept_rows = (
                    session.execute(select(ConceptModel).where(ConceptModel.generation_id == generation.id))
                    .scalars()
                    .all()
                )
                for concept in concept_rows:
                    self._safe_delete_path(concept.local_path)
                    session.execute(delete(FeedbackModel).where(FeedbackModel.concept_id == concept.id))
                    session.delete(concept)
                session.delete(generation)

            session.execute(delete(PreferenceModel).where(PreferenceModel.actor_id == actor_id))
            session.execute(delete(ConsentModel).where(ConsentModel.actor_id == actor_id))
            session.execute(delete(CollaborationModel).where(CollaborationModel.user_actor_id == actor_id))
            session.execute(delete(CollaborationModel).where(CollaborationModel.artist_actor_id == actor_id))
            session.execute(delete(CollaborationNoteModel).where(CollaborationNoteModel.artist_actor_id == actor_id))
            session.execute(delete(SessionModel).where(SessionModel.actor_id == actor_id))

            deletion_row.status = "completed"
            deletion_row.completed_at = utc_now_iso()
            session.commit()

        return self.get_deletion(deletion_id) or {}

    def get_deletion(self, deletion_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            row = session.get(DeletionModel, deletion_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "actor_id": row.actor_id,
                "reason": row.reason,
                "status": row.status,
                "requested_at": row.requested_at,
                "completed_at": row.completed_at,
            }

    @property
    def generation_disabled(self) -> bool:
        with self._session() as session:
            state = self._get_runtime_state(session)
            return bool(state.get("generation_disabled", False))

    def set_generation_disabled(self, disabled: bool) -> None:
        with self._session() as session:
            state = self._get_runtime_state(session)
            state["generation_disabled"] = disabled
            self._set_runtime_state(session, state)
            session.commit()

    def metrics_snapshot(self) -> dict[str, Any]:
        with self._session() as session:
            state = self._get_runtime_state(session)
            providers = state.get("providers", {})
            return {
                "generation_disabled": bool(state.get("generation_disabled", False)),
                "counters": dict(state.get("counters", {})),
                "diagnostics": {
                    "last_generation_provider": str(providers.get("last_generation_provider", "")),
                },
            }
