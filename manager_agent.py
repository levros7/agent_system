"""
Manager Agent - Coordinates all agents and processes messages.
"""
import threading
import time
from datetime import datetime


class ManagerAgent:
    def __init__(self, message_queue, dashboard_queue=None):
        self.message_queue = message_queue
        self.dashboard_queue = dashboard_queue
        self.agents = {}
        self.running = True
    
    def register_agent(self, name, agent):
        """Register an agent to be managed."""
        self.agents[name] = agent
        print(f"[Manager] Registered agent: {name}")
    
    def run(self):
        """Start all registered agents as daemon threads."""
        print("[Manager] Starting all agents...")
        
        # Start each agent in its own thread
        for name, agent in self.agents.items():
            thread = threading.Thread(
                target=agent.run,
                args=(self.message_queue,),
                name=name,
                daemon=True
            )
            thread.start()
        
        # Monitor message queue and display messages
        print("[Manager] Monitoring message queue...")
        while self.running:
            try:
                message = self.message_queue.get(timeout=1)
                self._display_message(message)
            except:
                pass
    
    def _display_message(self, message):
        """Display a message from an agent."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        agent_name = message.get("agent", "Unknown")
        message_type = message.get("type", "message")
        data = message.get("data")
        
        print(f"[{timestamp}] {agent_name} ({message_type}): {data}")
        
        # Forward to dashboard queue if available
        if self.dashboard_queue:
            try:
                self.dashboard_queue.put(message)
            except:
                pass
