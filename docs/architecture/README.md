# Architecture

The engine is a deterministic pipeline. One telemetry fixture in, one
reproducible incident report out.

```mermaid
flowchart LR
    A[Telemetry Fixture<br/>scenarios/*.json] --> B[Diagnostic Engine<br/>diagnose.py]
    B --> O[Observe<br/>symptoms]
    O --> C[Correlate<br/>evidence checks]
    C --> I[Isolate<br/>root cause]
    I --> D[Diagnose<br/>confidence]
    D --> M[Communicate<br/>remediation steps]
    M --> R[Incident Report<br/>stdout]

    style A fill:#1f2937,stroke:#4b5563,color:#fff
    style B fill:#1e3a8a,stroke:#3b82f6,color:#fff
    style R fill:#065f46,stroke:#10b981,color:#fff
```

## Failure classification

Each fixture carries correlation evidence; the engine passes or fails each
check and derives a root cause with a confidence score.

```mermaid
flowchart TD
    E[Evidence] --> T1{PCIe error burst?}
    E --> T2{Link instability?}
    E --> T3{Thermal anomaly?}
    E --> T4{Compute saturation?}

    T1 -- yes --> RC[PCIe link instability]
    T2 -- yes --> RC
    T3 -- yes --> TH[Thermal issue]
    T4 -- yes --> CS[Capacity issue]
```

## Design principles

- **Deterministic**: same fixture → same report, every time.
- **No runtime dependencies**: stdlib only, no web UI, no metrics server.
- **Separation of concerns**: telemetry (fixtures) vs. reasoning (engine) vs.
  output (report).
