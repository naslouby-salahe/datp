from __future__ import annotations

from pathlib import Path

DOC_PATHS = [
    Path("README.md"),
    Path("COMMANDS.md"),
]


def _docs_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in DOC_PATHS if path.exists()
    )


def test_baseline_role_docs_are_current() -> None:
    text = _docs_text()
    required = [
        "B0 is a centralized reference",
        "B1 uses the simple arithmetic mean",
        "B3 is diagnostic",
        "taxonomy too coarse",
        "no-p95",
        "circularity risk",
        "cluster stability",
        "must not overclaim",
    ]
    missing = [snippet for snippet in required if snippet not in text]
    assert not missing, f"Missing baseline documentation snippets: {missing}"


def test_no_stale_regime_a_fixed_k_claim() -> None:
    text = _docs_text()
    assert "B4 K=3 for Regime A (fixed)" not in text
    assert "Regime A uses K=3 fixed" not in text
