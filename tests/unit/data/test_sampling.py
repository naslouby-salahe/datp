from __future__ import annotations

import numpy as np
import polars as pl

from datp.data.sampling import (
    _allocate_attack_counts,
    _sample_attack_rows,
    _sample_benign_rows,
    apply_ciciot_cap,
)

LABEL = "Label"
BENIGN = "BENIGN"


def _make_df(
    n_benign: int,
    n_attack: int,
    *,
    attack_labels: list[str] | None = None,
    seed: int = 42,
) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[pl.DataFrame] = []

    if n_benign > 0:
        benign = pl.DataFrame(
            {f"f{i}": rng.standard_normal(n_benign) for i in range(2)}
        )
        benign = benign.with_columns(pl.lit(BENIGN).alias(LABEL))
        rows.append(benign)

    if n_attack > 0 and attack_labels:
        per = max(1, n_attack // len(attack_labels))
        for i, lbl in enumerate(attack_labels):
            n = per if i < len(attack_labels) - 1 else n_attack - per * i
            n = max(n, 0)
            if n == 0:
                continue
            atk = pl.DataFrame(
                {f"f{j}": rng.standard_normal(n) for j in range(2)}
            )
            atk = atk.with_columns(pl.lit(lbl).alias(LABEL))
            rows.append(atk)

    return pl.concat(rows) if rows else pl.DataFrame(schema={"f0": pl.Float64, "f1": pl.Float64, LABEL: pl.Utf8})


# ── _sample_benign_rows ──────────────────────────────────────────────


class TestSampleBenignRows:
    def test_returns_all_when_budget_exceeds_count(self):
        df = _make_df(100, 0)
        result = _sample_benign_rows(df, benign_budget=200, seed=1)
        assert len(result) == 100

    def test_samples_exact_budget(self):
        df = _make_df(1000, 0)
        result = _sample_benign_rows(df, benign_budget=50, seed=1)
        assert len(result) == 50

    def test_deterministic_with_seed(self):
        df = _make_df(1000, 0)
        a = _sample_benign_rows(df, benign_budget=50, seed=42)
        b = _sample_benign_rows(df, benign_budget=50, seed=42)
        assert a.equals(b)

    def test_zero_budget_returns_empty(self):
        df = _make_df(100, 0)
        result = _sample_benign_rows(df, benign_budget=0, seed=1)
        # len(df)=100 <= 0 is False, so it samples 0 rows
        assert len(result) == 0


# ── _allocate_attack_counts ───────────────────────────────────────────


class TestAllocateAttackCounts:
    def test_proportional_equal_categories(self):
        rng = np.random.default_rng(0)
        atk_a = pl.DataFrame({"f0": rng.standard_normal(5000), "f1": rng.standard_normal(5000)})
        atk_a = atk_a.with_columns(pl.lit("A").alias(LABEL))
        atk_b = pl.DataFrame({"f0": rng.standard_normal(5000), "f1": rng.standard_normal(5000)})
        atk_b = atk_b.with_columns(pl.lit("B").alias(LABEL))
        attack_df = pl.concat([atk_a, atk_b])

        alloc = _allocate_attack_counts(attack_df, attack_budget=2000, label_column=LABEL)
        assert alloc == {"A": 1000, "B": 1000}

    def test_proportional_unequal_categories(self):
        rng = np.random.default_rng(0)
        atk_a = pl.DataFrame({"f0": rng.standard_normal(7000), "f1": rng.standard_normal(7000)})
        atk_a = atk_a.with_columns(pl.lit("A").alias(LABEL))
        atk_b = pl.DataFrame({"f0": rng.standard_normal(3000), "f1": rng.standard_normal(3000)})
        atk_b = atk_b.with_columns(pl.lit("B").alias(LABEL))
        attack_df = pl.concat([atk_a, atk_b])

        alloc = _allocate_attack_counts(attack_df, attack_budget=1000, label_column=LABEL)
        # 700 exact A, 300 exact B → floor sums to 1000, no remainder
        assert alloc["A"] == 700
        assert alloc["B"] == 300

    def test_remainder_assignment(self):
        """When floors sum < budget, remainder goes to categories with largest fractional part."""
        rng = np.random.default_rng(0)
        parts = []
        # 3 categories with 3333 each = 9999 total, budget=1000
        # exact: 333.3 each → floor 333, sum=999, remainder=1 → category with highest fractional gets +1
        for label in ("A", "B", "C"):
            df = pl.DataFrame({"f0": rng.standard_normal(3333), "f1": rng.standard_normal(3333)})
            df = df.with_columns(pl.lit(label).alias(LABEL))
            parts.append(df)
        attack_df = pl.concat(parts)

        alloc = _allocate_attack_counts(attack_df, attack_budget=1000, label_column=LABEL)
        assert sum(alloc.values()) == 1000
        # Each gets floor=333, one gets +1 → two with 333, one with 334
        assert sorted(alloc.values()) == [333, 333, 334]

    def test_single_category(self):
        rng = np.random.default_rng(0)
        attack_df = pl.DataFrame({"f0": rng.standard_normal(500), "f1": rng.standard_normal(500)})
        attack_df = attack_df.with_columns(pl.lit("Only").alias(LABEL))

        alloc = _allocate_attack_counts(attack_df, attack_budget=100, label_column=LABEL)
        assert alloc == {"Only": 100}


# ── _sample_attack_rows ───────────────────────────────────────────────


class TestSampleAttackRows:
    def test_returns_all_when_attack_leq_budget(self):
        attack_df = _make_df(0, 50, attack_labels=["A", "B"]).filter(pl.col(LABEL) != BENIGN)
        result = _sample_attack_rows(attack_df, attack_budget=100, label_column=LABEL, seed=1)
        assert len(result) == 50

    def test_zero_budget_returns_empty(self):
        attack_df = _make_df(0, 100, attack_labels=["A"]).filter(pl.col(LABEL) != BENIGN)
        result = _sample_attack_rows(attack_df, attack_budget=0, label_column=LABEL, seed=1)
        assert len(result) == 0

    def test_samples_proportionally(self):
        df = _make_df(0, 20000, attack_labels=["A", "B"])
        attack_df = df.filter(pl.col(LABEL) != BENIGN)
        result = _sample_attack_rows(attack_df, attack_budget=10000, label_column=LABEL, seed=1)
        assert len(result) == 10000
        counts = result.group_by(LABEL).len()
        assert dict(zip(counts[LABEL].to_list(), counts["len"].to_list())) == {"A": 5000, "B": 5000}

    def test_deterministic_with_seed(self):
        attack_df = _make_df(0, 20000, attack_labels=["A", "B"]).filter(pl.col(LABEL) != BENIGN)
        a = _sample_attack_rows(attack_df, attack_budget=5000, label_column=LABEL, seed=42)
        b = _sample_attack_rows(attack_df, attack_budget=5000, label_column=LABEL, seed=42)
        assert a.equals(b)


# ── apply_ciciot_cap ──────────────────────────────────────────────────


class TestApplyCiciotCap:
    def test_priority_order_equal_categories(self):
        """80k benign + 20k attack (2×10k). Cap=50k, reserve=0.2 → attack=10k, benign=40k."""
        df = _make_df(80_000, 20_000, attack_labels=["DDoS_A", "DDoS_B"])
        result = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                                   attack_reserve_fraction=0.2, seed=42)
        assert len(result) == 50_000
        attack = result.filter(pl.col(LABEL) != BENIGN)
        benign = result.filter(pl.col(LABEL) == BENIGN)
        assert len(attack) == 10_000
        assert len(benign) == 40_000
        cat_counts = attack.group_by(LABEL).len()
        counts = dict(zip(cat_counts[LABEL].to_list(), cat_counts["len"].to_list()))
        assert counts == {"DDoS_A": 5000, "DDoS_B": 5000}

    def test_fewer_attack_than_budget(self):
        """3k attack < 10k reserve → all attack kept, benign fills remaining."""
        df = _make_df(80_000, 3_000, attack_labels=["Recon"])
        result = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                                   attack_reserve_fraction=0.2, seed=42)
        assert len(result) == 50_000
        assert result.filter(pl.col(LABEL) == "Recon").height == 3_000
        assert result.filter(pl.col(LABEL) == BENIGN).height == 47_000

    def test_no_cap_needed_benign_only(self):
        df = _make_df(100, 0)
        result = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                                   attack_reserve_fraction=0.2, seed=42)
        assert len(result) == 100

    def test_total_leq_cap_but_attack_exceeds_reserve(self):
        """10k benign + 20k attack = 30k ≤ 50k cap, but attack limited to reserve=10k."""
        df = _make_df(10_000, 20_000, attack_labels=["DDoS_A"])
        result = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                                   attack_reserve_fraction=0.2, seed=42)
        assert result.filter(pl.col(LABEL) != BENIGN).height == 10_000
        assert result.filter(pl.col(LABEL) == BENIGN).height == 10_000

    def test_zero_attack_original(self):
        df = _make_df(500, 0)
        result = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                                   attack_reserve_fraction=0.2, seed=42)
        assert len(result) == 500
        assert result.filter(pl.col(LABEL) != BENIGN).height == 0

    def test_deterministic(self):
        df = _make_df(80_000, 20_000, attack_labels=["A", "B"])
        a = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                              attack_reserve_fraction=0.2, seed=42)
        b = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                              attack_reserve_fraction=0.2, seed=42)
        # Row order may differ across group iterations; sort for deterministic comparison.
        sort_cols = [c for c in a.columns if c in b.columns]
        a_sorted = a.sort(sort_cols)
        b_sorted = b.sort(sort_cols)
        assert a_sorted.equals(b_sorted)

    def test_attack_only_no_benign(self):
        """Edge case: df has only attack rows, no benign."""
        rng = np.random.default_rng(0)
        df = pl.DataFrame({"f0": rng.standard_normal(500), "f1": rng.standard_normal(500)})
        df = df.with_columns(pl.lit("A").alias(LABEL))
        result = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                                   attack_reserve_fraction=0.2, seed=42)
        # attack budget = min(500, 10000) = 500, benign budget = 50000 - 500 = 49500
        # but benign df is empty → benign sample returns empty
        assert len(result) == 500

    def test_empty_dataframe(self):
        df = pl.DataFrame(schema={"f0": pl.Float64, "f1": pl.Float64, LABEL: pl.Utf8})
        result = apply_ciciot_cap(df, cap=50_000, label_column=LABEL, benign_label=BENIGN,
                                   attack_reserve_fraction=0.2, seed=42)
        assert len(result) == 0
