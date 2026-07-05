# Static local dashboard

Static dashboard là control center local, read-only cho JSON metrics của Nakazasen AI Router.

Mở:

```text
examples/dashboard_static/index.html
```

Dashboard có thể load `sample_metrics.json`, parse JSON được paste hoặc parse file JSON upload. Shape được hỗ trợ gồm `collect_metrics().to_dict()`, summary từ `sdk_worker_stack_demo.py` và quota snapshot.

Không cần server, network, API key, npm hoặc build step.

Dùng để xem provider health, job queue status, quota profiles, metrics summary và SDK integration blueprints.
