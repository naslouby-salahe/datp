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
| H01 | TBD | Download and place Edge-IIoTset if Regime D is required. | Path to be defined by ticket planner after codebase inspection. | Regime D cannot be implemented or audited without the dataset. | Regime D tickets. | Dataset files exist and pass checksum/schema audit. | OPEN |
| H02 | TBD | Provide raw CICIoT2023 CSV files if B-b metadata audit is required. | Path to be defined by ticket planner after codebase inspection. | Processed files do not contain MAC/device/group metadata. | CICIoT2023 B-b tickets. | Raw files exist and metadata audit passes or rejects B-b. | OPEN |

## Rules

If an item is `OPEN` or `WAITING_FOR_USER`, affected tickets must remain `BLOCKED_HUMAN`.

No agent may create fake substitutes, placeholder datasets, placeholder manifests, or success-shaped artifacts.