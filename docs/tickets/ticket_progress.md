# Ticket Progress

## Purpose

This file tracks what is done, what is missing, what is blocked, and what must happen next.

Before starting any ticket, the executing agent must check this file and verify previous-ticket completion.

## Current Rule

Before starting ticket `TXX`, check every previous ticket.

If any previous ticket is incomplete and not correctly blocked or skipped with reason, return to that ticket first.

## Current Status Summary

| Field | Value |
|---|---|
| Total tickets | 28 |
| Current ticket | None |
| Last completed ticket | None |
| NOT_STARTED tickets | T01–T23, T25, T26–T28 (27 tickets) |
| BLOCKED_HUMAN tickets | None (H01 and H02 both CLOSED) |
| SKIPPED_WITH_REASON tickets | T24 (CICIoT2023 B-b is infeasible on the currently available CSV artifact; T23 will write the rejection manifest) |
| Technical-blocked tickets | None |
| Scientific-blocked tickets | None |
| Next recommended action | Start T01 (Data Root Resolution) |

## Progress Log

| Entry | Ticket | Old Status | New Status | Reason | Next Action |
|---|---|---|---|---|---|
| 001 | N/A | N/A | N/A | Ticket system initialized. | Run ticket generation. |
| 002 | ALL | N/A | NOT_STARTED / BLOCKED_HUMAN | Ticket generation complete (28 tickets). 5 blocked on human interventions. | Start T01. |
| 003 | H01 | OPEN | CLOSED | Edge-IIoTset downloaded from Kaggle (`mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot`, 11 GB, 26 CSVs + matching PCAPs + 2 selected ML/DL aggregates) to `data/raw/Edge-IIoTset/`. Schema audit (63 columns): `frame.time` timestamps populated; `ip.src_host`/`ip.dst_host` client identifiers populated; `Attack_label`/`Attack_type` labels populated; protocol fields TCP/UDP/HTTP/DNS/MQTT/Modbus/ARP/ICMP present. T21/T22/T25(Edge-IIoTset) FEASIBLE. | Proceed with T01 → T21. |
| 004 | H02 | OPEN | CLOSED | Existing CICIoT2023 raw CSVs verified in-place (inspection only, no files modified). Found 372 per-attack CSVs across 35 class folders in `data/raw/CIC_IOT_Dataset2023/CSV/CSV/` + 63 merged CSVs in `data/raw/CIC_IOT_Dataset2023/CSV/MERGED_CSV/` (17 GB total). Schema audit: 39 numeric features + `Label` (merged only). **No** MAC, device, IP, capture-source, or timestamp columns. B-b INFEASIBLE; temporal probe on CICIoT2023 INFEASIBLE. | T23 to formally assign `B_B_REJECTED_NO_METADATA`; T24 to be `SKIPPED_WITH_REASON` after T23 executes. |
| 005 | T21 | BLOCKED_HUMAN | NOT_STARTED | H01 CLOSED. Edge-IIoTset raw files available with verified schema for preprocessing. | Schedule after T01 completes. |
| 006 | T22 | BLOCKED_HUMAN | NOT_STARTED | H01 CLOSED. Dependency reduced to T21 (ticket dependency, not human). | Schedule after T21 completes. |
| 007 | T23 | BLOCKED_HUMAN | NOT_STARTED | H02 CLOSED. Ticket implements `B_B_REJECTED_NO_METADATA` formally: defines the outcome enum, records schema evidence, writes the rejection manifest, and adds the downstream B-b training guard. No partition is built. | Execute after T01 to formalize the rejection enum, manifest, and guard. |
| 008 | T24 | BLOCKED_HUMAN | SKIPPED_WITH_REASON | CICIoT2023 B-b training/evaluation skipped because the verified raw CSV schema contains no MAC, device ID, client ID, capture-source identifier, source/destination IP, or other usable client partition metadata. H02 is closed; the branch is rejected by feasibility audit, not blocked by missing user action. CICIoT2023 B-b is infeasible on the currently available CSV artifact. No CICIoT2023 PCAP branch added now. | None — ticket is terminal. CICIoT2023 reported under Regime B-a only. |
| 009 | T25 | BLOCKED_HUMAN | NOT_STARTED | H01 + H02 CLOSED. Edge-IIoTset path FEASIBLE (`frame.time` timestamps populated); CICIoT2023 path rejected with `TEMPORAL_REJECTED_NO_TIMESTAMPS`. Ticket proceeds on Edge-IIoTset only. | Schedule after T21 completes. |

## Previous-Ticket Check Log

| Entry | Requested Ticket | Previous Tickets Checked | Result | Action Taken |
|---|---|---|---|---|
| 001 | N/A | N/A | N/A | N/A |