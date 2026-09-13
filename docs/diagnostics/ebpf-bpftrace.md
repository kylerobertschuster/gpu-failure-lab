# eBPF Runtime Diagnostics (bpftrace & bcc)

Kernel-level tracing for GPU-cluster networking and scheduling issues — using
**existing tools**, not hand-written C. `bpftrace` for one-liners, `bcc` for
batteries-included tools.

## Install

```bash
# Debian/Ubuntu
sudo apt-get install -y bpftrace bpfcc-tools linux-headers-$(uname -r)

# RHEL / Enterprise Linux
sudo dnf install -y bpftrace bcc-tools kernel-devel-$(uname -r)
```

## Why eBPF for GPU clusters

GPU training traffic is sensitive to two things that kernel tracing sees
directly: **TCP retransmissions** (congestion/loss) and **scheduler latency**
(CPU contention on the GPU node). Both are invisible to `ping`.

## TCP retransmits — the fabric's canary

Retransmits on a "lossless" RoCE fabric are a red flag: something is dropping
packets that should never drop.

```bash
# Count retransmits by process, live
sudo bpftrace -e 'kprobe:tcp_retransmit_skb { @retrans[comm] = count(); }'

# Retransmits by remote address (who are we retransmitting to?)
sudo bpftrace -e '
  kprobe:tcp_retransmit_skb {
    $sk = (struct sock *)arg0;
    @[comm, ntop($sk->__sk_common.skc_daddr)] = count();
  }'

# Histogram of retransmit events per 10s
sudo bpftrace -e '
  kprobe:tcp_retransmit_skb { @retrans = count(); }
  interval:s:10 { print(@retrans); clear(@retrans); }'
```

bcc equivalents (pre-built, nicer output):

```bash
sudo tcpretrans      # who's retransmitting, to where, with latency
sudo tcpconnect -T   # every TCP connect with timing
sudo tcplife         # connection lifetime + throughput
```

## Congestion events — ECN / CWR / loss

```bash
# Congestion Window Reduced (ECN) vs loss events
sudo bpftrace -e '
  kprobe:tcp_enter_cwr    { @cwr[comm] = count(); }
  kprobe:tcp_enter_loss   { @loss[comm] = count(); }
  kprobe:tcp_enter_recovery { @recovery[comm] = count(); }'

# If @loss is high but @cwr is zero on a RoCE fabric -> ECN marking is broken
# (see docs/diagnostics/roce-infiniband.md)
```

## Connection latency & handshake issues

```bash
# Time from SYN to accept (connection setup latency)
sudo bpftrace -e '
  kprobe:tcp_connect { @start[tid] = nsecs; }
  kretprobe:tcp_connect /@start[tid]/ {
    @connlat_us = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
  }'
```

bcc:

```bash
sudo tcpconnlat      # connection latency histogram (great for API endpoints)
```

## Scheduler latency — CPU contention on the GPU node

GPU nodes run CPU-bound workers (data loading, pre/post-processing) that can
starve the GPU. Runqueue latency is the tell.

```bash
# Wake-to-run latency via scheduler tracepoints (wakeup -> actually running)
sudo bpftrace -e '
  tracepoint:sched:sched_wakeup { @wake[args->pid] = nsecs; }
  tracepoint:sched:sched_switch {
    if (@wake[args->next_pid]) {
      @runqlat_us = hist((nsecs - @wake[args->next_pid]) / 1000);
      delete(@wake[args->next_pid]);
    }
  }'
```

bcc (much simpler and robust):

```bash
sudo runqlat       # runqueue latency histogram
sudo runqlen       # runqueue length over time
sudo cpudist       # CPU time distribution per task
```

High p99 `runqlat` (> a few ms) while the GPU sits idle → CPU contention, not a
GPU problem.

## Filesystem / OOM pressure (checkpointing, data loaders)

```bash
sudo biolatency     # block I/O latency — slow checkpoints?
sudo cachestat      # page-cache hit rate
sudo oomkill        # who got OOM-killed and when
```

## A reusable triage sequence

1. `tcpretrans` — is the fabric dropping packets?
2. `tcpconnlat` — are connects slow (control plane)?
3. `runqlat` — is the CPU starving the GPU?
4. `biolatency` — are checkpoints/dataloaders blocking on I/O?

Two minutes of tracing usually beats an hour of staring at dashboards.
