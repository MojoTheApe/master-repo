#!/usr/bin/env python3
"""Run the exact compatible Tracker admission adapter from the verified snapshot.

The same mechanically refreshed portable closure already ships in this repository
for contract verification. It is the canonical engine, not a second rules copy.
Only the accepted main checkout may run this entry point with a write token.
"""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_contract

RUNTIME = Path(__file__).resolve().parents[1] / 'tests/fixtures/portable-contract/raw'


def runtime():
    raw, record, _ = export_contract.trusted()
    root = RUNTIME
    export_contract.check_manifest(export_contract.safe_file(root, export_contract.MANIFEST).read_bytes(), raw)
    for name, expected in export_contract.layout_files(record, 'raw').items():
        if hashlib.sha256(export_contract.safe_file(root, name).read_bytes()).hexdigest() != expected:
            raise ValueError('Trusted admission runtime differs from compatible Tracker: ' + name)
    entry = 'scripts/tracker_admission_gate.py'
    if entry not in record['layouts']['raw']:
        raise ValueError('Publish and select the compatible Tracker admission adapter before requiring this gate')
    return root / 'scripts'


def main():
    sys.path.insert(0, str(runtime()))
    import tracker_admission_gate
    tracker_admission_gate.main()


if __name__ == '__main__':
    main()
