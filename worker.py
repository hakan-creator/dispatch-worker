import os
import time
import logging
import requests

# --- Config from environment ---
WORKER_API_URL = os.environ["WORKER_API_URL"]
WORKER_API_KEY = os.environ["WORKER_API_KEY"]
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SECONDS", "5"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("worker")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {WORKER_API_KEY}",
}


def api(payload: dict) -> dict:
    r = requests.post(WORKER_API_URL, json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def process_job(job: dict, context: dict):
    """Placeholder – replace with real logic per job type."""
    job_id = job["id"]
    job_type = job["type"]
    log.info(f"Processing job {job_id} type={job_type}")

    # Report progress
    api({"action": "progress", "job_id": job_id, "progress": 50})

    # TODO: Add real processing logic here based on job_type
    # For now just mark as done
    api({
        "action": "complete",
        "job_id": job_id,
        "status": "DONE",
        "result": {"message": f"Job {job_type} completed (placeholder)"},
    })
    log.info(f"Job {job_id} completed")


def main():
    log.info(f"Worker started. Polling {WORKER_API_URL} every {POLL_INTERVAL}s")
    while True:
        try:
            data = api({"action": "poll"})
            job = data.get("job")
            if job:
                context = data.get("context", {})
                try:
                    process_job(job, context)
                except Exception as e:
                    log.exception(f"Job {job['id']} failed: {e}")
                    try:
                        api({
                            "action": "complete",
                            "job_id": job["id"],
                            "status": "FAILED",
                            "error": str(e),
                        })
                    except Exception:
                        log.exception("Failed to report job failure")
            else:
                log.debug("No jobs available")
        except Exception:
            log.exception("Poll error")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
