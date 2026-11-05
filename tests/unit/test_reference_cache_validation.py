import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.reference.cache_validation import (
    verify_audit_references,
    verify_ipca_snapshot,
    verify_population_snapshot,
)


def test_versioned_official_ibge_caches_are_eligible() -> None:
    assert verify_population_snapshot(
        Path("data/reference/population.json"), 2026
    ) == 5571
    assert verify_ipca_snapshot(
        Path("data/reference/ipca.json"),
        competence="202609",
        base_competence="202607",
    ) == Decimal("7695.8200000000000")


def test_reject_population_with_wrong_year(tmp_path: Path) -> None:
    source = json.loads(
        Path("data/reference/population.json").read_text(encoding="utf-8")
    )
    source["reference_year"] = 2025
    path = tmp_path / "population.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="corresponde"):
        verify_population_snapshot(path, 2026)


def test_reject_ipca_with_missing_or_changed_month(
    tmp_path: Path,
) -> None:
    source = json.loads(
        Path("data/reference/ipca.json").read_text(encoding="utf-8")
    )
    source["indices"]["202609"] = "7696.30"
    path = tmp_path / "ipca.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="mudou"):
        verify_ipca_snapshot(
            path,
            competence="202609",
            base_competence="202607",
        )


def test_all_audit_references_validate() -> None:
    verify_audit_references(
        population_path=Path("data/reference/population.json"),
        ipca_path=Path("data/reference/ipca.json"),
        competence="202609",
        base_competence="202607",
    )
