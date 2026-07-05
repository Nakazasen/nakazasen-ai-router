# API key nhà cung cấp

Nakazasen AI Router không bao giờ ship API key. Người dùng tự cung cấp key qua environment variables hoặc key file đặt ngoài repo.

## Chế độ không có key

Không có key vẫn dùng được offline tests, fake providers, segmentation, SQLite jobs, quota policy, metrics, install smoke và static dashboard.

## Lấy key

- Gemini: tạo API key trong Google AI Studio.
- Groq: tạo API key trong Groq Console.
- OpenRouter: tạo API key trong OpenRouter Keys.

## Environment variables

```powershell
$env:GEMINI_API_KEY=""
$env:GROQ_API_KEY=""
$env:OPENROUTER_API_KEY=""
```

## Key file ngoài repo

Copy `docs/provider_keys.example.env` ra ngoài repo rồi điền provider bạn dùng:

```text
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
```

Test key:

```powershell
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\provider_keys.txt"
```

## Setup có hướng dẫn

```powershell
py scripts/key_setup.py --out "D:\path\to\provider_keys.txt"
```

Helper dùng masked input và từ chối ghi vào repo này trừ khi bạn truyền `--allow-inside-repo`.

## Troubleshooting

- Thiếu key: set env var hoặc truyền `--key-file`.
- Key sai: tạo lại trong console provider.
- Quota/429: chờ hoặc dùng provider profile khác.
- Network disabled: set `enable_network=True` trong SDK code.
- Sai path file: dùng absolute path ngoài repo.
