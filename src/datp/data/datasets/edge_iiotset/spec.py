# SPDX-License-Identifier: Proprietary
"""Edge-IIoTset dataset spec (Regime D — conditional external validation).

63-column schema from Ferrag et al. (2022). Downloaded from Kaggle.
Metadata columns: frame.time, ip.src_host, ip.dst_host, Attack_label, Attack_type.
Client identity: ip.src_host — physical device clients.
"""

from __future__ import annotations

from datp.data.catalog import (
    ClientIdentity,
    DatasetID,
    DatasetSpec,
    RawLayout,
    SplitPolicy,
)

DATASET_ID = "edge_iiotset"
FEATURE_COUNT: int = 58
LABEL_COLUMN: str = "Attack_label"
ATTACK_TYPE_COLUMN: str = "Attack_type"
BENIGN_LABEL: str = "0"
TIMESTAMP_COLUMN: str = "frame.time"
CLIENT_ID_COLUMN: str = "ip.src_host"
DST_HOST_COLUMN: str = "ip.dst_host"

_METADATA_COLUMNS: tuple[str, ...] = (
    TIMESTAMP_COLUMN,
    CLIENT_ID_COLUMN,
    DST_HOST_COLUMN,
    LABEL_COLUMN,
    ATTACK_TYPE_COLUMN,
)

FEATURE_COLUMNS: tuple[str, ...] = (
    "arp.dst.proto_ipv4",
    "arp.opcode",
    "arp.hw.size",
    "arp.src.proto_ipv4",
    "icmp.checksum",
    "icmp.seq_le",
    "icmp.transmit_timestamp",
    "icmp.unused",
    "http.file_data",
    "http.content_length",
    "http.request.uri.query",
    "http.request.method",
    "http.referer",
    "http.request.full_uri",
    "http.request.version",
    "http.response",
    "http.tls_port",
    "tcp.ack",
    "tcp.ack_raw",
    "tcp.checksum",
    "tcp.connection.fin",
    "tcp.connection.rst",
    "tcp.connection.syn",
    "tcp.connection.synack",
    "tcp.dstport",
    "tcp.flags",
    "tcp.flags.ack",
    "tcp.len",
    "tcp.options",
    "tcp.payload",
    "tcp.seq",
    "tcp.srcport",
    "udp.port",
    "udp.stream",
    "udp.time_delta",
    "dns.qry.name",
    "dns.qry.name.len",
    "dns.qry.qu",
    "dns.qry.type",
    "dns.retransmission",
    "dns.retransmit_request",
    "dns.retransmit_request_in",
    "mqtt.conack.flags",
    "mqtt.conflag.cleansess",
    "mqtt.conflags",
    "mqtt.hdrflags",
    "mqtt.len",
    "mqtt.msg_decoded_as",
    "mqtt.msg",
    "mqtt.msgtype",
    "mqtt.proto_len",
    "mqtt.protoname",
    "mqtt.topic",
    "mqtt.topic_len",
    "mqtt.ver",
    "mbtcp.len",
    "mbtcp.trans_id",
    "mbtcp.unit_id",
)

ALL_COLUMNS: tuple[str, ...] = (*_METADATA_COLUMNS, *FEATURE_COLUMNS)

# ── Raw data layout ───────────────────────────────────────────────────────
RAW_ROOT = "Edge-IIoTset"
RAW_DATASET_DIR = "Edge-IIoTset dataset"
RAW_ATTACK_DIR = "Attack traffic"
RAW_NORMAL_DIR = "Normal traffic"

# Normal traffic subdirectories (sensor names = client identifiers).
NORMAL_SENSOR_DIRS: tuple[str, ...] = (
    "Distance",
    "Flame_Sensor",
    "Heart_Rate",
    "IR_Receiver",
    "Modbus",
    "Soil_Moisture",
    "Sound_Sensor",
    "Temperature_and_Humidity",
    "Water_Level",
    "phValue",
)

# Attack traffic CSV base names (without _attack.csv suffix).
ATTACK_TYPES: tuple[str, ...] = (
    "Backdoor",
    "DDoS_HTTP_Flood",
    "DDoS_ICMP_Flood",
    "DDoS_TCP_SYN_Flood",
    "DDoS_UDP_Flood",
    "MITM",
    "OS_Fingerprinting",
    "Password",
    "Port_Scanning",
    "Ransomware",
    "SQL_injection",
    "Uploading",
    "Vulnerability_scanner",
    "XSS",
)

NUM_NORMAL_SENSORS: int = len(NORMAL_SENSOR_DIRS)
NUM_ATTACK_TYPES: int = len(ATTACK_TYPES)

# ── Split configuration ───────────────────────────────────────────────────
SPLIT_RATIOS: dict[str, float] = {
    "train": 0.60,
    "cal": 0.25,
}

CHRONOLOGICAL_SPLIT: bool = True
BENIGN_ONLY_CALIBRATION: bool = True

# ── DatasetSpec ────────────────────────────────────────────────────────────
EDGE_IIOTSET_SPEC = DatasetSpec(
    id=DatasetID.EDGE_IIOTSET,
    display_name="Edge-IIoTset",
    processed_slug=DatasetID.EDGE_IIOTSET.value,
    feature_count=FEATURE_COUNT,
    feature_columns=FEATURE_COLUMNS,
    label_column=LABEL_COLUMN,
    benign_label=BENIGN_LABEL,
    client_identity=ClientIdentity.DEVICE_DIRECTORY,
    raw_layout=RawLayout(root_slug=RAW_ROOT),
    split_policy=SplitPolicy(
        name="chronological_gapped",
        calibration_benign_only=BENIGN_ONLY_CALIBRATION,
        chronological=CHRONOLOGICAL_SPLIT,
        contiguous_gaps=False,
        ratios=SPLIT_RATIOS,
    ),
    cap_policy=None,
    family_map=None,
    device_ids=NORMAL_SENSOR_DIRS,
    attack_family_dirs=(),
    expected_client_count=NUM_NORMAL_SENSORS,
)
