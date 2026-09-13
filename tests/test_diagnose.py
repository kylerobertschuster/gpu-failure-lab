"""Tests for the diagnostic engine."""

from __future__ import annotations

import json
from pathlib import Path

import diagnose

FIXTURE = Path(__file__).parent.parent / "scenarios" / "pcie_error.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_is_valid() -> None:
    data = load_fixture()
    assert data["incident_id"] == "GPU-NODE-07"
    assert data["severity"] == "HIGH"
    assert data["root_cause"] == "PCIe link instability"
    assert data["confidence"] == "91%"


def test_print_report_contains_key_fields(capsys) -> None:
    diagnose.print_report(load_fixture())
    out = capsys.readouterr().out
    assert "GPU-NODE-07" in out
    assert "PCIe link instability" in out
    assert "CONFIDENCE" in out
    assert "91%" in out


def test_main_no_args_returns_1(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["diagnose.py"])
    assert diagnose.main() == 1


def test_main_with_fixture(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["diagnose.py", str(FIXTURE)])
    assert diagnose.main() == 0
    assert "INCIDENT: GPU-NODE-07" in capsys.readouterr().out


def test_main_missing_file_returns_1(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["diagnose.py", "does/not/exist.json"])
    assert diagnose.main() == 1
