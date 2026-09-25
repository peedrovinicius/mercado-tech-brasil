from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("APP_ENV", "development")
    project_name: str = "Mercado Tech Brasil"
    version: str = "0.6.0"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://mercado_tech:mercado_tech_dev@localhost:5432/mercado_tech",
    )
    sources_path: Path = ROOT / "config" / "sources.json"
    cbo_config_path: Path = ROOT / "config" / "cbo_tech.yml"
    bronze_path: Path = ROOT / "data" / "bronze"
    silver_path: Path = ROOT / "data" / "silver"
    gold_path: Path = ROOT / "data" / "gold"


settings = Settings()
