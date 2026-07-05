# Tích hợp SDK-first

Dùng `nakazasen-ai-router` như Python SDK embedded khi bạn chưa muốn Router Server trung tâm.

## Cài đặt

Từ local wheel:

```powershell
py -m pip install dist\nakazasen_ai_router-0.2.1-py3-none-any.whl
```

Từ GitHub:

```powershell
py -m pip install git+https://github.com/Nakazasen/nakazasen-ai-router.git
```

## Route tối thiểu

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env(provider_names=("gemini", "groq"), enable_network=True)
outcome = router.route_outcome(AIRequest(prompt="Summarize this", metadata={"task_type": "summarization"}))
```

## Full worker stack

Kết hợp các phần sau cho workload AI bền vững:

- `segment_text()` cho payload dài.
- `SQLiteJobStore` cho job bền vững.
- `InMemoryQuotaTracker` cho capacity check trong process.
- `AIRouter.route_outcome()` cho routing an toàn.
- `collect_metrics()` cho observability.

Xem `examples/sdk_worker_stack_demo.py`.

## Vệ sinh repo

Không commit API key, live report, production SQLite state hoặc raw prompt trong job metadata.
