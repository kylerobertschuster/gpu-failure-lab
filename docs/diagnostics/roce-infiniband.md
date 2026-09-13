# RoCE v2 & InfiniBand Network Diagnostics

Runtime debugging for GPU fabric networks. No custom tooling — these are the
vendor tools and kernel interfaces an SRE actually uses during an incident.

## The failure model

RoCE v2 rides on top of a *lossless* Ethernet fabric. Lossless requires three
things to work together; when one is off, you get silent stalls instead of
clean drops:

| Requirement | What it does | Symptom when wrong |
|-------------|--------------|--------------------|
| MTU 9000 (jumbo) | fewer frames, less overhead | poor bandwidth, fragmentation |
| PFC (priority 3) | backpressure instead of drops | packets dropped, retransmit storms |
| ECN / DCQCN | congestion notification | full buffer -> PFC storms, head-of-line blocking |

InfiniBand is natively lossless (credit-based flow control), so it doesn't need
PFC/ECN — but it has its own fabric-management failure modes.

## Inventory the fabric

```bash
# What RDMA devices exist?
ibv_devices
ibv_devinfo -v          # full capabilities, ports, RoCE mode

# Port state and link speed/width
ibstat
ibstat mlx5_0

# Confirm RoCE v2 vs IB (GID type: 1 = IB, 2 = RoCE v1, 3 = RoCE v2)
cat /sys/class/infiniband/mlx5_0/ports/1/gid_attrs/types/*

# Linux RDMA stack view
rdma link
rdma dev
```

## Check PFC (the #1 RoCE footgun)

PFC must be enabled on the **same priority** on every switch *and* every NIC in
the path. A mismatch means the "lossless" priority silently drops.

```bash
# Mellanox: enable PFC on priority 3 (RoCE traffic class)
mlnx_qos -i eth1 --pfc=0,0,0,1,0,0,0,0

# Verify what's actually applied
mlnx_qos -i eth1
```

```bash
# Ethernet counter view: pause frames tell you PFC is being *triggered*
ethtool -S eth1 | grep -iE 'pause|pfc|prio'
```

What to look for:
- `rx_prio3_pause` climbing → receivers are being overwhelmed (congestion).
- `tx_prio3_pause` climbing → this node is applying backpressure.
- A burst of pause frames followed by a stall → classic PFC/DCQCN interaction
  problem (see below).

## Check ECN / DCQCN

```bash
# ECN enabled at the TCP level?
sysctl net.ipv4.tcp_ecn

# ECN-marked / congestion counters
nstat -az | grep -iE 'ecn|cwr|retrans'

# Mellanox congestion control (DCQCN) parameters
mlnx_qos -i eth1
# or via sysfs on newer kernels
find /sys/class/infiniband/mlx5_0/ports/1 -name '*congest*' 2>/dev/null
```

**The PFC + DCQCN failure mode to know:** if ECN marking isn't reaching the
sender (bad switch config), the sender never slows down, the receiver buffer
fills, PFC kicks in as a last resort, and you get head-of-line blocking that
looks like a network "freeze" rather than drops. Fix the ECN path, don't just
band-aid PFC.

## Measure the fabric (perftest)

```bash
# Latency (us) and bandwidth (Gbps) between two RDMA nodes
ib_read_lat -d mlx5_0 -n 1000
ib_write_lat -d mlx5_0 -n 1000
ib_read_bw  -d mlx5_0 --report_gbits
ib_write_bw -d mlx5_0 --report_gbits -D 5
```

Interpretation:
- Latency in single-digit µs and bandwidth near line rate → fabric healthy.
- Bandwidth fine but latency spiky → congestion/ECN problem.
- Latency fine but bandwidth collapsed → MTU or PFC problem.

## Fabric topology & health (InfiniBand)

```bash
# Subnet topology map
ibnetdiscover -p

# Diagnostic scan (errors, link width downgrades, etc.)
ibdiagnet -r

# Watch counters live
ibdump          # capture RDMA traffic
perfquery -x    # port counters
```

## Quick triage table

| Symptom | First thing to check |
|---------|----------------------|
| Bandwidth far below line rate | MTU 9000 on every hop |
| Packets dropped on "lossless" queue | PFC priority mismatch NIC↔switch |
| Latency spikes under load | ECN marking path / DCQCN params |
| Full stall, no drops | PFC head-of-line blocking from missing ECN |
| Link flaps / width downgrade | physical layer (see `pcie-link-instability.md`) |
