"""Synthetic, offline tests for the strict historical rehydration gate."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.rehydrate_caged_history import (
    _compare_overview_metrics,
    _compare_published_artifacts,
    _expected_manifests,
    _verify_extracted,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _create_manifests(root: Path, approval: Path) -> dict[str, str]:
    hashes = {}
    for kind in ("MOV", "FOR", "EXC"):
        digest = hashlib.sha256(kind.encode()).hexdigest()
        hashes[kind] = digest
        _write_json(
            root / "202608" / "extracted" / f"CAGED{kind}202608.txt.manifest.json",
            {
                "competence": "202608",
                "source": "novo_caged_mte",
                "transport": "ftp_mte",
                "source_url": (
                    "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/"
                    f"2026/202608/CAGED{kind}202608.7z"
                ),
                "sha256": digest,
                "size_bytes": 3,
            },
        )
    _write_json(
        approval,
        {"202608": {"approved": True, "source_sha256": hashes["MOV"]}},
    )
    return hashes


def test_manifest_requires_original_approved_sha_and_official_transport(
    tmp_path: Path,
) -> None:
    bronze = tmp_path / "bronze"
    approval = tmp_path / "approvals.json"
    hashes = _create_manifests(bronze, approval)
    expected = _expected_manifests(
        "202608", bronze_root=bronze, approvals_path=approval
    )
    assert expected["MOV"]["sha256"] == hashes["MOV"]

    path = bronze / "202608/extracted/CAGEDFOR202608.txt.manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["transport"] = "https_huggingface_mirror"
    _write_json(path, payload)
    with pytest.raises(ValueError, match="Manifesto oficial inválido"):
        _expected_manifests("202608", bronze_root=bronze, approvals_path=approval)


def test_unapproved_original_hash_must_fail(tmp_path: Path) -> None:
    bronze = tmp_path / "bronze"
    approval = tmp_path / "approvals.json"
    _create_manifests(bronze, approval)
    _write_json(approval, {"202608": {"approved": True, "source_sha256": "f" * 64}})
    with pytest.raises(ValueError, match="difere da aprovação"):
        _expected_manifests("202608", bronze_root=bronze, approvals_path=approval)


def test_extracted_file_must_match_original_size_and_sha(tmp_path: Path) -> None:
    source = tmp_path / "CAGEDMOV202608.txt"
    source.write_bytes(b"MOV")
    expected = {
        "size_bytes": 3,
        "sha256": hashlib.sha256(b"MOV").hexdigest(),
    }
    assert _verify_extracted(
        "202608", kind="MOV", extracted_dir=tmp_path, original=expected
    ) == source

    source.write_bytes(b"BAD")
    with pytest.raises(ValueError, match="SHA-256 divergente"):
        _verify_extracted(
            "202608", kind="MOV", extracted_dir=tmp_path, original=expected
        )


def test_baseline_diff_is_blocking_even_if_file_exists(tmp_path: Path) -> None:
    gold = tmp_path / "gold"
    gold.mkdir()
    target = gold / "overview-202608.json"
    target.write_bytes(b"old")
    original = hashlib.sha256(b"old").hexdigest()
    baseline = {
        "artifacts": {"202608": {"overview-202608.json": original}}
    }
    assert _compare_published_artifacts(baseline, gold) == []

    target.write_bytes(b"changed")
    result = _compare_published_artifacts(baseline, gold)
    assert len(result) == 1
    assert result[0]["competence"] == "202608"
    assert result[0]["before_sha256"] == original
    assert result[0]["after_sha256"] != original


def test_baseline_path_traversal_is_rejected(tmp_path: Path) -> None:
    baseline = {"artifacts": {"202608": {"../secret.txt": "invalid"}}}
    with pytest.raises(ValueError, match="Caminho inválido"):
        _compare_published_artifacts(baseline, tmp_path)


def test_metric_diagnostics_distinguish_numeric_changes(tmp_path: Path) -> None:
    gold = tmp_path / "gold"
    gold.mkdir()
    original = {
        "overview_metrics": {
            "202607": {
                "admissions": 100,
                "dismissals": 85,
                "balance": 15,
                "salary_median_admissions_real": 3000.0,
            }
        }
    }
    _write_json(
        gold / "overview-202607.json",
        {
            "admissions": 100,
            "dismissals": 85,
            "balance": 15,
            "salary_median_admissions_real": 3000.0,
        },
    )
    assert _compare_overview_metrics(original, gold) == []

    _write_json(
        gold / "overview-202607.json",
        {
            "admissions": 101,
            "dismissals": 85,
            "balance": 16,
            "salary_median_admissions_real": 3000.0,
        },
    )
    changes = _compare_overview_metrics(original, gold)
    assert len(changes) == 1
    assert changes[0]["competence"] == "202607"
    assert changes[0]["changed_metrics"]["balance"] == {
        "published": 15,
        "reconstructed": 16,
    }


def test_missing_overview_blocks_comparison(tmp_path: Path) -> None:
    original = {"overview_metrics": {"202608": {"balance": 10}}}
    changes = _compare_overview_metrics(original, tmp_path)
    assert changes == [
        {"competence": "202608", "error": "overview reconstruído ausente"}
    ]
