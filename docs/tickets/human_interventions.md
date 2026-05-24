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
| H01 | T21, T22, T25 | Download Edge-IIoTset dataset from Ferrag et al. (2022) IEEE Access. | Place raw files in `data/raw/Edge-IIoTset/`. After download, inspect schema, client identifiers, timestamps, and feature modality. | Regime D external validation cannot be implemented without the dataset. Phase 0 GA-08 confirmed no Edge-IIoTset files exist anywhere in the repository. | T21 (preprocessing), T22 (training/evaluation), T25 (temporal probe). | Dataset files exist at `data/raw/Edge-IIoTset/`, pass schema audit, and produce a valid feasibility outcome. | `CLOSED` |
| H02 | T23, T24, T25 | Provide raw CICIoT2023 CSV files (full dataset with all original columns). | Place raw CSV files in `data/raw/CIC_IOT_Dataset2023/CSV/`. Currently this directory contains only `README.pdf`. | Processed Parquet files contain only 39 feature columns — no MAC, device, group, or timestamp metadata. B-b feasibility audit requires inspecting raw CSVs for client identifier columns. | T23 (B-b metadata/partition), T24 (B-b training), T25 (temporal probe if CICIoT2023 has timestamps). | Raw CSV files exist at specified path, metadata audit completes, and one B-b feasibility outcome is assigned. | `CLOSED` |

## Resolution Records

### H01 — Edge-IIoTset (CLOSED on 2026-05-24)

- Source: Kaggle dataset `mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot` (CC-BY-NC-SA-4.0), downloaded via Kaggle CLI.
- Location on disk: `data/raw/Edge-IIoTset/`
- Size: 11 GB, 52 files (26 CSV + matching PCAPs + `Readme.txt` + dataset PDF).
- Structure:
  - `Edge-IIoTset dataset/Attack traffic/` — 14 attack CSV/PCAP pairs (DDoS_HTTP, DDoS_UDP, DDoS_ICMP, DDoS_TCP_SYN, MITM, Port_Scanning, OS_Fingerprinting, Vulnerability_scanner, Password, Backdoor, Ransomware, SQL_injection, Uploading, XSS).
  - `Edge-IIoTset dataset/Normal traffic/<sensor>/` — 10 normal-sensor CSV/PCAP pairs (Distance, Modbus, IR_Receiver, Flame_Sensor, Soil_Moisture, Sound_Sensor, Heart_Rate, Water_Level, phValue, Temperature_and_Humidity).
  - `Edge-IIoTset dataset/Selected dataset for ML and DL/` — `DNN-EdgeIIoT-dataset.csv` (~2.22M rows) and `ML-EdgeIIoT-dataset.csv` (~158k rows).
- Schema (raw attack/normal CSVs, 63 columns confirmed on `DDoS_HTTP_Flood_attack.csv` and `Temperature_and_Humidity.csv` — identical column lists):
  - Timestamp: `frame.time` — populated (e.g., `"... 2021 11:35:29.350784000"`).
  - Client / device identifiers: `ip.src_host`, `ip.dst_host` — populated with real IPs (e.g., `192.168.0.170`, `192.168.0.128`); ARP IPv4 fields also present.
  - Labels: `Attack_label`, `Attack_type` — `Attack_type` is constant per file (e.g., `DDoS_HTTP`), matches filename.
  - Application protocol fields: TCP, UDP, HTTP, DNS, MQTT, MBTCP (Modbus), ARP, ICMP.
- Feasibility outcomes:
  - T21 preprocessing: **FEASIBLE** (clean per-file schema; multiple client/device IPs visible).
  - T22 training / evaluation: **FEASIBLE**.
  - T25 temporal probe on Edge-IIoTset (Regime D): **FEASIBLE** — `frame.time` provides chronologically ordered timestamps.
- No artifacts were fabricated; only Kaggle-provided files are present.

### H02 — CICIoT2023 (CLOSED on 2026-05-24)

- Verification was inspection-only — no raw files were modified, moved, renamed, or reprocessed.
- Files were already present from a prior user-provided drop and were located under nested subdirectories.
- Location on disk: `data/raw/CIC_IOT_Dataset2023/CSV/`
  - `CSV/CSV/<attack-class>/*.csv` — 372 per-attack CSVs across 35 class folders (Benign_Final, 25 DDoS/DoS variants, Mirai-*, Recon-*, BrowserHijacking, BackdoorMalware, DictionaryBruteForce, DNS_Spoofing, MITM-ArpSpoofing, SqlInjection, CommandInjection, Uploading_Attack, VulnerabilityScan, XSS).
  - `CSV/MERGED_CSV/Merged{01..63}.csv` — 63 merged CSVs.
  - `CSV/README.pdf`, `CSV/CSV/README_CSV.pdf`.
- Total CSV size: 17 GB; representative files non-empty and readable (e.g., `Benign_Final/BenignTraffic.pcap.csv` ≈ 362k rows; `MERGED_CSV/Merged01.csv` ≈ 712k rows).
- Schema (identical across per-attack folder files and merged files except for the `Label` column):
  - 39 numeric flow features: `Header_Length`, `Protocol Type`, `Time_To_Live`, `Rate`, TCP flag counts (`fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`, `ack_count`, `syn_count`, `fin_count`, `rst_count`), L7/L4/L3 protocol indicators (`HTTP`, `HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IGMP`, `IPv`, `LLC`), packet-size stats (`Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`), `IAT`, `Number`, `Variance`.
  - `Label` column: present only in `MERGED_CSV/`; absent from per-attack folder files (folder name is the implicit label). Confirmed label values: `BENIGN`, `DDOS-*`, `DOS-*`, `MIRAI-*`, `RECON-*`, `DDOS-PSHACK_FLOOD`, etc.
- Absent columns (verified across both per-attack and merged samples):
  - **No MAC address column.**
  - **No device / client / capture-source identifier column.**
  - **No source/destination IP address column** (note: `Time_To_Live` is a per-packet TTL, not a host or flow identifier).
  - **No flow / packet timestamp column.**
- Feasibility outcomes (recorded from real schema, not fabricated):
  - **CICIoT2023 B-b is infeasible on the currently available CSV artifact.** This is a valid feasibility outcome from the H02 audit, not an unresolved human intervention. T23 formalizes the outcome as `B_B_REJECTED_NO_METADATA` and writes the rejection manifest. T24 is `SKIPPED_WITH_REASON` (CICIoT2023 will be reported under Regime B-a only).
  - CICIoT2023 temporal branch: **rejected with `TEMPORAL_REJECTED_NO_TIMESTAMPS`** — no timestamp column in raw schema. T25 covers the Edge-IIoTset temporal path only.
  - No CICIoT2023 PCAP branch is added now. Pseudo-clients from folders/merged-files/labels/row-chunks/filenames and pseudo-time from file order are explicitly prohibited.
  - No further user action is required for CICIoT2023.

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