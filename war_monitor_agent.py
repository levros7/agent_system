"""
War Monitor Agent - Monitors US-Israel/Iran conflict metrics.
Tracks Bitcoin, S&P 500, WTI Oil prices and sends alerts via Telegram.
Fits the existing agent_system manager/queue architecture.
"""
import time
import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timezone


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8619883125:AAFUcPGAecAqFVmRz3c7vr5uO5YY5qx9m2s')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID', '603046431')

# Alert if price moves more than this % since last check
ALERT_THRESHOLD = 2.0

# How often to check (seconds)
INTERVAL = 60

WAR_START = datetime(2026, 2, 28, tzinfo=timezone.utc)


def _fetch(url, timeout=8):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def fetch_btc():
    data = _fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
    return data['bitcoin']['usd'], data['bitcoin']['usd_24h_change']


def fetch_yahoo(ticker):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval=1d&range=2d'
    data = _fetch(url)
    result = data['chart']['result'][0]
    closes = [c for c in result['indicators']['quote'][0]['close'] if c is not None]
    price = closes[-1]
    prev = result['meta'].get('previousClose') or closes[-2]
    change = ((price - prev) / prev) * 100
    return price, change


def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        body = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}).encode()
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            data=body,
            headers={'Content-Type': 'application/json'},
        )
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print(f'[WarMonitorAgent] Telegram error: {e}')


def war_day():
    return (datetime.now(timezone.utc) - WAR_START).days + 1


class WarMonitorAgent:
    def __init__(self):
        self.name = 'WarMonitorAgent'
        self.interval = INTERVAL
        self._prev = {}   # ticker -> last price
        self._last_briefing_day = None

    def _check_alert(self, ticker, price, change, label, symbol='$'):
        prev = self._prev.get(ticker)
        self._prev[ticker] = price

        alerted = False
        if prev is not None:
            move = ((price - prev) / prev) * 100
            if abs(move) >= ALERT_THRESHOLD:
                direction = '📈 SURGE' if move > 0 else '📉 DROP'
                send_telegram(
                    f'⚠️ <b>WAR MONITOR ALERT — {label}</b>\n'
                    f'{direction} {abs(move):.2f}% in last {self.interval}s\n'
                    f'Price: {symbol}{price:,.2f}  |  24h: {change:+.2f}%\n'
                    f'🌐 War Day {war_day()}'
                )
                alerted = True
        return alerted

    def _send_daily_briefing(self, btc, btc_c, sp, sp_c, oil, oil_c):
        sign = lambda n: '▲' if n >= 0 else '▼'
        msg = (
            f'🚨 <b>WAR MONITOR — DAY {war_day()}</b>\n'
            f'📅 {datetime.now(timezone.utc).strftime("%b %d, %Y  %H:%M UTC")}\n\n'
            f'⚔️ <b>2026 Iran War</b>\n'
            f'🔴 Status: ACTIVE  |  Hormuz: CLOSED\n'
            f'🔴 Ceasefire: NONE  |  Nukes: STRUCK\n\n'
            f'📈 <b>MARKETS</b>\n'
            f'₿ Bitcoin: ${btc:,.2f}  {sign(btc_c)}{abs(btc_c):.2f}%\n'
            f'📊 S&P 500: ${sp:,.2f}  {sign(sp_c)}{abs(sp_c):.2f}%\n'
            f'🛢 WTI Oil: ${oil:,.2f}  {sign(oil_c)}{abs(oil_c):.2f}%\n\n'
            f'🎯 Missiles launched (2026): ~500+\n'
            f'✅ Intercepted: ~450 (~90%)\n\n'
            f'🌐 <a href="https://vigilant-forgiveness-production-6c0f.up.railway.app">Live Dashboard</a>'
        )
        send_telegram(msg)

    def run(self, message_queue):
        print(f'[{self.name}] Started — monitoring BTC, S&P500, WTI Oil every {self.interval}s')

        while True:
            try:
                btc, btc_c = fetch_btc()
                sp,  sp_c  = fetch_yahoo('^GSPC')
                oil, oil_c = fetch_yahoo('CL=F')

                # Check for price spike alerts
                self._check_alert('btc',  btc, btc_c, 'Bitcoin',     '$')
                self._check_alert('sp',   sp,  sp_c,  'S&P 500',     '$')
                self._check_alert('oil',  oil, oil_c, 'WTI Crude Oil', '$')

                # Send daily briefing once per day at 09:00 UTC
                now = datetime.now(timezone.utc)
                if now.hour == 9 and self._last_briefing_day != now.date():
                    self._send_daily_briefing(btc, btc_c, sp, sp_c, oil, oil_c)
                    self._last_briefing_day = now.date()

                # Post status to manager dashboard
                message_queue.put({
                    'agent': self.name,
                    'type': 'war_monitor',
                    'data': (
                        f'Day {war_day()} | '
                        f'BTC ${btc:,.0f} ({btc_c:+.2f}%) | '
                        f'S&P {sp:,.0f} ({sp_c:+.2f}%) | '
                        f'Oil ${oil:.2f} ({oil_c:+.2f}%)'
                    ),
                    'timestamp': time.time(),
                    'metrics': {
                        'war_day': war_day(),
                        'btc': btc, 'btc_change': btc_c,
                        'sp500': sp, 'sp500_change': sp_c,
                        'oil': oil, 'oil_change': oil_c,
                    },
                })

            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({
                    'agent': self.name,
                    'type': 'error',
                    'data': str(e),
                    'timestamp': time.time(),
                })

            time.sleep(self.interval)
