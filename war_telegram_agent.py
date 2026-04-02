"""
War Telegram Agent — monitors shared state and sends alerts + daily briefings.
Features: price alerts, ceasefire detection, agent health monitoring, channel broadcast.
"""
import time
import urllib.request
import json
import os
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN  = os.getenv('TELEGRAM_BOT_TOKEN', '8619883125:AAFUcPGAecAqFVmRz3c7vr5uO5YY5qx9m2s')
TELEGRAM_CHAT_ID    = os.getenv('TELEGRAM_CHAT_ID',    '603046431')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')  # e.g. @WarMonitorChannel
ALERT_THRESHOLD     = 2.0
CHECK_INTERVAL      = 30
HEALTH_THRESHOLD    = 300   # 5 minutes silence = unhealthy
WAR_AGENTS          = ['WarBTCAgent', 'WarSP500Agent', 'WarOilAgent', 'WarNewsAgent']

WAR_START = datetime(2026, 2, 28, tzinfo=timezone.utc)


def send_telegram(text, chat_id=None):
    targets = [t for t in [chat_id or TELEGRAM_CHAT_ID, TELEGRAM_CHANNEL_ID] if t]
    for target in targets:
        try:
            body = json.dumps({'chat_id': target, 'text': text, 'parse_mode': 'HTML'}).encode()
            req  = urllib.request.Request(
                f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                data=body, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=8)
        except Exception as e:
            print(f'[WarTelegramAgent] Telegram error ({target}): {e}')


class WarTelegramAgent:
    def __init__(self, shared_state):
        self.name  = 'WarTelegramAgent'
        self.state = shared_state
        self._last_headline       = None
        self._ceasefire_alerted   = False
        self._alerted_down        = set()   # agents already alerted as down

    def _format_briefing(self, snap):
        sign = lambda n: '▲' if n and n >= 0 else '▼'
        fmt  = lambda n: f'${n:,.2f}' if n else 'N/A'
        chg  = lambda n: f'{sign(n)}{abs(n):.2f}%' if n is not None else '—'
        status = '🟢 CEASEFIRE REPORTED' if snap.get('ceasefire') else '🔴 ACTIVE'
        return (
            f'🚨 <b>WAR MONITOR — DAY {snap["war_day"]}</b>\n'
            f'📅 {datetime.now(timezone.utc).strftime("%b %d, %Y  %H:%M UTC")}\n\n'
            f'⚔️ <b>2026 Iran War</b>\n'
            f'Status: {status}  |  Hormuz: CLOSED\n\n'
            f'📈 <b>MARKETS</b>\n'
            f'₿ Bitcoin:  {fmt(snap["btc"])}  {chg(snap["btc_change"])}\n'
            f'📊 S&P 500: {fmt(snap["sp500"])}  {chg(snap["sp500_change"])}\n'
            f'🛢 WTI Oil: {fmt(snap["oil"])}  {chg(snap["oil_change"])}\n\n'
            f'🎯 Missiles (2026): ~500+  |  Intercepted: ~90%\n\n'
            f'🌐 <a href="https://vigilant-forgiveness-production-6c0f.up.railway.app">Live Dashboard</a>'
        )

    def run(self, message_queue):
        print(f'[{self.name}] Started — monitoring every {CHECK_INTERVAL}s')

        while True:
            try:
                snap = self.state.get_snapshot()
                self.state.ping_agent(self.name)

                # ── Price spike alerts ─────────────────────────────────
                for ticker, price, change, label in [
                    ('btc',   snap['btc'],   snap['btc_change'],   'Bitcoin'),
                    ('sp500', snap['sp500'], snap['sp500_change'], 'S&P 500'),
                    ('oil',   snap['oil'],   snap['oil_change'],   'WTI Crude Oil'),
                ]:
                    if price is None:
                        continue
                    alerted, move = self.state.should_alert(ticker, price, ALERT_THRESHOLD)
                    if alerted:
                        direction = '📈 SURGE' if move > 0 else '📉 DROP'
                        send_telegram(
                            f'⚠️ <b>MARKET ALERT — {label}</b>\n'
                            f'{direction} {abs(move):.2f}% move\n'
                            f'Price: ${price:,.2f}  |  24h: {change:+.2f}%\n'
                            f'🌐 War Day {snap["war_day"]}'
                        )
                        message_queue.put({'agent': self.name, 'type': 'alert_sent',
                                           'data': f'ALERT: {label} {direction} {abs(move):.2f}%',
                                           'timestamp': time.time()})

                # ── Ceasefire alert ────────────────────────────────────
                if snap.get('ceasefire') and not self._ceasefire_alerted:
                    self._ceasefire_alerted = True
                    send_telegram(
                        f'🕊️ <b>CEASEFIRE SIGNAL DETECTED</b>\n\n'
                        f'{snap.get("ceasefire_headline", "")}\n\n'
                        f'War Day {snap["war_day"]} — monitoring for confirmation.\n'
                        f'🌐 <a href="https://vigilant-forgiveness-production-6c0f.up.railway.app">Dashboard</a>'
                    )
                    message_queue.put({'agent': self.name, 'type': 'ceasefire_alert',
                                       'data': 'Ceasefire signal sent to Telegram',
                                       'timestamp': time.time()})
                elif not snap.get('ceasefire'):
                    self._ceasefire_alerted = False

                # ── Breaking news alert ────────────────────────────────
                news = self.state.get_news()
                if news:
                    top = news[0]
                    if top['title'] != self._last_headline:
                        self._last_headline = top['title']
                        send_telegram(
                            f'📰 <b>BREAKING — WAR UPDATE</b>\n\n'
                            f'{top["title"]}\n\n'
                            f'<i>{top["source"]} · {top["date"]}</i>\n'
                            f'<a href="{top["url"]}">Read more</a>'
                        )
                        message_queue.put({'agent': self.name, 'type': 'news_alert',
                                           'data': f'Sent: {top["title"][:80]}',
                                           'timestamp': time.time()})

                # ── Agent health monitoring ────────────────────────────
                silent = self.state.get_silent_agents(HEALTH_THRESHOLD)
                for agent in silent:
                    if agent not in self._alerted_down:
                        self._alerted_down.add(agent)
                        send_telegram(
                            f'🔴 <b>AGENT DOWN — {agent}</b>\n'
                            f'No activity for >{HEALTH_THRESHOLD//60} minutes.\n'
                            f'War monitoring may be degraded.'
                        )
                        message_queue.put({'agent': self.name, 'type': 'health_alert',
                                           'data': f'AGENT DOWN: {agent}',
                                           'timestamp': time.time()})
                # Clear recovery
                for agent in list(self._alerted_down):
                    if agent not in silent:
                        self._alerted_down.discard(agent)
                        send_telegram(f'🟢 <b>AGENT RECOVERED — {agent}</b>\nBack online.')

                # ── Daily briefing ─────────────────────────────────────
                if self.state.should_send_daily_briefing():
                    send_telegram(self._format_briefing(snap))
                    message_queue.put({'agent': self.name, 'type': 'daily_briefing',
                                       'data': f'Daily briefing sent — Day {snap["war_day"]}',
                                       'timestamp': time.time()})

            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error',
                                   'data': str(e), 'timestamp': time.time()})

            time.sleep(CHECK_INTERVAL)
