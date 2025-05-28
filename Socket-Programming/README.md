# Distributed Task Processing System

This is a distributed task processing system implemented using TCP sockets in Python. The system consists of three components:
1. Server - Manages task distribution and result collection
2. Task Sender - Sends computational tasks to the server
3. Worker - Processes subtasks and returns results

## Features
- Splits large computational tasks into smaller subtasks
- Distributes subtasks among multiple workers
- Combines results and returns them to the task sender
- Handles multiple task senders and workers simultaneously
- Built with pure Python standard library (no external dependencies)

## Example Use Case
The current implementation demonstrates the calculation of sum of squares for a large range of numbers (e.g., from 1 to 1,000,000). The task is split into multiple subtasks that are processed in parallel by different workers.

## How to Run

1. First, start the server:
```bash
python server.py
```

2. Start one or more workers in separate terminal windows:
```bash
python worker.py
```

3. Run the task sender to submit a task:
```bash
python task_sender.py
```

## Architecture

### Server (`server.py`)
- Listens for incoming connections from task senders and workers
- Splits tasks into subtasks
- Maintains a queue of subtasks
- Collects and combines results
- Sends final results back to task senders

### Task Sender (`task_sender.py`)
- Connects to the server
- Sends computational tasks
- Waits for and receives final results

### Worker (`worker.py`)
- Connects to the server
- Requests subtasks
- Processes subtasks
- Sends results back to the server

## Protocol
The system uses a simple message protocol with JSON payloads:
1. Message length (4 bytes, big-endian)
2. JSON message payload

## Error Handling
- Graceful handling of client disconnections
- Logging of errors and important events
- Automatic task queue management

## Customization
To implement different types of tasks:
1. Modify the `process_subtask` method in `worker.py`
2. Update the `split_task` method in `server.py`
3. Adjust the `send_final_result` method in `server.py` to combine results appropriately 