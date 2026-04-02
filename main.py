"""
Main entry point for the 4-agent system.
Starts the manager which coordinates all agents and a web dashboard.
"""
import threading
import time
import os
from queue import Queue
from manager_agent import ManagerAgent
from web_dashboard import WebDashboard
from agent1 import Agent1
from agent2 import Agent2
from agent3 import Agent3
from agent4 import Agent4
from war_shared_state import WarSharedState
from war_btc_agent import WarBTCAgent
from war_sp500_agent import WarSP500Agent
from war_oil_agent import WarOilAgent
from war_news_agent import WarNewsAgent
from war_telegram_agent import WarTelegramAgent
from war_fear_greed_agent import WarFearGreedAgent


def main():
    # Create message queues
    message_queue = Queue()  # For agents to post messages
    dashboard_queue = Queue()  # For dashboard to consume messages
    
    # Create and start web dashboard
    dashboard = WebDashboard(dashboard_queue, port=int(os.environ.get('PORT', 5000)))
    
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
    
    # War Monitor team — shared state connects all agents
    war_state = WarSharedState()

    # Extended market + ops agents (also use war_state)
    manager.register_agent("WarGoldAgent",      Agent1(war_state))
    manager.register_agent("WarGasAgent",       Agent2(war_state))
    manager.register_agent("WarDashboardAgent", Agent3(war_state))
    manager.register_agent("WarWorkflowManager", Agent4(war_state))

    manager.register_agent("WarFearGreedAgent", WarFearGreedAgent(war_state))
    manager.register_agent("WarBTCAgent",      WarBTCAgent(war_state))
    manager.register_agent("WarSP500Agent",    WarSP500Agent(war_state))
    manager.register_agent("WarOilAgent",      WarOilAgent(war_state))
    manager.register_agent("WarNewsAgent",     WarNewsAgent(war_state))
    manager.register_agent("WarTelegramAgent", WarTelegramAgent(war_state))
    
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
