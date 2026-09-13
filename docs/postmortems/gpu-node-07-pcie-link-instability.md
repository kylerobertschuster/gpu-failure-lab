# Incident Postmortem: PCIe Link Instability on GPU-NODE-07

> Reconstructed from the deterministic telemetry fixture `scenarios/pcie_error.json`.
> The diagnostic engine reproduced this incident end-to-end: observe → correlate →
> isolate → diagnose → communicate.

## Metadata

| Field | Value |
|-------|-------|
| Incident ID | GPU-NODE-07 |
| Severity | HIGH |
| Status | Resolved |
| Root cause confidence | 91% |
| Diagnosis path | `python3 diagnose.py scenarios/pcie_error.json` |

## Summary

A burst of PCIe correctable errors and repeated link retrains on `GPU-NODE-07`
degraded application latency by 34%. Correlation ruled out thermal and compute
saturation as causes and isolated **PCIe link instability** as the root cause.

## Impact

| Metric | Value |
|--------|-------|
| PCIe correctable errors | ↑ 847% |
| Link retrains | 12 |
| GPU utilization | 91% |
| GPU temperature | 67°C (normal) |
| Application latency | +34% |

## Timeline

| Phase | Event | Action |
|-------|-------|--------|
| Observe | Correctable-error counter spiked 847% | Symptom captured from telemetry |
| Correlate | Link retrains + latency degradation present; thermal and saturation checks failed | Evidence checks run |
| Isolate | PCIe error burst + link instability both positive | Root cause narrowed to PCIe |
| Diagnose | PCIe link instability, 91% confidence | Root cause recorded |
| Communicate | Remediation chain emitted | Next investigation steps produced |

## Root Cause

PCIe link instability, evidenced by a correctable-error burst and 12 link
retrains. Thermal anomaly and compute saturation were **explicitly ruled out**,
so the failure is a physical-layer / interconnect problem rather than a
thermals or workload issue.

## Resolution

Immediate investigation steps, in order:

1. Inspect PCIe AER (Advanced Error Reporting) counters.
2. Verify PCIe topology.
3. Check riser / backplane connectivity.
4. Compare with neighboring nodes.

## Prevention

| Action item | Owner | Priority | Due | Status |
|-------------|-------|----------|-----|--------|
| Add AER counter alerting to telemetry | Platform SRE | P0 | +1 wk | Open |
| Document PCIe runbook | Platform SRE | P0 | +1 wk | Done (see `docs/runbooks/pcie-link-instability.md`) |
| Add riser/backplane reseat procedure | DC Ops | P1 | +2 wk | Open |

## Lessons Learned

- **What went well**: the correlation step cleanly eliminated two competing
  hypotheses (thermal, saturation) before reaching the root cause.
- **What to improve**: a single-node fixture can't yet compare against
  neighboring nodes — cross-node comparison is a manual follow-up today.
