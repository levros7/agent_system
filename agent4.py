"""
Agent4 — War Workflow Manager
Manages and coordinates all other agents in the war monitor system.

Responsibilities:
- Monitors health of all 8 agents every 30s
- Detects and reports agent failures to Telegram
- Watches for correlated market anomalies (e.g. Oil + Gas both spiking = Hormuz alert)
- Sends a full system status report to Telegram every 30 minutes
- Logs all workflow decisions to the dashboard activity feed
"""
import time
import urllib.request
import json
import os
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8619883125:AAFUcPGAecAqFVmRz3c7vr5uO5YY5qx9m2s')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID', '603046431')
CHECK_INTERVAL     = 30    # health check every 30s
REPORT_INTERVAL    = 1800  # full status report every 30min
HEALTH_THRESHOLD   = 180   # agent silent >3min = issue

ALL_AGENTS = [
    'WarBTCAgent', 'WarSP500Agent', 'WarOilAgent',
    'WarNewsAgent', 'WarTelegramAgent',
    'WarGoldAgent', 'WarGasAgent', 'WarDashboardAgent',
]


def _send_telegram(text):
    try:
        body = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}).encode()
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            data=body, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print(f'[WarWorkflowManager] Telegram error: {e}')


def _fmt(n, d=2):
    return f'${n:,.{d}f}' if n is not None else 'N/A'

def _chg(n):
    if n is None: return '—'
    return f'{"▲" if n >= 0 else "▼"} {abs(n):.2f}%'


class Agent4:
    def __init__(self, shared_state=None):
        self.name  = 'WarWorkflowManager'
        self.state = shared_state
        self._downed_agents  = set()   # agents currently flagged as down
        self._last_report_at = 0
        self._report_count   = 0
        self._last_hormuz_alert = 0    # prevent repeated Hormuz alerts

    # ── Helpers ──────────────────────────────────────────────────────────

    def _post(self, queue, msg_type, data):
        queue.put({'agent': self.name, 'type': msg_type, 'data': data, 'timestamp': time.time()})

    # ── Health check ─────────────────────────────────────────────────────

    def _check_agent_health(self, queue):
        silent = self.state.get_silent_agents(HEALTH_THRESHOLD)

        # New failures
        for agent in silent:
            if agent not in self._downed_agents:
                self._downed_agents.add(agent)
                mins = HEALTH_THRESHOLD // 60
                _send_telegram(
                    f'🔴 <b>WORKFLOW ALERT — Agent Down</b>\n'
                    f'<b>{agent}</b> has been silent for >{mins} minutes.\n'
                    f'War monitoring may be degraded.'
                )
                self._post(queue, 'agent_down', f'AGENT DOWN: {agent} — silent >{mins}min')

        # Recoveries
        for agent in list(self._downed_agents):
            if agent not in silent:
                self._downed_agents.discard(agent)
                _send_telegram(f'🟢 <b>WORKFLOW — Agent Recovered</b>\n<b>{agent}</b> is back online.')
                self._post(queue, 'agent_recovered', f'RECOVERED: {agent}')

        # All-clear summary to dashboard
        alive  = len(ALL_AGENTS) - len(self._downed_agents)
        status = 'ALL SYSTEMS OPERATIONAL' if not self._downed_agents else f'{len(self._downed_agents)} AGENT(S) DOWN'
        self._post(queue, 'health_check', f'{alive}/{len(ALL_AGENTS)} agents active — {status}')

    # ── Correlated market anomaly detection ──────────────────────────────

    def _check_correlations(self, snap, queue):
        oil_chg = snap.get('oil_change') or 0
        gas_chg = snap.get('gas_change') or 0
        now     = time.time()

        # Oil AND Gas both up >3% → likely Hormuz escalation signal
        if oil_chg > 3 and gas_chg > 3 and (now - self._last_hormuz_alert) > 3600:
            self._last_hormuz_alert = now
            _send_telegram(
                f'⚠️ <b>WORKFLOW — Hormuz Escalation Signal</b>\n\n'
                f'Oil {_chg(oil_chg)} and Gas {_chg(gas_chg)} both spiking.\n'
                f'Possible Strait of Hormuz escalation detected.\n'
                f'🌐 <a href="https://vigilant-forgiveness-production-6c0f.up.railway.app">Dashboard</a>'
            )
            self._post(queue, 'hormuz_signal', f'Hormuz signal: Oil {_chg(oil_chg)} + Gas {_chg(gas_chg)}')

    # ── Full status report ────────────────────────────────────────────────

    def _send_status_report(self, snap, queue):
        self._report_count += 1
        news      = self.state.get_news()
        headline  = news[0]['title'] if news else 'No recent headlines'
        ceasefire = '🟢 CEASEFIRE REPORTED' if snap.get('ceasefire') else '🔴 ACTIVE'
        alive     = len(ALL_AGENTS) - len(self._downed_agents)
        down_list = ', '.join(self._downed_agents) if self._downed_agents else 'None'

        report = (
            f'📋 <b>WORKFLOW STATUS REPORT #{self._report_count}</b>\n'
            f'📅 {datetime.now(timezone.utc).strftime("%b %d  %H:%M UTC")}  |  Day {snap["war_day"]}\n\n'
            f'🤖 <b>AGENT HEALTH</b>\n'
            f'Active: {alive}/{len(ALL_AGENTS)}  |  Down: {down_list}\n\n'
            f'⚔️ <b>WAR STATUS:</b> {ceasefire}\n\n'
            f'📈 <b>MARKETS</b>\n'
            f'₿  BTC:   {_fmt(snap["btc"])}  {_chg(snap["btc_change"])}\n'
            f'📊 SP500: {_fmt(snap["sp500"])}  {_chg(snap["sp500_change"])}\n'
            f'🛢 Oil:   {_fmt(snap["oil"])}  {_chg(snap["oil_change"])}\n'
            f'🥇 Gold:  {_fmt(snap.get("gold"))}  {_chg(snap.get("gold_change"))}\n'
            f'🔥 Gas:   {_fmt(snap.get("gas"), 3)}  {_chg(snap.get("gas_change"))}\n\n'
            f'📰 <b>Latest:</b> {headline}\n\n'
            f'🌐 <a href="https://vigilant-forgiveness-production-6c0f.up.railway.app">Live Dashboard</a>'
        )
        _send_telegram(report)
        self._post(queue, 'status_report',
                   f'Report #{self._report_count} — {alive}/{len(ALL_AGENTS)} agents up | '
                   f'BTC {_fmt(snap["btc"])} | Oil {_fmt(snap["oil"])}')

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self, message_queue):
        print(f'[{self.name}] Started — managing {len(ALL_AGENTS)} agents')
        # Wait 90s on startup so agents have time to register their first ping
        time.sleep(90)

        while True:
            try:
                self.state.ping_agent(self.name)
                snap = self.state.get_snapshot()

                self._check_agent_health(message_queue)
                self._check_correlations(snap, message_queue)

                # Full report every 30 minutes
                if time.time() - self._last_report_at >= REPORT_INTERVAL:
                    self._last_report_at = time.time()
                    self._send_status_report(snap, message_queue)

            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                self._post(message_queue, 'error', str(e))

            time.sleep(CHECK_INTERVAL)
