import socket
import logging
import time
from utils import serialize_message, deserialize_message, calculate_squares_sum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Worker:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """Connect to the server."""
        self.socket.connect((self.host, self.port))
        self.socket.settimeout(35)  # Set timeout slightly higher than server's
        # Identify as worker
        self.socket.sendall(serialize_message({'type': 'worker'}))
        logging.info(f"Connected to server at {self.host}:{self.port}")

    def start_working(self):
        """Start processing tasks from the server."""
        while True:
            try:
                # Request and process tasks
                response = deserialize_message(self.socket)
                
                if response['status'] == 'no_task':
                    logging.info("No tasks available. Waiting...")
                    time.sleep(1)  # Wait before requesting again
                    continue
                
                if response['status'] == 'task_available':
                    subtask = response['subtask']
                    start_time = time.time()
                    
                    # Process the subtask
                    start, end = subtask['range']
                    result = calculate_squares_sum(start, end)
                    
                    # Send result back
                    self.socket.sendall(serialize_message({
                        'task_id': subtask['task_id'],
                        'subtask_index': subtask['subtask_index'],
                        'result': result
                    }))
                    
                    processing_time = time.time() - start_time
                    logging.info(
                        f"Completed subtask {subtask['subtask_index']} of task {subtask['task_id']} "
                        f"in {processing_time:.2f} seconds"
                    )
                
            except socket.timeout:
                logging.error("Connection timed out. Reconnecting...")
                self.reconnect()
            except ConnectionError as e:
                logging.error(f"Connection error: {e}. Reconnecting...")
                self.reconnect()
            except Exception as e:
                logging.error(f"Error processing task: {e}")
                break

    def reconnect(self):
        """Attempt to reconnect to the server."""
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect()
                logging.info("Successfully reconnected to server")
                return
            except Exception as e:
                attempt += 1
                wait_time = min(30, 2 ** attempt)  # Exponential backoff
                logging.error(f"Reconnection attempt {attempt} failed: {e}. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
        
        logging.error("Failed to reconnect after maximum attempts. Shutting down...")
        raise ConnectionError("Maximum reconnection attempts exceeded")

    def close(self):
        """Close the connection."""
        self.socket.close()

if __name__ == '__main__':
    worker = Worker()
    try:
        worker.connect()
        worker.start_working()
    except KeyboardInterrupt:
        logging.info("Worker shutting down...")
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        worker.close() 