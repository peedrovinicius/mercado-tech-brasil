from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    environment: str = os.getenv("APP_ENV", "development")
    project_name: str = "Mercado Tech Brasil"
    version: str = "0.7.0"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://mercado_tech:mercado_tech_dev@localhost:5432/mercado_tech",
    )
    sources_path: Path = ROOT / "config" / "sources.json"
    cbo_config_path: Path = ROOT / "config" / "cbo_tech.yml"
    reference_totals_path: Path = ROOT / "config" / "reference_totals.json"
    publication_approvals_path: Path = ROOT / "config" / "publication_approvals.json"
    bronze_path: Path = ROOT / "data" / "bronze"
    silver_path: Path = ROOT / "data" / "silver"
    gold_path: Path = ROOT / "data" / "gold"


settings = Settings()
