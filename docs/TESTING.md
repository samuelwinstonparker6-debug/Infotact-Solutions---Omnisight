# OmniSight Testing & Benchmark Guide

## 1. Unit & API Integration Tests

Run the full fast test suite using `pytest` from the `omnisight/` root:

```bash
python -m pytest tests/test_api.py tests/test_self_healing_pipeline.py -v
```

### What Is Verified
- **API Health & Status (`tests/test_api.py`)**: Root welcome endpoint, `/health` SQLite connectivity check, `/api/v1/status`, scan creation, scan listing, and active scan cancellation.
- **Pipeline & GitHub Fallback (`tests/test_self_healing_pipeline.py`)**: CI/CD webhook acceptance (`202 Accepted`) and safe mock fallback when `GITHUB_TOKEN` is absent.

## 2. Multimodal Vision Benchmark

The vision evaluation harness validates precision, recall, and F1-score against the calibrated 8-defect target in `mock-app/ground_truth.json`:

```bash
python -m pytest tests/test_vision_benchmark.py -v
```

## 3. Frontend Lint & Production Build Verification

```bash
cd frontend
npm run lint
npm run build
```
