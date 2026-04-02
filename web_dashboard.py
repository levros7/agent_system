"""
Web Dashboard for the 4-Agent System
Provides a real-time web interface to monitor all agents.
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
from collections import deque
from datetime import datetime


class WebDashboard:
    def __init__(self, message_queue, port=5000):
        self.app = Flask(__name__)
        CORS(self.app)
        self.port = port
        self.message_queue = message_queue
        
        # Store last N messages for history
        self.message_history = deque(maxlen=100)
        
        # Agent status tracking
        self.agent_status = {
            "Agent1": {"running": True, "last_update": None, "message_count": 0},
            "Agent2": {"running": True, "last_update": None, "message_count": 0},
            "Agent3": {"running": True, "last_update": None, "message_count": 0},
            "Agent4": {"running": True, "last_update": None, "message_count": 0}
        }
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self):
        """Set up Flask routes"""
        
        @self.app.route('/')
        def index():
            return self.get_dashboard_html()
        
        @self.app.route('/api/status')
        def get_status():
            """Return agent status"""
            return jsonify(self.agent_status)
        
        @self.app.route('/api/history')
        def get_history():
            """Return message history"""
            return jsonify(list(self.message_history))
        
        @self.app.route('/api/agent/<agent_name>/toggle')
        def toggle_agent(agent_name):
            """Toggle agent on/off"""
            if agent_name in self.agent_status:
                self.agent_status[agent_name]["running"] = not self.agent_status[agent_name]["running"]
                status = "enabled" if self.agent_status[agent_name]["running"] else "disabled"
                return jsonify({"success": True, "agent": agent_name, "status": status})
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        @self.app.route('/api/clear-history', methods=['POST'])
        def clear_history():
            """Clear message history"""
            self.message_history.clear()
            return jsonify({"success": True})
    
    def process_messages(self):
        """Process messages from the queue and update caches."""
        while True:
            try:
                message = self.message_queue.get(timeout=1)
                
                # Store in history
                self.message_history.append({
                    "timestamp": message.get("timestamp"),
                    "agent": message.get("agent"),
                    "type": message.get("type"),
                    "data": message.get("data")
                })
                
                # Update agent status
                agent_name = message.get("agent")
                if agent_name in self.agent_status:
                    self.agent_status[agent_name]["last_update"] = datetime.now().isoformat()
                    self.agent_status[agent_name]["message_count"] += 1
                    
            except:
                pass
    
    def run(self):
        """Start the Flask server."""
        self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
    
    def get_dashboard_html(self):
        """Return the dashboard HTML."""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Agent System Dashboard</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                
                header {
                    background: rgba(255, 255, 255, 0.95);
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                
                h1 {
                    color: #333;
                    font-size: 28px;
                    margin-bottom: 10px;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin-top: 15px;
                }
                
                .stat-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }
                
                .stat-label {
                    font-size: 12px;
                    opacity: 0.8;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                
                .stat-value {
                    font-size: 24px;
                    font-weight: bold;
                    margin-top: 5px;
                }
                
                .agents-section {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }
                
                .agent-card {
                    background: rgba(255, 255, 255, 0.95);
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: transform 0.3s, box-shadow 0.3s;
                }
                
                .agent-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
                }
                
                .agent-card.disabled {
                    opacity: 0.5;
                    background: rgba(255, 255, 255, 0.7);
                }
                
                .agent-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .agent-title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                }
                
                .agent-toggle {
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: background 0.3s;
                }
                
                .agent-toggle:hover {
                    background: #764ba2;
                }
                
                .agent-toggle.off {
                    background: #ccc;
                }
                
                .agent-info {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 15px;
                }
                
                .info-item {
                    background: #f5f5f5;
                    padding: 12px;
                    border-radius: 6px;
                }
                
                .info-label {
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 4px;
                }
                
                .info-value {
                    font-size: 16px;
                    font-weight: bold;
                    color: #333;
                }
                
                .info-value.time {
                    font-size: 13px;
                    color: #999;
                }
                
                .status-badge {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #4caf50;
                    margin-right: 6px;
                }
                
                .status-badge.offline {
                    background: #f44336;
                }
                
                .messages-section {
                    background: rgba(255, 255, 255, 0.95);
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                
                .messages-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .messages-header h2 {
                    color: #333;
                    font-size: 20px;
                }
                
                .clear-btn {
                    background: #f44336;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: background 0.3s;
                }
                
                .clear-btn:hover {
                    background: #d32f2f;
                }
                
                .message-log {
                    background: #1e1e1e;
                    color: #d4d4d4;
                    padding: 15px;
                    border-radius: 6px;
                    max-height: 400px;
                    overflow-y: auto;
                    font-family: 'Monaco', 'Courier New', monospace;
                    font-size: 12px;
                    line-height: 1.6;
                }
                
                .log-entry {
                    margin-bottom: 8px;
                    padding: 8px;
                    border-left: 3px solid #667eea;
                    padding-left: 12px;
                }
                
                .log-timestamp {
                    color: #858585;
                }
                
                .log-agent {
                    color: #4ec9b0;
                    font-weight: bold;
                }
                
                .log-type {
                    color: #ce9178;
                }
                
                .log-data {
                    color: #9cdcfe;
                }
                
                .empty-state {
                    text-align: center;
                    color: #999;
                    padding: 30px;
                    font-size: 14px;
                }
                
                @media (max-width: 768px) {
                    header h1 {
                        font-size: 20px;
                    }
                    
                    .stats-grid {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .agents-section {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🤖 Agent System Dashboard</h1>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Active Agents</div>
                            <div class="stat-value" id="active-count">4</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Messages</div>
                            <div class="stat-value" id="message-count">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Last Update</div>
                            <div class="stat-value" id="last-update">--:--</div>
                        </div>
                    </div>
                </header>
                
                <div class="agents-section" id="agents-container"></div>
                
                <div class="messages-section">
                    <div class="messages-header">
                        <h2>📋 Message Log</h2>
                        <button class="clear-btn" onclick="clearHistory()">Clear History</button>
                    </div>
                    <div class="message-log" id="message-log">
                        <div class="empty-state">Waiting for messages...</div>
                    </div>
                </div>
            </div>
            
            <script>
                const AGENTS = ["Agent1", "Agent2", "Agent3", "Agent4"];
                let messageCount = 0;
                
                function formatTime(timestamp) {
                    if (!timestamp) return "--:--";
                    try {
                        const date = new Date(timestamp);
                        return date.toLocaleTimeString();
                    } catch {
                        return timestamp;
                    }
                }
                
                function updateAgentStatus() {
                    fetch('/api/status')
                        .then(r => r.json())
                        .then(data => {
                            const container = document.getElementById('agents-container');
                            let activeCount = 0;
                            
                            AGENTS.forEach(agent => {
                                const status = data[agent];
                                if (status.running) activeCount++;
                                
                                let card = document.getElementById(`card-${agent}`);
                                if (!card) {
                                    card = document.createElement('div');
                                    card.id = `card-${agent}`;
                                    card.className = 'agent-card';
                                    container.appendChild(card);
                                }
                                
                                const running = status.running;
                                card.className = `agent-card ${!running ? 'disabled' : ''}`;
                                
                                card.innerHTML = `
                                    <div class="agent-header">
                                        <span class="agent-title">
                                            <span class="status-badge ${!running ? 'offline' : ''}"></span>
                                            ${agent}
                                        </span>
                                        <button class="agent-toggle ${!running ? 'off' : ''}" 
                                                onclick="toggleAgent('${agent}')">
                                            ${running ? 'ON' : 'OFF'}
                                        </button>
                                    </div>
                                    <div class="agent-info">
                                        <div class="info-item">
                                            <div class="info-label">Messages Sent</div>
                                            <div class="info-value">${status.message_count}</div>
                                        </div>
                                        <div class="info-item">
                                            <div class="info-label">Last Update</div>
                                            <div class="info-value time">${formatTime(status.last_update)}</div>
                                        </div>
                                    </div>
                                `;
                            });
                            
                            document.getElementById('active-count').textContent = activeCount;
                        });
                }
                
                function updateMessageLog() {
                    fetch('/api/history')
                        .then(r => r.json())
                        .then(messages => {
                            const log = document.getElementById('message-log');
                            messageCount = messages.length;
                            document.getElementById('message-count').textContent = messageCount;
                            
                            if (messages.length === 0) {
                                log.innerHTML = '<div class="empty-state">Waiting for messages...</div>';
                                return;
                            }
                            
                            log.innerHTML = messages.map(msg => {
                                const time = formatTime(msg.timestamp);
                                return `
                                    <div class="log-entry">
                                        <span class="log-timestamp">[${time}]</span>
                                        <span class="log-agent">${msg.agent}</span>
                                        <span class="log-type">(${msg.type})</span>
                                        <span class="log-data">: ${msg.data}</span>
                                    </div>
                                `;
                            }).reverse().join('');
                            
                            // Update last update time
                            const lastMsg = messages[messages.length - 1];
                            document.getElementById('last-update').textContent = formatTime(lastMsg.timestamp);
                        });
                }
                
                function toggleAgent(agent) {
                    fetch(`/api/agent/${agent}/toggle`)
                        .then(r => r.json())
                        .then(data => {
                            if (data.success) {
                                updateAgentStatus();
                            }
                        });
                }
                
                function clearHistory() {
                    if (confirm('Clear all message history?')) {
                        fetch('/api/clear-history', { method: 'POST' })
                            .then(r => r.json())
                            .then(data => {
                                if (data.success) {
                                    updateMessageLog();
                                }
                            });
                    }
                }
                
                // Initial load
                updateAgentStatus();
                updateMessageLog();
                
                // Auto-refresh every 2 seconds
                setInterval(updateAgentStatus, 2000);
                setInterval(updateMessageLog, 2000);
            </script>
        </body>
        </html>
        '''
