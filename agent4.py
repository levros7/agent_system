"""
Agent 4 - Analytics Agent
Analyzes trends and generates reports.
"""
import time


class Agent4:
    def __init__(self):
        self.name = "Agent4"
        self.interval = 12  # Run every 12 seconds
    
    def run(self, message_queue):
        """Main agent loop."""
        print(f"[{self.name}] Started")
        report_count = 0
        
        while True:
            try:
                report_count += 1
                message = {
                    "agent": self.name,
                    "type": "analytics",
                    "data": f"Generated report #{report_count}",
                    "timestamp": time.time()
                }
                message_queue.put(message)
                time.sleep(self.interval)
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                time.sleep(self.interval)
