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

