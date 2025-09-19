# Runbook

This document describes how to respond to specific operational scenarios.

---

## 1) CAPTCHA (auto-quarantine)

**Symptoms**:  
- HTML response contains a CAPTCHA page or HTTP 403.

**Actions**:  
- Place the URL/domain into a quarantine list ( Redis key: `quarantine`) for 10 minutes.  
- Do not requeue the job until the quarantine period expires.  
- Reduce request rate or change the user-agent.  
- Log a warning for monitoring or alerting.

**Recovery**:  
- After the quarantine period, retry once.  
- If CAPTCHA repeats, increase the quarantine period or permanently exclude the domain.

---

## 2) Node failure (auto-replace)

**Symptoms**:  
- Worker container marked as `unhealthy` or exits unexpectedly.

**Actions**:  
- `restart: on-failure` is enabled, so the container will restart automatically.  
- If failures keep repeating:
  ```bash
  docker-compose restart worker
