"""Initial leads table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

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
    op.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            business_name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            address VARCHAR(500),
            phone VARCHAR(50),
            email VARCHAR(255),
            website VARCHAR(500),
            has_website BOOLEAN NOT NULL DEFAULT false,
            instagram VARCHAR(255),
            facebook VARCHAR(255),
            google_maps_url VARCHAR(1000),
            place_id VARCHAR(255) UNIQUE,
            rating NUMERIC(3, 1),
            reviews_count INTEGER,
            latitude FLOAT,
            longitude FLOAT,
            status leadstatus NOT NULL DEFAULT 'new',
            ai_score INTEGER,
            score_breakdown TEXT,
            website_quality websitequality,
            website_quality_score INTEGER,
            website_title VARCHAR(500),
            has_contact_form BOOLEAN,
            has_gallery BOOLEAN,
            is_mobile_responsive BOOLEAN,
            has_modern_ui BOOLEAN,
            website_analysis_summary TEXT,
            outreach_email TEXT,
            outreach_whatsapp TEXT,
            outreach_dm TEXT,
            outreach_message TEXT,
            source_keyword VARCHAR(255),
            source_latitude FLOAT,
            source_longitude FLOAT,
            source_radius INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            analyzed_at TIMESTAMPTZ,
            scored_at TIMESTAMPTZ,
            personalized_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_id ON leads (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_business_name ON leads (business_name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_category ON leads (category)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_status ON leads (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_ai_score ON leads (ai_score)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_created_at ON leads (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_category_status ON leads (category, status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS leads")
    op.execute("DROP TYPE IF EXISTS leadstatus")
    op.execute("DROP TYPE IF EXISTS websitequality")
