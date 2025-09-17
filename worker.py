import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

import psycopg2
import redis
import requests
from prometheus_client import start_http_server, Counter

# Prometheus counters
fetch_total = Counter("crawler_fetch_total", "Total fetch attempts")
success_total = Counter("crawler_success_total", "Total successful fetches")
error_total = Counter("crawler_error_total", "Total failed fetches")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "crawlerdb")
PG_USER = os.getenv("POSTGRES_USER", "crawleruser")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "crawlerpass")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


# healthz server
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200);
            self.end_headers();
            self.wfile.write(b"OK")
        else:
            self.send_response(404);
            self.end_headers()


def start_health_server():
    HTTPServer(("", 8001), HealthHandler).serve_forever()


def get_pg_conn():
    while True:
        try:
            conn = psycopg2.connect(host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASS, port=PG_PORT)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS results(
                    id SERIAL PRIMARY KEY,
                    url TEXT, status_code INT, content TEXT,
                    fetched_at TIMESTAMP DEFAULT NOW()
                )""")
            return conn
        except Exception as e:
            print("DB connect retry:", e);
            time.sleep(5)


def main():
    # start metrics & health servers
    start_http_server(8000)
    threading.Thread(target=start_health_server, daemon=True).start()

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    conn = get_pg_conn()
    cur = conn.cursor()

    print("Worker ready. Waiting for jobs on Redis list 'url_queue'...")
    while True:
        _, job = r.blpop("url_queue")  # blocks until a URL arrives
        url = job.decode() if isinstance(job, bytes) else job
        fetch_total.inc()
        try:
            resp = requests.get(url, timeout=10)
            status = resp.status_code
            body = resp.text[:500]
            (success_total if status == 200 else error_total).inc()
            cur.execute("INSERT INTO results(url, status_code, content) VALUES (%s, %s, %s)", (url, status, body))
            print(f"Fetched {url} [{status}]")
        except Exception as e:
            error_total.inc()
            print(f"Error fetching {url}: {e}")


if __name__ == "__main__":
    main()
