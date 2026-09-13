# Runbook: PCIe Link Instability

## Purpose

Diagnose and remediate PCIe link instability on a GPU node, characterized by a
correctable-error burst, repeated link retrains, and application latency
degradation.

## When to use

- PCIe correctable errors trending sharply upward.
- Link retrains > 0 on a healthy workload.
- Application latency climbing while thermals and utilization look normal.

## Prerequisites

- Host access to the affected node.
- Baseline values for the node's AER counters and link status.

## Procedure

### 1. Inspect PCIe AER counters

```bash
# Summary of AER errors
lspci -vvv | grep -i -A 5 "Advanced Error Reporting"

# Correctable/uncorrectable error counts
cat /sys/bus/pci/devices/*/aer_dev_correctable
cat /sys/bus/pci/devices/*/aer_dev_fatal
```

### 2. Verify PCIe topology and link status

```bash
# Current link speed and width per device
lspci -vvv | grep -i -E "LnkSta|LnkCap"

# Confirm the GPU is at the expected width (e.g. x16) and gen (e.g. Gen4)
nvidia-smi -q | grep -i -A 4 "Link"
```

### 3. Check riser / backplane connectivity

- Power down the node.
- Reseat the GPU and any riser card.
- Inspect the slot and backplane for dust or physical damage.
- Power on and re-check AER counters over a 30-minute window.

### 4. Compare neighboring nodes

```bash
# Does the error signature appear on sibling nodes?
# If yes -> backplane or shared-power issue.
# If no  -> isolated to this slot/GPU.
```

## Validation

- [ ] AER correctable counters return to baseline.
- [ ] Zero link retrains over the observation window.
- [ ] Application latency back within normal range.

## Escalation

If reseating does not clear the errors, escalate to hardware vendor with:
- `lspci -vvv` output
- AER counter history
- Riser/backplane serial numbers
