# Persistent generic job queue

`SQLiteJobStore` is an optional domain-neutral queue for durable AI workers. It stores operational job state, not raw prompts or payloads.

## Boundary

Your app owns payloads and results. The job queue stores references:

- `payload_ref`
- `result_ref`
- `workload_type`
- attempts, leases, retry time, status
- sanitized metadata

## Basic worker loop

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

## Crash recovery

`claim_next()` leases a job for a worker. If a worker crashes, `release_expired_leases()` or a later claim can make expired jobs available again.

## Safety

`sanitize_job_metadata()` removes sensitive keys such as API keys, tokens, prompts, and raw payloads. Do not store raw user data in queue metadata.
