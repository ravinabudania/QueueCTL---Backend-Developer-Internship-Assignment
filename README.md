# 🧠 QueueCTL – CLI-Based Background Job Queue System

`QueueCTL` is a lightweight **Python-based background job queue** that lets you enqueue shell commands, run them with worker processes, handle retries with exponential backoff, and manage a **Dead Letter Queue (DLQ)** — all from the command line.

---

## 🚀 Features

- 🧾 **Job Queue Management** – Enqueue shell commands to run asynchronously  
- ⚙️ **Worker Processes** – Run multiple workers concurrently using `multiprocessing`  
- 🔁 **Retry & DLQ Handling** – Automatically retry failed jobs and move permanently failed ones to DLQ  
- 💾 **Persistent Storage** – Uses SQLite for job state tracking  
- 🧩 **Simple CLI Interface** – Manage queue, workers, and DLQ directly from terminal  

---

## 📦 Tech Stack

| Component | Description |
|------------|--------------|
| Language | Python 3.8+ |
| Database | SQLite |
| Concurrency | `multiprocessing` |
| CLI Parsing | `argparse` |
| Process Execution | `subprocess` |

---

## 🧰 Installation

```bash
git clone https://github.com/<username>/queuectl.git
cd queuectl
python -m venv .venv
.venv\Scripts\activate   # (on Windows)
pip install -r requirements.txt  # if you add any in the future

# QueueCTL - Job Queue Management System

A lightweight job queue system with SQLite backend and worker management.
```

Expected output:

jobs: {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0, 'dead': 0}

2️⃣ Create a Job File

Create a JSON file (e.g., job.json):

{
  "id": "job1",
  "command": "echo Hello from QueueCTL",
  "max_retries": 3
}

3️⃣ Enqueue a Job
python queuectl.py enqueue --file job.json


Output:

enqueued job job1

4️⃣ View Jobs in the Queue
python queuectl.py list


Output:

job1 - pending - echo Hello from QueueCTL

5️⃣ Start Worker(s)
python queuectl.py worker start --count 1


Output:

[worker-0] started PID=12345
[worker-0] executing job job1: echo Hello from QueueCTL
[worker-0] completed job1

6️⃣ Re-check Job Status
python queuectl.py status


Output:

jobs: {'pending': 0, 'processing': 0, 'completed': 1, 'failed': 0, 'dead': 0}

7️⃣ Manage the Dead Letter Queue (DLQ)

List jobs that permanently failed:

python queuectl.py dlq list


Retry a dead job:

python queuectl.py dlq retry job1
