"""
Agent4 — War Intel Summary Agent
Every 30 minutes, compiles a full war intelligence summary from shared state
and sends it to Telegram + posts to the activity feed.
"""
import time
import urllib.request
import json
import os
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8619883125:AAFUcPGAecAqFVmRz3c7vr5uO5YY5qx9m2s')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID', '603046431')
WAR_START          = datetime(2026, 2, 28, tzinfo=timezone.utc)
SUMMARY_INTERVAL   = 1800  # 30 minutes


def _send_telegram(text):
    try:
        body = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}).encode()
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            data=body, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print(f'[WarIntelAgent] Telegram error: {e}')


def _fmt(n, decimals=2):
    return f'${n:,.{decimals}f}' if n is not None else 'N/A'

def _chg(n):
    if n is None: return '—'
    arrow = '▲' if n >= 0 else '▼'
    return f'{arrow} {abs(n):.2f}%'


class Agent4:
    def __init__(self, shared_state=None):
        self.name = 'WarIntelAgent'
        self.interval = SUMMARY_INTERVAL
        self.state = shared_state
        self._summary_count = 0

    def run(self, message_queue):
        print(f'[{self.name}] Started — sending intel summaries every {self.interval//60}min')
        # Wait 2 minutes on startup so other agents have time to fetch data first
        time.sleep(120)

        while True:
            try:
                if self.state:
                    self.state.ping_agent(self.name)
                    snap = self.state.get_snapshot()
                    news = self.state.get_news()

                    self._summary_count += 1
                    war_day = snap['war_day']
                    ceasefire = snap.get('ceasefire', False)
                    status_line = '🟢 CEASEFIRE REPORTED' if ceasefire else '🔴 ACTIVE'

                    top_headline = news[0]['title'] if news else 'No recent headlines'

                    summary = (
                        f'📋 <b>WAR INTEL SUMMARY #{self._summary_count}</b>\n'
                        f'📅 {datetime.now(timezone.utc).strftime("%b %d  %H:%M UTC")}  |  Day {war_day}\n\n'
                        f'⚔️ <b>Status:</b> {status_line}\n'
                        f'🚧 Strait of Hormuz: CLOSED\n\n'
                        f'📈 <b>MARKETS</b>\n'
                        f'₿  BTC:   {_fmt(snap["btc"])}  {_chg(snap["btc_change"])}\n'
                        f'📊 SP500: {_fmt(snap["sp500"])}  {_chg(snap["sp500_change"])}\n'
                        f'🛢 Oil:   {_fmt(snap["oil"])}  {_chg(snap["oil_change"])}\n'
                        f'🥇 Gold:  {_fmt(snap.get("gold"))}  {_chg(snap.get("gold_change"))}\n'
                        f'🔥 Gas:   {_fmt(snap.get("gas"), 3)}  {_chg(snap.get("gas_change"))}\n\n'
                        f'📰 <b>Latest:</b> {top_headline}\n\n'
                        f'🌐 <a href="https://vigilant-forgiveness-production-6c0f.up.railway.app">Live Dashboard</a>'
                    )

                    _send_telegram(summary)

                    message_queue.put({
                        'agent': self.name,
                        'type': 'intel_summary',
                        'data': f'Summary #{self._summary_count} sent — Day {war_day} | '
                                f'BTC {_fmt(snap["btc"])} | Oil {_fmt(snap["oil"])}',
                        'timestamp': time.time(),
                    })
                else:
                    message_queue.put({
                        'agent': self.name,
                        'type': 'intel_summary',
                        'data': 'No shared state connected',
                        'timestamp': time.time(),
                    })

            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error', 'data': str(e), 'timestamp': time.time()})

            time.sleep(self.interval)
