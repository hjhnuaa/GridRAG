"""Initial GridRAG schema."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260418_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial database schema."""

    op.create_table(
        "residents",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("id_number", sa.String(length=32), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_visit_at", sa.DateTime(), nullable=True),
        sa.Column("visit_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_residents")),
    )
    op.create_index("ix_residents_name_address", "residents", ["name", "address"], unique=False)

    op.create_table(
        "documents",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.String(length=100), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index("ix_documents_name", "documents", ["name"], unique=False)
    op.create_index("ix_documents_status_doc_type", "documents", ["status", "doc_type"], unique=False)

    op.create_table(
        "visit_records",
        sa.Column("resident_id", sa.String(length=36), nullable=False),
        sa.Column("visitor_name", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], name=op.f("fk_visit_records_resident_id_residents")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visit_records")),
    )
    op.create_index(
        "ix_visit_records_resident_id_created_at",
        "visit_records",
        ["resident_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "events",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("reporter_name", sa.String(length=100), nullable=False),
        sa.Column("resident_id", sa.String(length=36), nullable=True),
        sa.Column("ai_suggestion", sa.Text(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], name=op.f("fk_events_resident_id_residents")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index("ix_events_resident_id", "events", ["resident_id"], unique=False)
    op.create_index(
        "ix_events_status_category_created_at",
        "events",
        ["status", "category", "created_at"],
        unique=False,
    )

    op.create_table(
        "document_chunks",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("doc_name", sa.String(length=255), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=255), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_chunks_document_id_documents"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)
    op.create_index("ix_document_chunks_doc_type", "document_chunks", ["doc_type"], unique=False)

    op.create_table(
        "chat_histories",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_histories")),
    )
    op.create_index(
        "ix_chat_histories_session_id_created_at",
        "chat_histories",
        ["session_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "retrieval_logs",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("rewritten_query", sa.Text(), nullable=True),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("retrieval_ms", sa.Integer(), nullable=False),
        sa.Column("rerank_scores", sa.JSON(), nullable=False),
        sa.Column("top_chunks", sa.JSON(), nullable=False),
        sa.Column("is_grounded", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_logs")),
    )
    op.create_index(
        "ix_retrieval_logs_session_id_created_at",
        "retrieval_logs",
        ["session_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all tables."""

    op.drop_index("ix_retrieval_logs_session_id_created_at", table_name="retrieval_logs")
    op.drop_table("retrieval_logs")
    op.drop_index("ix_chat_histories_session_id_created_at", table_name="chat_histories")
    op.drop_table("chat_histories")
    op.drop_index("ix_document_chunks_doc_type", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("ix_events_status_category_created_at", table_name="events")
    op.drop_index("ix_events_resident_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_visit_records_resident_id_created_at", table_name="visit_records")
    op.drop_table("visit_records")
    op.drop_index("ix_documents_status_doc_type", table_name="documents")
    op.drop_index("ix_documents_name", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_residents_name_address", table_name="residents")
    op.drop_table("residents")
