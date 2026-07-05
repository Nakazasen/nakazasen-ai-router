# Integration blueprints

## mat-the-website

If the repo has a Python backend, use the SDK directly for content generation, summarization, and chat-like features. If it is frontend-only, do not expose provider keys in the browser; add a backend/proxy inside that repo first.

## translation_app

Use embedded SDK mode. Treat translation as an app-level workload using `long_context` or `segmented_batch`. Combine segmentation, job queue, quota, and metrics.

## AIOS_habbit

Use embedded SDK for local assistant, planning, summarization, and background AI tasks. Use `SQLiteJobStore` for durable background tasks and metrics snapshots for health.

## SlideGenius

Use SDK for outline generation, slide content, speaker notes, structured JSON, and long-document summarization. Segment long inputs before generation.
