# Metrics and observability snapshots

Nakazasen AI Router exposes safe JSON metrics for routers and persistent job queues. Metrics are operational snapshots, not payload logs.

## Python API

```python
from nakazasen_ai_router import collect_metrics

snapshot = collect_metrics(router, job_store).to_dict()
```

## CLI

```powershell
py scripts/router_metrics.py --jobs jobs.sqlite3
py scripts/router_metrics.py --router-state-json router_state.json
py scripts/router_metrics.py --jobs jobs.sqlite3 --json-out metrics.json
```

## Router metrics

Router metrics include candidate counts, provider health counts, success/failure counters, error type counts, and latency aggregates when available.

## Job metrics

Job metrics include status counts, due jobs, expired leases, max-attempt jobs, workload type counts, and error type counts.

## Safety

Metrics output must not contain API keys, authorization headers, prompts, raw payloads, or raw provider responses.
