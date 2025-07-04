from task_sender import TaskSender
import logging

def main():
    # Create a task sender instance
    sender = TaskSender(host='localhost', port=5000)
    
    try:
        # Connect to the server
        sender.connect()
        
        # Example 1: Sum squares from 1 to 1,000,000
        print("Calculating sum of squares from 1 to 1,000,000...")
        result1 = sender.send_task(1, 1_000_000, num_subtasks=10)
        print(f"Result: {result1:,}")
        
        # Example 2: Sum squares from 1 to 10,000 with more subtasks
        print("\nCalculating sum of squares from 1 to 10,000...")
        result2 = sender.send_task(1, 10_000, num_subtasks=20)
        print(f"Result: {result2:,}")
        
    except ConnectionRefusedError:
        print("Error: Could not connect to the server. Make sure the server is running.")
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        sender.close()


if __name__ == '__main__':
    main() 
