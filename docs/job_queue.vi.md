# Job queue generic bền vững

`SQLiteJobStore` là queue tùy chọn, trung lập domain, dành cho AI worker bền vững. Nó lưu trạng thái vận hành của job, không lưu raw prompt hoặc payload.

## Ranh giới

App của bạn sở hữu payload và result. Job queue chỉ lưu reference:

- `payload_ref`
- `result_ref`
- `workload_type`
- attempts, lease, retry time, status
- metadata đã sanitize

## Worker loop cơ bản

```python
from nakazasen_ai_router import AIRequest, JobStatus, SQLiteJobStore

jobs = SQLiteJobStore("jobs.sqlite3")
job = jobs.enqueue("payloads/doc-1.txt", workload_type="summarization")

while True:
    job = jobs.claim_next("worker-1", lease_seconds=300)
    if job is None:
        break
    payload = load_payload(job.payload_ref)
    outcome = router.route_outcome(AIRequest(prompt=payload, metadata={"job_id": job.job_id}))
    if outcome.status == "success" and outcome.result:
        result_ref = save_result(outcome.result.text)
        jobs.mark_success(job.job_id, result_ref=result_ref)
    elif outcome.status == "retry_later":
        jobs.mark_retry_later(job.job_id, retry_after_seconds=outcome.retry_after_seconds or 60, error_type=outcome.error_type or "retry_later")
    else:
        jobs.mark_failed(job.job_id, error_type=outcome.error_type or "route_failed")
```

## Khôi phục sau crash

`claim_next()` lease job cho worker. Nếu worker crash, `release_expired_leases()` hoặc lần claim sau có thể đưa job hết hạn lease quay lại queue.

## An toàn

`sanitize_job_metadata()` loại bỏ key nhạy cảm như API key, token, prompt và raw payload. Không lưu raw user data trong metadata của queue.
