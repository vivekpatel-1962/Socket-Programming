import socket
import threading
import queue
import json
from typing import Dict, List, Any
import logging
import time
from utils import TaskResult, serialize_message, deserialize_message, split_range


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)

# Configure results logging
results_logger = logging.getLogger('results')
results_logger.setLevel(logging.INFO)
results_handler = logging.FileHandler('results.log')
results_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
results_logger.addHandler(results_handler)

class TaskServer:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.task_queue = queue.Queue()
        self.results: Dict[str, List[TaskResult]] = {}  # task_id -> list of results
        self.tasks_info: Dict[str, dict] = {}    # task_id -> task information
        self.lock = threading.Lock()
        self.retry_thread = threading.Thread(target=self._check_timeouts, daemon=True)
        self.running = True

    def start(self):
        """Start the server and listen for connections."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logging.info(f"Server started on {self.host}:{self.port}")
        
        # Start the retry checker thread
        self.retry_thread.start()

        while True:
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(30)  # Set socket timeout
                logging.info(f"New connection from {address}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

    def _check_timeouts(self):
        """Check for timed out tasks and requeue them."""
        while self.running:
            try:
                with self.lock:
                    for task_id, results in self.results.items():
                        for result in results:
                            if result.start_time and result.is_timed_out() and result.can_retry():
                                logging.warning(f"Task {task_id}, subtask {result.subtask_index} timed out. Retrying...")
                                # Reset task status
                                result.start_time = None
                                # Requeue the task
                                self.task_queue.put({
                                    'task_id': task_id,
                                    'subtask_index': result.subtask_index,
                                    'range': self.tasks_info[task_id]['ranges'][result.subtask_index]
                                })
            except Exception as e:
                logging.error(f"Error in timeout checker: {e}")
            time.sleep(5)  # Check every 5 seconds

    def handle_client(self, client_socket: socket.socket):
        """Handle incoming client connections."""
        try:
            # First message should identify the client type
            client_type = deserialize_message(client_socket).get('type')
            
            if client_type == 'task_sender':
                self.handle_task_sender(client_socket)
            elif client_type == 'worker':
                self.handle_worker(client_socket)
            else:
                logging.warning(f"Unknown client type: {client_type}")
                
        except Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def handle_task_sender(self, client_socket: socket.socket):
        """Handle task sender clients."""
        try:
            # Receive task
            task_data = deserialize_message(client_socket)
            task_id = task_data['task_id']
            task_range = task_data['range']
            num_subtasks = task_data['num_subtasks']

            # Split task into subtasks
            ranges = split_range(task_range[0], task_range[1], num_subtasks)
            subtasks = [
                {
                    'task_id': task_id,
                    'subtask_index': i,
                    'range': range_
                }
                for i, range_ in enumerate(ranges)
            ]
            
            # Store task information
            self.tasks_info[task_id] = {
                'total_subtasks': len(subtasks),
                'completed_subtasks': 0,
                'client_socket': client_socket,
                'ranges': ranges
            }
            
            # Initialize results tracking
            self.results[task_id] = [
                TaskResult(task_id, i) for i in range(len(subtasks))
            ]
            
            # Add subtasks to queue
            for subtask in subtasks:
                self.task_queue.put(subtask)
                
            logging.info(f"Task {task_id} split into {len(subtasks)} subtasks")
            
        except Exception as e:
            logging.error(f"Error handling task sender: {e}")

    def handle_worker(self, client_socket: socket.socket):
        """Handle worker clients."""
        while True:
            try:
                # Get a subtask from the queue
                if self.task_queue.empty():
                    # Send no-task message
                    client_socket.sendall(serialize_message({'status': 'no_task'}))
                    break

                subtask = self.task_queue.get()
                task_id = subtask['task_id']
                subtask_index = subtask['subtask_index']

                # Mark task as started
                with self.lock:
                    task_result = self.results[task_id][subtask_index]
                    task_result.start()

                # Send subtask to worker
                client_socket.sendall(serialize_message({
                    'status': 'task_available',
                    'subtask': subtask
                }))

                # Receive result
                result_data = deserialize_message(client_socket)
                result = result_data['result']

                # Store result and log it
                with self.lock:
                    task_result = self.results[task_id][subtask_index]
                    task_result.result = result
                    task_result.start_time = None  # Mark as completed
                    self.tasks_info[task_id]['completed_subtasks'] += 1

                    # Log the result
                    results_logger.info(
                        f"Task {task_id}, Subtask {subtask_index}: Range {subtask['range']}, "
                        f"Result: {result}, Attempts: {task_result.attempts}"
                    )

                    # Check if all subtasks are completed
                    if self.tasks_info[task_id]['completed_subtasks'] == self.tasks_info[task_id]['total_subtasks']:
                        self.send_final_result(task_id)

            except Exception as e:
                logging.error(f"Error handling worker: {e}")
                break

    def send_final_result(self, task_id: str):
        """Send the final combined result to the task sender."""
        try:
            client_socket = self.tasks_info[task_id]['client_socket']
            # Sum up all results for this task
            final_result = sum(r.result for r in self.results[task_id])
            
            client_socket.sendall(serialize_message({
                'status': 'completed',
                'result': final_result
            }))
            
            # Log final result
            results_logger.info(f"Task {task_id} completed. Final result: {final_result}")
            
            # Cleanup
            del self.results[task_id]
            del self.tasks_info[task_id]
            
            logging.info(f"Task {task_id} completed, final result sent")
            
        except Exception as e:
            logging.error(f"Error sending final result: {e}")

    def shutdown(self):
        """Shutdown the server gracefully."""
        self.running = False
        if self.retry_thread.is_alive():
            self.retry_thread.join()
        self.server_socket.close()

if __name__ == '__main__':
    server = TaskServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Server shutting down...")
        server.shutdown()
    except Exception as e:
        logging.error(f"Server error: {e}")
        server.shutdown() 
