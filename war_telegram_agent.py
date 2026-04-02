"""
War Telegram Agent — monitors shared state and sends alerts + daily briefings.
Reacts to data from BTC, SP500, Oil, and News agents.
"""
import time
import urllib.request
import json
import os
from datetime import datetime, timezone


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8619883125:AAFUcPGAecAqFVmRz3c7vr5uO5YY5qx9m2s')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID',   '603046431')
ALERT_THRESHOLD    = 2.0   # % move to trigger alert
CHECK_INTERVAL     = 30    # seconds between checks

WAR_START = datetime(2026, 2, 28, tzinfo=timezone.utc)


def send_telegram(text, chat_id=TELEGRAM_CHAT_ID):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return
    try:
        body = json.dumps({'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}).encode()
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            data=body,
            headers={'Content-Type': 'application/json'},
        )
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print(f'[WarTelegramAgent] Telegram error: {e}')


class WarTelegramAgent:
    def __init__(self, shared_state):
        self.name  = 'WarTelegramAgent'
        self.state = shared_state

    def _format_briefing(self, snap):
        sign = lambda n: '▲' if n and n >= 0 else '▼'
        fmt  = lambda n: f'${n:,.2f}' if n else 'N/A'
        chg  = lambda n: f'{sign(n)}{abs(n):.2f}%' if n is not None else '—'
        return (
            f'🚨 <b>WAR MONITOR — DAY {snap["war_day"]}</b>\n'
            f'📅 {datetime.now(timezone.utc).strftime("%b %d, %Y  %H:%M UTC")}\n\n'
            f'⚔️ <b>2026 Iran War</b>\n'
            f'🔴 Status: ACTIVE  |  Hormuz: CLOSED\n'
            f'🔴 Ceasefire: NONE  |  Nukes: STRUCK\n\n'
            f'📈 <b>MARKETS</b>\n'
            f'₿ Bitcoin:  {fmt(snap["btc"])}  {chg(snap["btc_change"])}\n'
            f'📊 S&P 500: {fmt(snap["sp500"])}  {chg(snap["sp500_change"])}\n'
            f'🛢 WTI Oil: {fmt(snap["oil"])}  {chg(snap["oil_change"])}\n\n'
            f'🎯 Missiles (2026): ~500+  |  Intercepted: ~90%\n\n'
            f'🌐 <a href="https://vigilant-forgiveness-production-6c0f.up.railway.app">Live Dashboard</a>'
        )

    def run(self, message_queue):
        print(f'[{self.name}] Started — monitoring shared state every {CHECK_INTERVAL}s')

        while True:
            try:
                snap = self.state.get_snapshot()

                # ── Price spike alerts ─────────────────────────────────
                checks = [
                    ('btc',   snap['btc'],   snap['btc_change'],   'Bitcoin'),
                    ('sp500', snap['sp500'], snap['sp500_change'], 'S&P 500'),
                    ('oil',   snap['oil'],   snap['oil_change'],   'WTI Crude Oil'),
                ]
                for ticker, price, change, label in checks:
                    if price is None:
                        continue
                    alerted, move = self.state.should_alert(ticker, price, ALERT_THRESHOLD)
                    if alerted:
                        direction = '📈 SURGE' if move > 0 else '📉 DROP'
                        msg = (
                            f'⚠️ <b>WAR MONITOR ALERT — {label}</b>\n'
                            f'{direction} {abs(move):.2f}% move detected\n'
                            f'Price: ${price:,.2f}  |  24h: {change:+.2f}%\n'
                            f'🌐 War Day {snap["war_day"]}'
                        )
                        send_telegram(msg)
                        message_queue.put({
                            'agent': self.name,
                            'type': 'alert_sent',
                            'data': f'ALERT: {label} {direction} {abs(move):.2f}%',
                            'timestamp': time.time(),
                        })

                # ── Latest news headline alert ─────────────────────────
                news = self.state.get_news()
                if news:
                    top = news[0]
                    # Only alert once per headline (track by title)
                    if not hasattr(self, '_last_headline') or self._last_headline != top['title']:
                        self._last_headline = top['title']
                        send_telegram(
                            f'📰 <b>BREAKING — WAR UPDATE</b>\n\n'
                            f'{top["title"]}\n\n'
                            f'<i>{top["source"]} · {top["date"]}</i>\n'
                            f'<a href="{top["url"]}">Read more</a>'
                        )
                        message_queue.put({
                            'agent': self.name,
                            'type': 'news_alert',
                            'data': f'Sent headline: {top["title"][:80]}',
                            'timestamp': time.time(),
                        })

                # ── Daily briefing at 09:00 UTC ────────────────────────
                if self.state.should_send_daily_briefing():
                    send_telegram(self._format_briefing(snap))
                    message_queue.put({
                        'agent': self.name,
                        'type': 'daily_briefing',
                        'data': f'Daily briefing sent — War Day {snap["war_day"]}',
                        'timestamp': time.time(),
                    })

            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error', 'data': str(e), 'timestamp': time.time()})

            time.sleep(CHECK_INTERVAL)
