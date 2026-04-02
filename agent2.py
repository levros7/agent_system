"""
Agent 2 - Data Collection Agent
Collects and aggregates data from various sources.
"""
import time
import random


class Agent2:
    def __init__(self):
        self.name = "Agent2"
        self.interval = 8  # Run every 8 seconds
    
    def run(self, message_queue):
        """Main agent loop."""
        print(f"[{self.name}] Started")
        
        while True:
            try:
                # Simulate data collection
                data_points = random.randint(10, 50)
                message = {
                    "agent": self.name,
                    "type": "data_collection",
                    "data": f"Collected {data_points} data points",
                    "timestamp": time.time()
                }
                message_queue.put(message)
                time.sleep(self.interval)
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                time.sleep(self.interval)
