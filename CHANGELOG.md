# Changelog

## 0.1.0 - Khởi tạo

- Tạo repo Python cho Nakazasen AI Router.
- Thêm API router tối thiểu.
- Thêm provider giả lập cho success, quota fail, auth fail, timeout.
- Thêm test fallback, cooldown quota, disable auth, local_only, và không log API key.

## 0.3.0 - Provider Registry và env config

- Thêm Provider Registry cho OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral và local OpenAI-compatible.
- Thêm `create_router_from_env()` để tạo router từ biến môi trường.
- Cloud provider không có API key sẽ bị bỏ qua.
- Local OpenAI-compatible có thể chạy không cần key nếu dùng localhost/127.0.0.1.
- Test mặc định vẫn mock-first, không gọi internet và không cần API key thật.
