## 🔧 How It Works

1. The `client.py` submits a large computation task (e.g., sum squares).
2. The `server.py` breaks the task into subtasks and assigns them to `worker.py`.
3. Each worker processes a subtask and sends the result back.
4. The server combines all results and sends the final output to the client.

## 🧪 Try It Locally

1. Run `server.py`
2. Start `worker.py` in 2+ terminals
3. Run `client.py` to send a job
