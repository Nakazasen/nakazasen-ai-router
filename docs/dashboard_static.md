# Static local dashboard

The static dashboard is a local, read-only control center for Nakazasen AI Router JSON metrics.

Open:

```text
examples/dashboard_static/index.html
```

It can load `sample_metrics.json`, parse pasted JSON, or parse an uploaded JSON file. Supported shapes include `collect_metrics().to_dict()`, `sdk_worker_stack_demo.py` summaries, and quota snapshots.

No server, network, API key, npm, or build step is required.

Use it to inspect provider health, job queue status, quota profiles, metrics summaries, and SDK integration blueprints.
