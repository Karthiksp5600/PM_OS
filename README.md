# PM_OS

## Myntra Discovery on Railway

This repo is ready to deploy the Myntra discovery UI directly on Railway.

### What Railway runs

- Service: `python -m productpilot.discovery.ui.simple_web_app`
- Port: Railway injects `PORT`, and the app now binds to `0.0.0.0`
- Health endpoint: `/health`

### Deploy steps

1. Push this repo to GitHub.
2. In Railway, choose **New Project** → **Deploy from GitHub repo**.
3. Select this repository.
4. Railway will detect the root `Dockerfile` and deploy automatically.
5. After deploy, open **Networking** and generate a public domain.

### Recommended Railway variables

- `INGEST_RECORD_GOAL=3000`
- `STATIC_RECORD_GOAL=2500`
- `CRAWLEE_ENABLE=0`
- `MAXCRAWL_ENABLE=0`

These defaults keep the demo stable on a simple Railway deployment. You can turn live crawlers back on later by adding the right dependencies and variables.

### Local run

```bash
python3 -m productpilot.discovery.ui.simple_web_app
```

Then open:

```bash
http://127.0.0.1:8765
```
