# Human Interventions

## Purpose

This file lists every action that must be performed by the user before blocked tickets can proceed.

Agents must not bypass these actions.

## Status Values

Allowed values:

1. `OPEN`
2. `WAITING_FOR_USER`
3. `USER_PROVIDED`
4. `VERIFIED`
5. `CLOSED`
6. `CANCELLED_WITH_REASON`

## Current Human Interventions

| ID | Related Ticket | Required User Action | Required Path or Decision | Why Required | Blocks | Verification | Status |
|---|---|---|---|---|---|---|---|
| H01 | T21, T22, T25 | Download Edge-IIoTset dataset from Ferrag et al. (2022) IEEE Access. | Place raw files in `data/raw/Edge-IIoTset/`. After download, inspect schema, client identifiers, timestamps, and feature modality. | Regime D external validation cannot be implemented without the dataset. Phase 0 GA-08 confirmed no Edge-IIoTset files exist anywhere in the repository. | T21 (preprocessing), T22 (training/evaluation), T25 (temporal probe). | Dataset files exist at `data/raw/Edge-IIoTset/`, pass schema audit, and produce a valid feasibility outcome. | `OPEN` |
| H02 | T23, T24, T25 | Provide raw CICIoT2023 CSV files (full dataset with all original columns). | Place raw CSV files in `data/raw/CIC_IOT_Dataset2023/CSV/`. Currently this directory contains only `README.pdf`. | Processed Parquet files contain only 39 feature columns — no MAC, device, group, or timestamp metadata. B-b feasibility audit requires inspecting raw CSVs for client identifier columns. | T23 (B-b metadata/partition), T24 (B-b training), T25 (temporal probe if CICIoT2023 has timestamps). | Raw CSV files exist at specified path, metadata audit completes, and one B-b feasibility outcome is assigned. | `OPEN` |

## Rules

If an item is `OPEN` or `WAITING_FOR_USER`, affected tickets must remain `BLOCKED_HUMAN`.

No agent may create fake substitutes, placeholder datasets, placeholder manifests, or success-shaped artifacts.

## Resolution Process

When the user provides the required data or decision:

1. The user confirms completion.
2. The relevant agent verifies the files/decision are valid.
3. Update the intervention status to `USER_PROVIDED`.
4. Run the verification check.
5. If verification passes, update to `VERIFIED` then `CLOSED`.
6. Update affected ticket statuses from `BLOCKED_HUMAN` to `NOT_STARTED`.
7. Update `ticket_progress.md` accordingly.