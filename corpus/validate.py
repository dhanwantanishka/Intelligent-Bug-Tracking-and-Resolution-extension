"""
IBTRRS Corpus Validator
Validates schema conformity, SPDX license, absence of sensitive secrets, and duplicate IDs.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Dict, Any

SUSPICIOUS_SECRET_PATTERNS = [
    re.compile(r"(?i)(?:api_key|secret|password|bearer|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"sk-[A-Za-z0-9]{32,}")
]


def validate_corpus_file(jsonl_path: Path) -> List[Dict[str, Any]]:
    records = []
    seen_ids = set()

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Line {line_num}: Invalid JSON syntax: {e}")

            record_id = rec.get("record_id")
            if not record_id:
                raise ValueError(f"Line {line_num}: Missing record_id")
            if record_id in seen_ids:
                raise ValueError(f"Line {line_num}: Duplicate record_id: {record_id}")
            seen_ids.add(record_id)

            if rec.get("schema_version") != "1.0":
                raise ValueError(f"Record {record_id}: Invalid schema_version (expected '1.0')")

            if rec.get("language") != "python":
                raise ValueError(f"Record {record_id}: Language must be 'python'")

            license_info = rec.get("license", {})
            if license_info.get("spdx") != "CC0-1.0":
                raise ValueError(f"Record {record_id}: License SPDX must be 'CC0-1.0'")

            provenance = rec.get("provenance", {})
            if provenance.get("origin") != "authored":
                raise ValueError(f"Record {record_id}: Provenance origin must be 'authored'")

            # Secret scanning check
            full_text = json.dumps(rec)
            for pat in SUSPICIOUS_SECRET_PATTERNS:
                if pat.search(full_text):
                    raise ValueError(f"Record {record_id}: Secret scanner detected potential credential")

            records.append(rec)

    return records


if __name__ == "__main__":
    records_file = Path(__file__).resolve().parent.parent / "records" / "records.jsonl"
    validated = validate_corpus_file(records_file)
    print(f"Validated {len(validated)} records successfully. All schema and license checks passed.")

