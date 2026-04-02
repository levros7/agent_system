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
            "WarGoldAgent":      {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarGasAgent":       {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarDashboardAgent": {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarWorkflowManager": {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarFearGreedAgent":      {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarMissileTrackerAgent": {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarBTCAgent":        {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarSP500Agent":     {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarOilAgent":       {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarNewsAgent":      {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
            "WarTelegramAgent":  {"running": True, "last_update": None, "message_count": 0, "last_data": "", "last_type": ""},
        }
        self.war_metrics = {}
        self.agent_logs = {name: deque(maxlen=10) for name in self.agent_status}
        
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
        
        @self.app.route('/api/war-metrics')
        def get_war_metrics():
            return jsonify(self.war_metrics)

        @self.app.route('/api/agent-logs')
        def get_agent_logs():
            return jsonify({k: list(v) for k, v in self.agent_logs.items()})

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
                    now = datetime.utcnow().isoformat() + 'Z'
                    self.agent_status[agent_name]["last_update"] = now
                    self.agent_status[agent_name]["message_count"] += 1
                    self.agent_status[agent_name]["last_data"] = message.get("data", "")
                    self.agent_status[agent_name]["last_type"] = message.get("type", "")
                    self.agent_logs[agent_name].append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "type": message.get("type", ""),
                        "data": message.get("data", ""),
                    })
                if "metrics" in message and message.get("agent", "").startswith("War"):
                    if message.get("type") in ("btc_price", "sp500_price", "oil_price"):
                        key = message["agent"].replace("War", "").replace("Agent", "").lower()
                        self.war_metrics[key] = message["metrics"]
                        self.war_metrics["war_day"] = (datetime.now() - datetime(2026, 2, 28)).days + 1
                    
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
                
                <style>
                  @keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }
                  body { background:#080c10; color:#e6edf3; font-family:'SF Mono','Fira Code',monospace; }
                  .section-label { font-size:10px;letter-spacing:3px;color:#8b949e;padding:14px 0 8px;border-bottom:1px solid #21262d;margin-bottom:12px }
                </style>

                <!-- War Monitor Team -->
                <div class="section-label">⚔️ WAR MONITOR TEAM</div>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px;margin-bottom:20px" id="war-agents"></div>

                <!-- Extended War Agents -->
                <div class="section-label">🛰️ EXTENDED INTEL AGENTS</div>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px;margin-bottom:20px" id="sys-agents"></div>

                <!-- Live Activity Feed -->
                <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;overflow:hidden">
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #21262d">
                        <span style="font-size:10px;letter-spacing:3px;color:#8b949e">📡 LIVE ACTIVITY FEED</span>
                        <button onclick="clearHistory()" style="background:#f85149;color:#fff;border:none;padding:4px 12px;border-radius:4px;cursor:pointer;font-size:10px">CLEAR</button>
                    </div>
                    <div id="activity-feed" style="max-height:320px;overflow-y:auto;font-family:monospace;font-size:11px"></div>
                </div>
            </div>
            
            <script>
                const ALL_AGENTS   = ["WarGoldAgent","WarGasAgent","WarDashboardAgent","WarWorkflowManager"];
                const WAR_AGENTS   = ["WarMissileTrackerAgent","WarFearGreedAgent","WarBTCAgent","WarSP500Agent","WarOilAgent","WarNewsAgent","WarTelegramAgent"];
                const AGENT_ICONS  = {
                    WarGoldAgent:"🥇", WarGasAgent:"🔥", WarDashboardAgent:"🌐", WarWorkflowManager:"⚙️",
                    WarMissileTrackerAgent:"🚀", WarFearGreedAgent:"😱", WarBTCAgent:"₿", WarSP500Agent:"📈", WarOilAgent:"🛢",
                    WarNewsAgent:"📰", WarTelegramAgent:"📡"
                };
                const AGENT_DESC = {
                    WarGoldAgent:"Gold Futures · Yahoo Finance", WarGasAgent:"Natural Gas · Yahoo Finance",
                    WarDashboardAgent:"Dashboard Uptime Monitor", WarWorkflowManager:"Manages All 8 Agents · Health + Reports",
                    WarMissileTrackerAgent:"RSS Missile Monitor · Reuters · ToI · CNN · AJZ",
                    WarFearGreedAgent:"Fear & Greed Index · Alternative.me",
                    WarBTCAgent:"Bitcoin · Binance API", WarSP500Agent:"S&P 500 · Yahoo Finance",
                    WarOilAgent:"WTI Oil · Yahoo Finance", WarNewsAgent:"War Headlines · GNews",
                    WarTelegramAgent:"Alerts & Briefings · Telegram"
                };

                let agentLogs = {};
                let lastActivity = {};

                function timeSince(iso) {
                    if (!iso) return 'never';
                    const secs = Math.floor((Date.now() - new Date(iso)) / 1000);
                    if (secs < 5)  return 'just now';
                    if (secs < 60) return secs + 's ago';
                    return Math.floor(secs/60) + 'm ago';
                }

                function typeColor(t) {
                    if (!t) return '#8b949e';
                    if (t.includes('error'))   return '#f85149';
                    if (t.includes('alert') || t.includes('briefing')) return '#d29922';
                    if (t.includes('btc') || t.includes('sp500') || t.includes('oil')) return '#3fb950';
                    if (t.includes('news'))    return '#58a6ff';
                    if (t.includes('telegram')) return '#bc8cff';
                    return '#8b949e';
                }

                function renderAgentCard(agent, status, logs) {
                    const running  = status.running;
                    const isActive = status.last_update && (Date.now() - new Date(status.last_update)) < 5000;
                    const icon     = AGENT_ICONS[agent] || '🤖';
                    const desc     = AGENT_DESC[agent] || '';
                    const logRows  = (logs || []).slice().reverse().map(l => `
                        <div style="display:flex;gap:8px;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                            <span style="color:#555;min-width:56px;font-size:10px">${l.time}</span>
                            <span style="color:${typeColor(l.type)};min-width:80px;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${l.type}</span>
                            <span style="color:#ccc;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${l.data}</span>
                        </div>`).join('') || '<div style="color:#444;font-size:10px;padding:4px 0">No activity yet...</div>';

                    return `
                        <div id="card-${agent}" style="
                            background:#0d1117;border-radius:10px;padding:16px;
                            border:1px solid ${isActive ? typeColor(status.last_type) : '#21262d'};
                            box-shadow:${isActive ? '0 0 12px ' + typeColor(status.last_type) + '44' : 'none'};
                            transition:all 0.4s;
                        ">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                                <div style="display:flex;align-items:center;gap:10px">
                                    <span style="font-size:20px">${icon}</span>
                                    <div>
                                        <div style="font-weight:700;font-size:13px;color:#e6edf3">${agent}</div>
                                        <div style="font-size:10px;color:#8b949e">${desc}</div>
                                    </div>
                                </div>
                                <div style="display:flex;align-items:center;gap:8px">
                                    <div style="
                                        width:8px;height:8px;border-radius:50%;
                                        background:${running ? (isActive ? typeColor(status.last_type) : '#3fb950') : '#f85149'};
                                        box-shadow:${isActive ? '0 0 8px ' + typeColor(status.last_type) : 'none'};
                                        ${isActive ? 'animation:pulse-dot 0.8s ease-in-out infinite' : ''}
                                    "></div>
                                    <button onclick="toggleAgent('${agent}')" style="
                                        background:${running ? '#21262d' : '#f85149'};color:${running ? '#8b949e' : '#fff'};
                                        border:1px solid #30363d;padding:3px 10px;border-radius:4px;
                                        cursor:pointer;font-size:10px;letter-spacing:1px
                                    ">${running ? 'ON' : 'OFF'}</button>
                                </div>
                            </div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
                                <div style="background:#161b22;border-radius:6px;padding:8px;text-align:center">
                                    <div style="font-size:9px;color:#8b949e;letter-spacing:1px">MESSAGES</div>
                                    <div style="font-size:20px;font-weight:700;color:#e6edf3">${status.message_count}</div>
                                </div>
                                <div style="background:#161b22;border-radius:6px;padding:8px;text-align:center">
                                    <div style="font-size:9px;color:#8b949e;letter-spacing:1px">LAST ACTIVE</div>
                                    <div style="font-size:12px;font-weight:600;color:${isActive ? typeColor(status.last_type) : '#8b949e'}">${timeSince(status.last_update)}</div>
                                </div>
                            </div>
                            ${status.last_data ? `<div style="background:#161b22;border-radius:6px;padding:8px;margin-bottom:10px;font-size:11px;color:#3fb950;font-family:monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">▶ ${status.last_data}</div>` : ''}
                            <div style="background:#0a0e13;border-radius:6px;padding:8px;max-height:130px;overflow-y:auto;font-family:monospace">
                                <div style="font-size:9px;color:#555;letter-spacing:1px;margin-bottom:4px">ACTIVITY LOG</div>
                                ${logRows}
                            </div>
                        </div>`;
                }

                function updateDashboard() {
                    Promise.all([
                        fetch('/api/status').then(r => r.json()),
                        fetch('/api/agent-logs').then(r => r.json()),
                        fetch('/api/history').then(r => r.json()),
                    ]).then(([status, logs, history]) => {

                        // Stats
                        const active = Object.values(status).filter(s => s.running).length;
                        document.getElementById('active-count').textContent = active;
                        document.getElementById('message-count').textContent = history.length;
                        if (history.length) {
                            const last = history[history.length - 1];
                            document.getElementById('last-update').textContent =
                                last.timestamp ? new Date(last.timestamp * 1000).toLocaleTimeString() : '--';
                        }

                        // Agent cards — System agents
                        const sysContainer = document.getElementById('sys-agents');
                        sysContainer.innerHTML = ALL_AGENTS.map(a =>
                            renderAgentCard(a, status[a] || {}, logs[a])
                        ).join('');

                        // Agent cards — War Monitor team
                        const warContainer = document.getElementById('war-agents');
                        warContainer.innerHTML = WAR_AGENTS.map(a =>
                            renderAgentCard(a, status[a] || {}, logs[a])
                        ).join('');

                        // Global activity feed
                        const feed = document.getElementById('activity-feed');
                        if (history.length === 0) {
                            feed.innerHTML = '<div style="color:#444;padding:20px;text-align:center">Waiting for activity...</div>';
                        } else {
                            feed.innerHTML = [...history].reverse().map(msg => {
                                const t = msg.timestamp ? new Date(msg.timestamp * 1000).toLocaleTimeString() : '';
                                const c = typeColor(msg.type);
                                return `<div style="display:flex;gap:10px;padding:6px 8px;border-bottom:1px solid #161b22;align-items:flex-start">
                                    <span style="color:#555;font-size:10px;min-width:58px;padding-top:1px">${t}</span>
                                    <span style="color:${c};font-size:10px;min-width:100px;font-weight:600">${msg.agent || ''}</span>
                                    <span style="color:#666;font-size:10px;min-width:90px">${msg.type || ''}</span>
                                    <span style="color:#aaa;font-size:10px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${msg.data || ''}</span>
                                </div>`;
                            }).join('');
                        }
                    }).catch(() => {});
                }

                function toggleAgent(agent) {
                    fetch(`/api/agent/${agent}/toggle`).then(r => r.json()).then(updateDashboard);
                }

                function clearHistory() {
                    if (confirm('Clear all activity history?')) {
                        fetch('/api/clear-history', { method: 'POST' }).then(updateDashboard);
                    }
                }

                updateDashboard();
                setInterval(updateDashboard, 2000);
            </script>
        </body>
        </html>
        '''
