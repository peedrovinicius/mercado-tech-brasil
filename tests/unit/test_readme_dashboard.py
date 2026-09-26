from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_readme_dashboard_generator_uses_published_gold(tmp_path: Path):
    generated = tmp_path / "readme-dashboard.svg"

    subprocess.run(
        [
            sys.executable,
            "scripts/generate_readme_dashboard.py",
            "--output",
            str(generated),
        ],
        check=True,
    )

    svg = generated.read_text(encoding="utf-8")
    committed = Path("assets/readme-dashboard.svg").read_text(encoding="utf-8")

    expected_metrics = (
        "134.209",
        "127.865",
        "+6.344",
        "+906",
        "10,13%",
        "2,71%",
        "26,76%",
    )

    for metric in expected_metrics:
        assert metric in svg
        assert metric in committed
