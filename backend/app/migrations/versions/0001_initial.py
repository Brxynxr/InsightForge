"""Initial migration for PromptForge.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.String(36), unique=True, nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("total_records", sa.Integer, nullable=False, server_default="0"),
        sa.Column("validated_records", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rejected_records", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("target_language", sa.String(10), nullable=True),
        sa.Column(
            "export_formats",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "job_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "job_records",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer, nullable=False, index=True),
        sa.Column("record_index", sa.Integer, nullable=False),
        sa.Column(
            "original_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("optimized_text", sa.Text, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("prompt", sa.Text, nullable=True),
        sa.Column("llm_response", sa.Text, nullable=True),
        sa.Column(
            "parsed_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("job_records")
    op.drop_table("jobs")
