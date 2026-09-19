# SRAI Operations Dashboard v0.1

A lightweight, local and read-only Django dashboard for the authoritative `SRAI_Operations` registry.

## Install on Windows

1. Extract this package to `C:\SRAI_GitHub\SRAI_Operations_Dashboard`.
2. Open PowerShell in that folder.
3. Run `Set-ExecutionPolicy -Scope Process Bypass` if local scripts are blocked.
4. Run `.\install.ps1` once.
5. Run `.\run_dashboard.ps1` whenever you want the dashboard.
6. Open `http://127.0.0.1:8010/`.

The default registry path is `C:\SRAI_GitHub\SRAI_Operations`. To use another path for one session:

```powershell
$env:SRAI_OPERATIONS_ROOT = "D:\path\to\SRAI_Operations"
.\run_dashboard.ps1
```

## Safety model

- The application reads registry, manifest and evidence JSON files on every request.
- It contains no edit, delete, upload or write endpoint.
- It does not require a database.
- External channel links open in a new browser tab.

## Main views

- Registry overview with health counts, search and filters
- Production-unit detail with evidence, notes, follow-ups and channel links
- Machine-readable health endpoint at `/health.json`
