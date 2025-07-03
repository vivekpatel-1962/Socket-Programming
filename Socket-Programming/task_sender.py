import socket
import json
import uuid
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



class TaskSender:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """Connect to the server."""
        self.socket.connect((self.host, self.port))
        # Identify as task sender
        self.send_message({'type': 'task_sender'})
        logging.info(f"Connected to server at {self.host}:{self.port}")

    def send_task(self, start: int, end: int, num_subtasks: int = 10):
        """Send a task to the server."""
        task_id = str(uuid.uuid4())
        task_data = {
            'task_id': task_id,
            'range': (start, end),
            'num_subtasks': num_subtasks
        }
        
        self.send_message(task_data)
        logging.info(f"Sent task {task_id} with range {start}-{end}")
        
        # Wait for result
        result = self.receive_message()
        if result['status'] == 'completed':
            logging.info(f"Task {task_id} completed. Result: {result['result']}")
            return result['result']
        else:
            logging.error(f"Task failed: {result}")
            return None

    def send_message(self, message: dict):
        """Send a message to the server."""
        message_bytes = json.dumps(message).encode('utf-8')
        message_length = len(message_bytes).to_bytes(4, byteorder='big')
        self.socket.sendall(message_length + message_bytes)

    def receive_message(self) -> dict:
        """Receive a message from the server."""
        message_length_bytes = self.socket.recv(4)
        message_length = int.from_bytes(message_length_bytes, byteorder='big')
        message_bytes = self.socket.recv(message_length)
        return json.loads(message_bytes.decode('utf-8'))

    def close(self):
        """Close the connection."""
        self.socket.close()

if __name__ == '__main__':
    # Example: Calculate sum of squares from 1 to 1,000,000
    sender = TaskSender()
    try:
        sender.connect()
        result = sender.send_task(1, 1_000_000, 10)
        print(f"Sum of squares from 1 to 1,000,000: {result}")
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        sender.close() 
