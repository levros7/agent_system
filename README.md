# 4-Agent System

A multi-agent event-driven system with 4 specialized agents that communicate via a message queue.

## Architecture

- **Agent1**: Task Processing - Processes batches of tasks
- **Agent2**: Data Collection - Collects and aggregates data points
- **Agent3**: Monitoring - Performs health checks
- **Agent4**: Analytics - Generates reports and analytics

Each agent runs on its own interval and sends messages to a central queue that the Manager Agent monitors and displays.

## Quick Start

```bash
# Navigate to project
cd /Users/levrosenblum/agent_system

# Run the system
python main.py
```

## Project Structure

```
main.py              # Entry point
manager_agent.py     # Coordinates all agents
agent1.py            # Task Processing Agent
agent2.py            # Data Collection Agent
agent3.py            # Monitoring Agent
agent4.py            # Analytics Agent
requirements.txt     # Dependencies (none required)
```

## How It Works

1. `main.py` starts the system and registers all 4 agents
2. `ManagerAgent` starts each agent in its own daemon thread
3. Each agent runs independently on its own interval
4. Agents put messages on a shared queue
5. Manager monitors the queue and displays all messages
6. Agents continue running until Ctrl+C is pressed

## Customization

Each agent can be customized by:
- Changing the `interval` value (seconds between runs)
- Modifying the `data` field in messages
- Adding new logic to the `run()` method
