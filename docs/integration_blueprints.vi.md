# Blueprint tích hợp

## mat-the-website

Nếu repo có Python backend, dùng SDK trực tiếp cho content generation, summarization và tính năng kiểu chat. Nếu chỉ là frontend, không expose provider key trong browser; hãy thêm backend/proxy trong repo đó trước.

## translation_app

Dùng embedded SDK mode. Xem translation là workload ở tầng app với `long_context` hoặc `segmented_batch`. Kết hợp segmentation, job queue, quota và metrics.

## AIOS_habbit

Dùng embedded SDK cho local assistant, planning, summarization và background AI tasks. Dùng `SQLiteJobStore` cho task nền bền vững và metrics snapshot để xem sức khỏe.

## SlideGenius

Dùng SDK cho outline generation, slide content, speaker notes, structured JSON và tóm tắt tài liệu dài. Segment input dài trước khi generate.
