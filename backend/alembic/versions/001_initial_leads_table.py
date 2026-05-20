"""Initial leads table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE leadstatus AS ENUM ('new', 'analyzing', 'analyzed', 'scored', 'personalized', 'contacted', 'converted', 'rejected');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE websitequality AS ENUM ('none', 'poor', 'average', 'good', 'excellent');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("has_website", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("instagram", sa.String(255), nullable=True),
        sa.Column("facebook", sa.String(255), nullable=True),
        sa.Column("google_maps_url", sa.String(1000), nullable=True),
        sa.Column("place_id", sa.String(255), nullable=True),
        sa.Column("rating", sa.Numeric(3, 1), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("status", sa.Enum("new", "analyzing", "analyzed", "scored", "personalized", "contacted", "converted", "rejected", name="leadstatus", create_type=False), nullable=False, server_default="new"),
        sa.Column("ai_score", sa.Integer(), nullable=True),
        sa.Column("score_breakdown", sa.Text(), nullable=True),
        sa.Column("website_quality", sa.Enum("none", "poor", "average", "good", "excellent", name="websitequality", create_type=False), nullable=True),
        sa.Column("website_quality_score", sa.Integer(), nullable=True),
        sa.Column("website_title", sa.String(500), nullable=True),
        sa.Column("has_contact_form", sa.Boolean(), nullable=True),
        sa.Column("has_gallery", sa.Boolean(), nullable=True),
        sa.Column("is_mobile_responsive", sa.Boolean(), nullable=True),
        sa.Column("has_modern_ui", sa.Boolean(), nullable=True),
        sa.Column("website_analysis_summary", sa.Text(), nullable=True),
        sa.Column("outreach_email", sa.Text(), nullable=True),
        sa.Column("outreach_whatsapp", sa.Text(), nullable=True),
        sa.Column("outreach_dm", sa.Text(), nullable=True),
        sa.Column("outreach_message", sa.Text(), nullable=True),
        sa.Column("source_keyword", sa.String(255), nullable=True),
        sa.Column("source_latitude", sa.Float(), nullable=True),
        sa.Column("source_longitude", sa.Float(), nullable=True),
        sa.Column("source_radius", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("personalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("place_id"),
    )
    op.create_index("ix_leads_id", "leads", ["id"])
    op.create_index("ix_leads_business_name", "leads", ["business_name"])
    op.create_index("ix_leads_category", "leads", ["category"])
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index("ix_leads_ai_score", "leads", ["ai_score"])
    op.create_index("ix_leads_created_at", "leads", ["created_at"])
    op.create_index("ix_leads_category_status", "leads", ["category", "status"])


def downgrade() -> None:
    op.drop_table("leads")
    op.execute("DROP TYPE IF EXISTS leadstatus")
    op.execute("DROP TYPE IF EXISTS websitequality")
