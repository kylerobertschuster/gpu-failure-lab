# GPU Failure Lab

Deterministic, reproducible telemetry diagnostic engine for high-performance
computing (HPC) and GPU infrastructure failures.

## Quickstart

```bash
python3 diagnose.py scenarios/pcie_error.json
```

## Architecture

- `scenarios/` — incident telemetry JSON fixtures representing hardware anomalies.
- `diagnose.py` — CLI analyzer isolating root causes and generating incident response chains.

No web UI. No Kubernetes. No Grafana. No AI.

One JSON fixture → one diagnostic engine → one reproducible incident report.

## Operations docs

- `docs/postmortems/` — incident postmortems (with a reusable template)
- `docs/runbooks/` — investigation runbooks (e.g. PCIe link instability)
- `docs/slo/` — vendor-neutral SLO/SLI and error-budget definitions
- `docs/architecture/` — Mermaid diagrams of the diagnostic pipeline
- `docs/diagnostics/` — RoCE/InfiniBand and eBPF (bpftrace/bcc) runtime diagnostics

## Development

```bash
pytest -v          # run tests
ruff check .       # lint
ruff format .      # format
```
