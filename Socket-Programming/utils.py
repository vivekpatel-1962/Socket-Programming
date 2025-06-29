import json
from typing import Tuple, List, Dict, Any
import socket
import time


def split_range(start: int, end: int, num_parts: int) -> List[Tuple[int, int]]:
    """Split a numeric range into approximately equal parts."""
    chunk_size = (end - start + 1) // num_parts
    ranges = []
    
    for i in range(num_parts):
        chunk_start = start + i * chunk_size
        chunk_end = chunk_start + chunk_size - 1 if i < num_parts - 1 else end
        ranges.append((chunk_start, chunk_end))
    
    return ranges

def serialize_message(message: Dict[str, Any]) -> bytes:
    """Serialize a message to bytes with length prefix."""
    message_bytes = json.dumps(message).encode('utf-8')
    message_length = len(message_bytes).to_bytes(4, byteorder='big')
    return message_length + message_bytes

def deserialize_message(socket: socket.socket) -> Dict[str, Any]:
    """Deserialize a message from a socket with timeout handling."""
    message_length_bytes = socket.recv(4)
    if not message_length_bytes:
        raise ConnectionError("Connection closed by peer")
    
    message_length = int.from_bytes(message_length_bytes, byteorder='big')
    message_bytes = socket.recv(message_length)
    if not message_bytes:
        raise ConnectionError("Connection closed by peer")
    
    return json.loads(message_bytes.decode('utf-8'))

def calculate_squares_sum(start: int, end: int) -> int:
    """Calculate sum of squares for a range of numbers."""
    return sum(i * i for i in range(start, end + 1))

class TaskTimeout(Exception):
    """Exception raised when a task times out."""
    pass

class TaskResult:
    """Class to track task results and status."""
    def __init__(self, task_id: str, subtask_index: int):
        self.task_id = task_id
        self.subtask_index = subtask_index
        self.result = None
        self.attempts = 0
        self.max_attempts = 3
        self.start_time = None
        self.timeout = 30  # seconds
        
    def start(self):
        """Mark task as started."""
        self.start_time = time.time()
        self.attempts += 1
        
    def is_timed_out(self) -> bool:
        """Check if task has timed out."""
        if self.start_time is None:
            return False
        return time.time() - self.start_time > self.timeout
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.attempts < self.max_attempts 
