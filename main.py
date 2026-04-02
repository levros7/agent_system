"""
Main entry point for the 4-agent system.
Starts the manager which coordinates all agents and a web dashboard.
"""
import threading
import time
from queue import Queue
from manager_agent import ManagerAgent
from web_dashboard import WebDashboard
from agent1 import Agent1
from agent2 import Agent2
from agent3 import Agent3
from agent4 import Agent4
from war_monitor_agent import WarMonitorAgent


def main():
    # Create message queues
    message_queue = Queue()  # For agents to post messages
    dashboard_queue = Queue()  # For dashboard to consume messages
    
    # Create and start web dashboard
    dashboard = WebDashboard(dashboard_queue, port=5000)
    
    # Start dashboard message processor
    processor_thread = threading.Thread(target=dashboard.process_messages, daemon=True)
    processor_thread.start()
    
    # Start Flask server
    dashboard_thread = threading.Thread(target=dashboard.run, daemon=True)
    dashboard_thread.start()
    
    print("=" * 50)
    print("🌐 Web Dashboard running at http://localhost:5000")
    print("=" * 50)
    
    # Create manager
    manager = ManagerAgent(message_queue, dashboard_queue)
    
    # Register agents
    manager.register_agent("Agent1", Agent1())
    manager.register_agent("Agent2", Agent2())
    manager.register_agent("Agent3", Agent3())
    manager.register_agent("Agent4", Agent4())
    manager.register_agent("WarMonitorAgent", WarMonitorAgent())
    
    # Start manager (runs all agents as daemon threads)
    manager_thread = threading.Thread(target=manager.run, daemon=True)
    manager_thread.start()
    
    print("✓ Agent system started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✓ Shutting down...")


if __name__ == "__main__":
    main()
