# Metrics và observability snapshot

Nakazasen AI Router cung cấp JSON metrics an toàn cho router và persistent job queue. Metrics là snapshot vận hành, không phải payload log.

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

Router metrics gồm số lượng candidate, trạng thái provider, counter success/failure, error type counts và latency aggregate nếu có.

## Job metrics

Job metrics gồm status counts, job đến hạn, lease hết hạn, job chạm max attempts, workload type counts và error type counts.

## An toàn

Metrics output không được chứa API key, authorization header, prompt, raw payload hoặc raw provider response.
