from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_municipality_population"
down_revision: str | None = "0003_real_salary"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "fact_market_municipality",
        sa.Column("population_estimate", sa.Integer(), nullable=True),
    )
    op.add_column(
        "fact_market_municipality",
        sa.Column("population_reference_year", sa.Integer(), nullable=True),
    )
    for column in (
        "admissions_per_100k",
        "dismissals_per_100k",
        "balance_per_100k",
    ):
        op.add_column(
            "fact_market_municipality",
            sa.Column(column, sa.Numeric(14, 4), nullable=True),
        )


def downgrade() -> None:
    for column in (
        "balance_per_100k",
        "dismissals_per_100k",
        "admissions_per_100k",
        "population_reference_year",
        "population_estimate",
    ):
        op.drop_column("fact_market_municipality", column)
