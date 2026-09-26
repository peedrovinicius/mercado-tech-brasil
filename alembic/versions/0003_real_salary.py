from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_real_salary"
down_revision: str | None = "0002_municipality_serving"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dataset_release",
        sa.Column("salary_mean_admissions_real", sa.Numeric(14, 2)),
    )
    op.add_column(
        "dataset_release",
        sa.Column("salary_median_admissions_real", sa.Numeric(14, 2)),
    )
    op.add_column(
        "dataset_release",
        sa.Column("salary_real_base_competence", sa.String(length=6)),
    )

    for table in (
        "fact_market_uf",
        "fact_market_occupation",
    ):
        op.add_column(
            table,
            sa.Column("salary_mean_admissions", sa.Numeric(14, 2)),
        )

    for table in (
        "fact_market_uf",
        "fact_market_occupation",
        "fact_market_municipality",
    ):
        op.add_column(
            table,
            sa.Column("salary_mean_admissions_real", sa.Numeric(14, 2)),
        )
        op.add_column(
            table,
            sa.Column("salary_median_admissions_real", sa.Numeric(14, 2)),
        )


def downgrade() -> None:
    for table in (
        "fact_market_municipality",
        "fact_market_occupation",
        "fact_market_uf",
    ):
        op.drop_column(table, "salary_median_admissions_real")
        op.drop_column(table, "salary_mean_admissions_real")

    for table in (
        "fact_market_occupation",
        "fact_market_uf",
    ):
        op.drop_column(table, "salary_mean_admissions")

    op.drop_column("dataset_release", "salary_real_base_competence")
    op.drop_column("dataset_release", "salary_median_admissions_real")
    op.drop_column("dataset_release", "salary_mean_admissions_real")
