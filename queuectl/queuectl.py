#!/usr/bin/env python3
import argparse, json, sqlite3, subprocess, multiprocessing, os, time, datetime

DB_FILE = "queuectl.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        command TEXT NOT NULL,
        state TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        max_retries INTEGER NOT NULL DEFAULT 3,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        next_run INTEGER,
        last_exit_code INTEGER,
        last_stdout TEXT,
        last_stderr TEXT
    )
    """)
    conn.commit()
    conn.close()

def connect():
    return sqlite3.connect(DB_FILE, timeout=10, check_same_thread=False)

def enqueue_job(job_data):
    job_id = job_data.get("id")
    cmd = job_data.get("command")
    max_retries = job_data.get("max_retries", 3)
    now = datetime.datetime.utcnow().isoformat()
    with connect() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT OR REPLACE INTO jobs
               (id, command, state, attempts, max_retries, created_at, updated_at)
               VALUES (?, ?, 'pending', 0, ?, ?, ?)""",
            (job_id, cmd, max_retries, now, now),
        )
        conn.commit()
    print(f"enqueued job {job_id}")

def list_jobs():
    with connect() as conn:
        c = conn.cursor()
        for row in c.execute("SELECT id, state, command FROM jobs ORDER BY created_at"):
            print(f"{row[0]} - {row[1]} - {row[2]}")

def show_status():
    with connect() as conn:
        c = conn.cursor()
        counts = {}
        for s in ["pending", "processing", "completed", "failed", "dead"]:
            c.execute("SELECT COUNT(*) FROM jobs WHERE state=?", (s,))
            counts[s] = c.fetchone()[0]
        print("jobs:", counts)

def update_job_state(job_id, state, exit_code=None, stdout=None, stderr=None, attempts=None):
    with connect() as conn:
        c = conn.cursor()
        now = datetime.datetime.utcnow().isoformat()
        c.execute("""
        UPDATE jobs SET state=?, last_exit_code=?, last_stdout=?, last_stderr=?,
                        updated_at=?, attempts=COALESCE(?, attempts)
        WHERE id=?""",
        (state, exit_code, stdout, stderr, now, attempts, job_id))
        conn.commit()

def fetch_pending_job():
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT id, command, attempts, max_retries FROM jobs WHERE state='pending' ORDER BY created_at LIMIT 1")
        return c.fetchone()

def mark_processing(job_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("UPDATE jobs SET state='processing', updated_at=? WHERE id=?", (datetime.datetime.utcnow().isoformat(), job_id))
        conn.commit()

def worker_loop(worker_id):
    while True:
        job = fetch_pending_job()
        if not job:
            time.sleep(1)
            continue
        job_id, cmd, attempts, max_retries = job
        mark_processing(job_id)
        print(f"[worker-{worker_id}] executing job {job_id}: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                update_job_state(job_id, "completed", result.returncode, result.stdout, result.stderr, attempts)
                print(f"[worker-{worker_id}] completed {job_id}")
            else:
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        except Exception as e:
            attempts += 1
            if attempts > max_retries:
                update_job_state(job_id, "dead", -1, None, str(e), attempts)
                print(f"[worker-{worker_id}] job {job_id} moved to DLQ")
            else:
                update_job_state(job_id, "pending", -1, None, str(e), attempts)
                print(f"[worker-{worker_id}] retrying {job_id} (attempt {attempts})")
        time.sleep(1)

def start_workers(count):
    for i in range(count):
        p = multiprocessing.Process(target=worker_loop, args=(i,))
        p.start()
        print(f"[worker-{i}] started PID={p.pid}")

def handle_dlq(action, job_id=None):
    with connect() as conn:
        c = conn.cursor()
        if action == "list":
            for row in c.execute("SELECT id, command FROM jobs WHERE state='dead'"):
                print(f"{row[0]} - {row[1]}")
        elif action == "retry" and job_id:
            c.execute("UPDATE jobs SET state='pending', attempts=0 WHERE id=? AND state='dead'", (job_id,))
            if c.rowcount:
                print(f"retried job {job_id}")
            else:
                print(f"job not found in DLQ")
            conn.commit()

def main():
    parser = argparse.ArgumentParser(prog="queuectl")
    sub = parser.add_subparsers(dest="cmd")

    p_enqueue = sub.add_parser("enqueue")
    p_enqueue.add_argument("--file", help="JSON file with job details")

    sub.add_parser("list")
    sub.add_parser("status")

    p_worker = sub.add_parser("worker")
    p_worker.add_argument("action", choices=["start"])
    p_worker.add_argument("--count", type=int, default=1)

    p_dlq = sub.add_parser("dlq")
    p_dlq.add_argument("action", choices=["list", "retry"])
    p_dlq.add_argument("job_id", nargs="?")

    args = parser.parse_args()
    init_db()

    if args.cmd == "enqueue":
        if not args.file:
            print("please specify --file job.json")
            return
        with open(args.file) as f:
            job_data = json.load(f)
        enqueue_job(job_data)
    elif args.cmd == "list":
        list_jobs()
    elif args.cmd == "status":
        show_status()
    elif args.cmd == "worker":
        if args.action == "start":
            start_workers(args.count)
    elif args.cmd == "dlq":
        handle_dlq(args.action, args.job_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
