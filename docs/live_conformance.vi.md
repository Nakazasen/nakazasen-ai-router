# Live provider conformance

Live conformance kiểm chứng provider thật nhưng không biến live check thành test mặc định hoặc CI bắt buộc.

## Quy tắc an toàn

- Dùng key file nằm ngoài repository.
- Không commit live report.
- Không print hoặc lưu raw API key.
- Không lưu raw test prompt trong router state hoặc attempts.
- Report đã sanitize và chỉ chứa provider/model/status/error type/latency/preview ngắn.

## Chạy một provider

```powershell
py scripts/live_conformance.py --provider gemini --key-file "path\to\provider_keys.txt"
```

Ghi report tùy chọn:

```powershell
py scripts/live_conformance.py --provider gemini --key-file "path\to\provider_keys.txt" --json-out local_cases/conformance_gemini.json
```

## Check tùy chọn

```powershell
py scripts/live_conformance.py --provider gemini --key-file "path\to\provider_keys.txt" --include-async --include-stream
```

## Tất cả provider có key

```powershell
py scripts/live_conformance.py --all-configured --key-file "path\to\provider_keys.txt"
```

Lệnh thành công nếu ít nhất một provider configured pass. Provider thiếu key sẽ có status `missing key`.
