"""Initial migration for compression jobs and batch compression jobs.

Revision ID: 001_initial
Revises:
Create Date: 2026-10-31 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create batch_compression_jobs table
    op.create_table(
        "batch_compression_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shared_settings", sa.JSON(), nullable=False),
        sa.Column("aggregate_original_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("aggregate_compressed_size", sa.BigInteger(), nullable=False, server_default="0"),
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
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_batch_compression_jobs_status"),
        "batch_compression_jobs",
        ["status"],
        unique=False,
    )

    # 2. Create compression_jobs table
    op.create_table(
        "compression_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("batch_id", sa.UUID(), nullable=True),
        sa.Column("original_file_reference", sa.String(length=1024), nullable=False),
        sa.Column("output_file_reference", sa.String(length=1024), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("original_size", sa.BigInteger(), nullable=False),
        sa.Column("output_size", sa.BigInteger(), nullable=True),
        sa.Column("file_format", sa.String(length=32), nullable=False),
        sa.Column("compression_preset", sa.String(length=64), nullable=True),
        sa.Column("target_size", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("target_achieved", sa.Boolean(), nullable=True),
        sa.Column("warning_message", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "job_metadata",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
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
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batch_compression_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_compression_jobs_batch_id"),
        "compression_jobs",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compression_jobs_file_format"),
        "compression_jobs",
        ["file_format"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compression_jobs_status"),
        "compression_jobs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_compression_jobs_status"), table_name="compression_jobs")
    op.drop_index(op.f("ix_compression_jobs_file_format"), table_name="compression_jobs")
    op.drop_index(op.f("ix_compression_jobs_batch_id"), table_name="compression_jobs")
    op.drop_table("compression_jobs")
    op.drop_index(op.f("ix_batch_compression_jobs_status"), table_name="batch_compression_jobs")
    op.drop_table("batch_compression_jobs")
