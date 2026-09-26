from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
)

metadata = MetaData()

dataset_release = Table(
    "dataset_release",
    metadata,
    Column("competence", Date, primary_key=True),
    Column("source", String(80), nullable=False),
    Column("source_sha256", String(64), nullable=False),
    Column("publishable", Boolean, nullable=False),
    Column("admissions", Integer, nullable=False),
    Column("dismissals", Integer, nullable=False),
    Column("balance", Integer, nullable=False),
    Column("records_tech", Integer, nullable=False),
    Column("salary_mean_admissions", Numeric(14, 2)),
    Column("salary_median_admissions", Numeric(14, 2)),
    Column("salary_mean_admissions_real", Numeric(14, 2)),
    Column("salary_median_admissions_real", Numeric(14, 2)),
    Column("salary_real_base_competence", String(6)),
    Column("valid_rate", Numeric(8, 6), nullable=False),
    Column("loaded_at_utc", DateTime(timezone=True), nullable=False),
    CheckConstraint("admissions >= 0", name="ck_release_admissions_nonnegative"),
    CheckConstraint("dismissals >= 0", name="ck_release_dismissals_nonnegative"),
    CheckConstraint("records_tech >= 0", name="ck_release_records_nonnegative"),
)

market_uf = Table(
    "fact_market_uf",
    metadata,
    Column(
        "competence",
        Date,
        ForeignKey("dataset_release.competence", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("uf", String(2), primary_key=True),
    Column("admissions", Integer, nullable=False),
    Column("dismissals", Integer, nullable=False),
    Column("balance", Integer, nullable=False),
    Column("salary_mean_admissions", Numeric(14, 2)),
    Column("salary_median_admissions", Numeric(14, 2)),
    Column("salary_mean_admissions_real", Numeric(14, 2)),
    Column("salary_median_admissions_real", Numeric(14, 2)),
    CheckConstraint("admissions >= 0", name="ck_market_uf_admissions_nonnegative"),
    CheckConstraint("dismissals >= 0", name="ck_market_uf_dismissals_nonnegative"),
)

market_municipality = Table(
    "fact_market_municipality",
    metadata,
    Column(
        "competence",
        Date,
        ForeignKey("dataset_release.competence", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("municipality_code", String(8), primary_key=True),
    Column("municipality_ibge_code", String(7)),
    Column("municipality_name", String(160)),
    Column("uf", String(2)),
    Column("admissions", Integer, nullable=False),
    Column("dismissals", Integer, nullable=False),
    Column("balance", Integer, nullable=False),
    Column("salary_mean_admissions", Numeric(14, 2)),
    Column("salary_median_admissions", Numeric(14, 2)),
    Column("salary_mean_admissions_real", Numeric(14, 2)),
    Column("salary_median_admissions_real", Numeric(14, 2)),
    CheckConstraint(
        "admissions >= 0",
        name="ck_market_municipality_admissions_nonnegative",
    ),
    CheckConstraint(
        "dismissals >= 0",
        name="ck_market_municipality_dismissals_nonnegative",
    ),
)

market_occupation = Table(
    "fact_market_occupation",
    metadata,
    Column(
        "competence",
        Date,
        ForeignKey("dataset_release.competence", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("cbo_family", String(4), primary_key=True),
    Column("cbo_code", String(10), primary_key=True),
    Column("admissions", Integer, nullable=False),
    Column("dismissals", Integer, nullable=False),
    Column("balance", Integer, nullable=False),
    Column("salary_mean_admissions", Numeric(14, 2)),
    Column("salary_median_admissions", Numeric(14, 2)),
    Column("salary_mean_admissions_real", Numeric(14, 2)),
    Column("salary_median_admissions_real", Numeric(14, 2)),
    CheckConstraint(
        "admissions >= 0",
        name="ck_market_occupation_admissions_nonnegative",
    ),
    CheckConstraint(
        "dismissals >= 0",
        name="ck_market_occupation_dismissals_nonnegative",
    ),
)
