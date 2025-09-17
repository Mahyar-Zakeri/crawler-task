# Crawler Worker 

## Features 
- **Worker (Python)**:
  - Fetch jobs from Redis (`url_queue`)
  - Fetch content via `requests`
  - Store results in PostgreSQL
  - Expose `/healthz` endpoint for health checks
  - Expose Prometheus metrics:
    - `crawler_fetch_total`
    - `crawler_success_total`
    - `crawler_error_total`

- **Dockerized**:
  - `Dockerfile` for the worker
  - `docker-compose.yml` for worker + Redis + Postgres

- **Documentation**:
  - `README.md` (this file)
  - `runbook.md` (operational scenarios)

---

##  How to Run

### 1. Build & start
```bash
docker-compose up --build -d
