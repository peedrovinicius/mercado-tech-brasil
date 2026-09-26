from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_municipality_serving"
down_revision: str | None = "0001_serving_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fact_market_municipality",
        sa.Column("competence", sa.Date(), nullable=False),
        sa.Column("municipality_code", sa.String(length=8), nullable=False),
        sa.Column("admissions", sa.Integer(), nullable=False),
        sa.Column("dismissals", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("salary_mean_admissions", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_median_admissions", sa.Numeric(14, 2), nullable=True),
        sa.ForeignKeyConstraint(
            ["competence"],
            ["dataset_release.competence"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("competence", "municipality_code"),
        sa.CheckConstraint(
            "admissions >= 0",
            name="ck_market_municipality_admissions_nonnegative",
        ),
        sa.CheckConstraint(
            "dismissals >= 0",
            name="ck_market_municipality_dismissals_nonnegative",
        ),
    )
    op.create_index(
        "idx_market_municipality_admissions",
        "fact_market_municipality",
        ["competence", "admissions"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_market_municipality_admissions",
        table_name="fact_market_municipality",
    )
    op.drop_table("fact_market_municipality")
