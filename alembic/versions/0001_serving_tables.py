from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_serving_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dataset_release",
        sa.Column("competence", sa.Date(), primary_key=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("publishable", sa.Boolean(), nullable=False),
        sa.Column("admissions", sa.Integer(), nullable=False),
        sa.Column("dismissals", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("records_tech", sa.Integer(), nullable=False),
        sa.Column("salary_mean_admissions", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_median_admissions", sa.Numeric(14, 2), nullable=True),
        sa.Column("valid_rate", sa.Numeric(8, 6), nullable=False),
        sa.Column("loaded_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "admissions >= 0",
            name="ck_release_admissions_nonnegative",
        ),
        sa.CheckConstraint(
            "dismissals >= 0",
            name="ck_release_dismissals_nonnegative",
        ),
        sa.CheckConstraint(
            "records_tech >= 0",
            name="ck_release_records_nonnegative",
        ),
    )
    op.create_table(
        "fact_market_uf",
        sa.Column("competence", sa.Date(), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("admissions", sa.Integer(), nullable=False),
        sa.Column("dismissals", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("salary_median_admissions", sa.Numeric(14, 2), nullable=True),
        sa.ForeignKeyConstraint(
            ["competence"],
            ["dataset_release.competence"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("competence", "uf"),
        sa.CheckConstraint(
            "admissions >= 0",
            name="ck_market_uf_admissions_nonnegative",
        ),
        sa.CheckConstraint(
            "dismissals >= 0",
            name="ck_market_uf_dismissals_nonnegative",
        ),
    )
    op.create_table(
        "fact_market_occupation",
        sa.Column("competence", sa.Date(), nullable=False),
        sa.Column("cbo_family", sa.String(length=4), nullable=False),
        sa.Column("cbo_code", sa.String(length=10), nullable=False),
        sa.Column("admissions", sa.Integer(), nullable=False),
        sa.Column("dismissals", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("salary_median_admissions", sa.Numeric(14, 2), nullable=True),
        sa.ForeignKeyConstraint(
            ["competence"],
            ["dataset_release.competence"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("competence", "cbo_family", "cbo_code"),
        sa.CheckConstraint(
            "admissions >= 0",
            name="ck_market_occupation_admissions_nonnegative",
        ),
        sa.CheckConstraint(
            "dismissals >= 0",
            name="ck_market_occupation_dismissals_nonnegative",
        ),
    )
    op.create_index(
        "idx_market_uf_admissions",
        "fact_market_uf",
        ["competence", "admissions"],
    )
    op.create_index(
        "idx_market_occupation_admissions",
        "fact_market_occupation",
        ["competence", "admissions"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_market_occupation_admissions",
        table_name="fact_market_occupation",
    )
    op.drop_index("idx_market_uf_admissions", table_name="fact_market_uf")
    op.drop_table("fact_market_occupation")
    op.drop_table("fact_market_uf")
    op.drop_table("dataset_release")
