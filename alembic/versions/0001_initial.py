"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-12
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index(op.f("ix_sessions_actor_id"), "sessions", ["actor_id"], unique=False)

    op.create_table(
        "consents",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("disclaimer_accepted", sa.Boolean(), nullable=False),
        sa.Column("accepted_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_consents_actor_id"), "consents", ["actor_id"], unique=False)

    op.create_table(
        "preferences",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("style", sa.String(length=100), nullable=False),
        sa.Column("motifs_json", sa.Text(), nullable=False),
        sa.Column("meaning_keywords_json", sa.Text(), nullable=False),
        sa.Column("avoid_list_json", sa.Text(), nullable=False),
        sa.Column("mood", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_preferences_actor_id"), "preferences", ["actor_id"], unique=False)

    op.create_table(
        "uploads",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("consent_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("storage_uri", sa.String(length=512), nullable=False),
        sa.Column("local_path", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_uploads_actor_id"), "uploads", ["actor_id"], unique=False)
    op.create_index(op.f("ix_uploads_consent_id"), "uploads", ["consent_id"], unique=False)

    op.create_table(
        "generations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("upload_id", sa.String(length=64), nullable=False),
        sa.Column("preference_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("model_version", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("safety_policy_version", sa.String(length=128), nullable=False),
        sa.Column("prompt_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generations_actor_id"), "generations", ["actor_id"], unique=False)
    op.create_index(op.f("ix_generations_upload_id"), "generations", ["upload_id"], unique=False)
    op.create_index(op.f("ix_generations_preference_id"), "generations", ["preference_id"], unique=False)

    op.create_table(
        "concepts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("generation_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("storage_uri", sa.String(length=512), nullable=False),
        sa.Column("local_path", sa.String(length=512), nullable=True),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_concepts_generation_id"), "concepts", ["generation_id"], unique=False)
    op.create_index(op.f("ix_concepts_actor_id"), "concepts", ["actor_id"], unique=False)

    op.create_table(
        "feedbacks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("sentiment", sa.String(length=20), nullable=False),
        sa.Column("reason_tags_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_feedbacks_concept_id"), "feedbacks", ["concept_id"], unique=False)
    op.create_index(op.f("ix_feedbacks_actor_id"), "feedbacks", ["actor_id"], unique=False)

    op.create_table(
        "deletions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_at", sa.String(length=64), nullable=False),
        sa.Column("completed_at", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deletions_actor_id"), "deletions", ["actor_id"], unique=False)

    op.create_table(
        "safety_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_safety_events_actor_id"), "safety_events", ["actor_id"], unique=False)

    op.create_table(
        "collaborations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_actor_id", sa.String(length=64), nullable=False),
        sa.Column("artist_actor_id", sa.String(length=64), nullable=False),
        sa.Column("concept_ids_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("granted_at", sa.String(length=64), nullable=False),
        sa.Column("revoked_at", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_collaborations_user_actor_id"), "collaborations", ["user_actor_id"], unique=False)
    op.create_index(op.f("ix_collaborations_artist_actor_id"), "collaborations", ["artist_actor_id"], unique=False)

    op.create_table(
        "collaboration_notes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("collaboration_id", sa.String(length=64), nullable=False),
        sa.Column("artist_actor_id", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=64), nullable=True),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_collaboration_notes_collaboration_id"),
        "collaboration_notes",
        ["collaboration_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_collaboration_notes_artist_actor_id"),
        "collaboration_notes",
        ["artist_actor_id"],
        unique=False,
    )

    op.create_table(
        "system_state",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("system_state")
    op.drop_index(op.f("ix_collaboration_notes_artist_actor_id"), table_name="collaboration_notes")
    op.drop_index(op.f("ix_collaboration_notes_collaboration_id"), table_name="collaboration_notes")
    op.drop_table("collaboration_notes")
    op.drop_index(op.f("ix_collaborations_artist_actor_id"), table_name="collaborations")
    op.drop_index(op.f("ix_collaborations_user_actor_id"), table_name="collaborations")
    op.drop_table("collaborations")
    op.drop_index(op.f("ix_safety_events_actor_id"), table_name="safety_events")
    op.drop_table("safety_events")
    op.drop_index(op.f("ix_deletions_actor_id"), table_name="deletions")
    op.drop_table("deletions")
    op.drop_index(op.f("ix_feedbacks_actor_id"), table_name="feedbacks")
    op.drop_index(op.f("ix_feedbacks_concept_id"), table_name="feedbacks")
    op.drop_table("feedbacks")
    op.drop_index(op.f("ix_concepts_actor_id"), table_name="concepts")
    op.drop_index(op.f("ix_concepts_generation_id"), table_name="concepts")
    op.drop_table("concepts")
    op.drop_index(op.f("ix_generations_preference_id"), table_name="generations")
    op.drop_index(op.f("ix_generations_upload_id"), table_name="generations")
    op.drop_index(op.f("ix_generations_actor_id"), table_name="generations")
    op.drop_table("generations")
    op.drop_index(op.f("ix_uploads_consent_id"), table_name="uploads")
    op.drop_index(op.f("ix_uploads_actor_id"), table_name="uploads")
    op.drop_table("uploads")
    op.drop_index(op.f("ix_preferences_actor_id"), table_name="preferences")
    op.drop_table("preferences")
    op.drop_index(op.f("ix_consents_actor_id"), table_name="consents")
    op.drop_table("consents")
    op.drop_index(op.f("ix_sessions_actor_id"), table_name="sessions")
    op.drop_table("sessions")
