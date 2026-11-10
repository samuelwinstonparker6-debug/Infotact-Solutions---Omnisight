# OmniSight API Reference

Base URL (local development): `http://127.0.0.1:8000`
Interactive Swagger docs: `/docs` | ReDoc: `/redoc`

## System & Settings

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/` | Root welcome metadata & docs links |
| `GET` | `/health` | Service health & database connectivity check |
| `GET` | `/api/v1/status` | Active service status and capabilities |
| `GET` | `/api/v1/settings` | Retrieve active VLM model & credential status |
| `POST` | `/api/v1/settings` | Update VLM model / credentials (persisted to `.env`) |
| `POST` | `/api/v1/system/clear-cache` | Clear temporary screenshots and cached artifacts |

## Scans & Self-Healing

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/v1/scan` | Trigger multi-viewport UI audit (`url`, `auto_fix`) |
| `GET` | `/api/v1/runs` | List historical and active scan runs |
| `GET` | `/api/v1/runs/{run_id}` | Fetch detailed bug findings & visual verification assets |
| `POST` | `/api/v1/scan/{run_id}/stop` | Stop an active scan by `run_id` |
| `POST` | `/api/v1/scan/stop` | Stop all currently running scans |
| `POST` | `/api/v1/bugs/{bug_id}/action` | Approve or reject an AI-generated bug fix |

## Export & GitHub Integration

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/scans/{run_id}/fixed_code.txt` | Download patched source code as `.txt` |
| `GET` | `/api/v1/scans/{run_id}/omnisight_scan_fixes.zip` | Download full verified patch bundle as `.zip` |
| `POST` | `/api/v1/scans/{run_id}/open-notepad` | Open generated code fixes directly in Notepad |
| `GET` | `/api/v1/github/status` | Check GitHub token authentication & target repo |
| `POST` | `/api/v1/github/connect` | Connect GitHub PAT and target repository |
| `POST` | `/api/v1/scans/{run_id}/create-pr` | Branch, commit verified fixes, and open GitHub PR |
| `POST` | `/api/v1/scans/{run_id}/sync-pr` | Sync merged PR changes back to local deployment |

## AI Design Studio & Webhooks

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/v1/design/interpret` | Classify natural-language prompt intent (`design` / `bugfix` / `both`) |
| `POST` | `/api/v1/design/generate` | Generate surgical CSS updates (with optional bug scan + PR) |
| `POST` | `/api/v1/webhook/ci-cd-trigger` | Trigger autonomous UI scan on CI/CD build events (`202 Accepted`) |
| `POST` | `/api/v1/webhook/github-events` | Handle native GitHub `pull_request` merge webhooks |
