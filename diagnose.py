#!/usr/bin/env python3
"""GPU Failure Lab — deterministic incident analyzer.

Usage:
    python3 diagnose.py scenarios/pcie_error.json

Turns a telemetry fixture (JSON) into a reproducible incident report:
observe → correlate → isolate → diagnose → communicate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HEADER = """╔══════════════════════════════════════════════╗
║ GPU INFRASTRUCTURE INCIDENT ANALYZER         ║
╚══════════════════════════════════════════════╝"""


def print_report(data: dict) -> None:
    print(HEADER)
    print(f"\nINCIDENT: {data.get('incident_id', 'UNKNOWN')}")
    print(f"SEVERITY: {data.get('severity', 'UNKNOWN')}\n")

    print("SYMPTOMS")
    for key, val in data.get("symptoms", {}).items():
        print(f"  {key:<27} {val}")

    print("\nCORRELATION")
    for item in data.get("correlation", []):
        mark = "✓" if item.get("status") else "✗"
        print(f"  {mark} {item.get('check', '?')}")

    print("\nLIKELY ROOT CAUSE")
    print(f"  {data.get('root_cause', 'Unknown')}")

    print("\nCONFIDENCE")
    print(f"  {data.get('confidence', 'N/A')}")

    print("\nNEXT INVESTIGATION")
    for idx, step in enumerate(data.get("remediation", []), 1):
        print(f"  {idx}. {step}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 diagnose.py <path_to_scenario.json>")
        return 1

    file_path = Path(sys.argv[1])
    if not file_path.is_file():
        print(f"Error: File '{file_path}' not found.")
        return 1

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    print_report(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
