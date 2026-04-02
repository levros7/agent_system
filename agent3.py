"""
Agent 3 - Monitoring Agent
Monitors system health and alerts.
"""
import time
import random


class Agent3:
    def __init__(self):
        self.name = "Agent3"
        self.interval = 10  # Run every 10 seconds
    
    def run(self, message_queue):
        """Main agent loop."""
        print(f"[{self.name}] Started")
        status_values = ["healthy", "warning", "critical"]
        
        while True:
            try:
                status = random.choice(status_values)
                message = {
                    "agent": self.name,
                    "type": "health_check",
                    "data": f"System status: {status}",
                    "timestamp": time.time()
                }
                message_queue.put(message)
                time.sleep(self.interval)
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                time.sleep(self.interval)
