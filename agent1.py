"""
Agent 1 - Task Processing Agent
Processes and logs tasks from a queue.
"""
import time
import threading


class Agent1:
    def __init__(self):
        self.name = "Agent1"
        self.interval = 5  # Run every 5 seconds
    
    def run(self, message_queue):
        """Main agent loop."""
        print(f"[{self.name}] Started")
        counter = 0
        
        while True:
            try:
                counter += 1
                message = {
                    "agent": self.name,
                    "type": "task_status",
                    "data": f"Task batch {counter} processed",
                    "timestamp": time.time()
                }
                message_queue.put(message)
                time.sleep(self.interval)
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                time.sleep(self.interval)
