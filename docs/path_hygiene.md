# Path hygiene

This repo must stay portable. Do not commit machine-specific paths, API key file names, local install smoke folders, or generated local artifacts.

Blocked examples include:

- `<drive>:\local-project-folder\...`
- `<drive>:\Users\<name>\...`
- `file:///<drive>:/...`
- a private key filename such as a personal API-key text file
- temporary install smoke folders

Allowed documentation placeholders include:

- `D:\path\to\provider_keys.txt`
- `D:\duong_dan_ngoai\provider_keys.txt`
- `path\to\provider_keys.txt`

Allowed local output conventions include `.demo_*` example folders and `local_cases/` for opt-in reports. These outputs should not be committed unless explicitly documented as safe sample data.

Run:

```powershell
py scripts/audit_local_paths.py
py -m pytest tests/test_local_path_leaks.py -q
```
