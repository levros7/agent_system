"""
War BTC Agent — fetches Bitcoin price every 60s via Binance API.
Posts price updates to the manager queue and shared state.
"""
import time
import urllib.request
import json


class WarBTCAgent:
    def __init__(self, shared_state):
        self.name = 'WarBTCAgent'
        self.interval = 60
        self.state = shared_state

    def run(self, message_queue):
        print(f'[{self.name}] Started — polling Binance every {self.interval}s')
        while True:
            try:
                req = urllib.request.Request(
                    'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = json.loads(r.read())

                price  = float(data['lastPrice'])
                change = float(data['priceChangePercent'])
                self.state.set_market('btc', price, change)
                self.state.ping_agent(self.name)

                message_queue.put({
                    'agent': self.name,
                    'type': 'btc_price',
                    'data': f'BTC ${price:,.2f}  ({change:+.2f}%)',
                    'timestamp': time.time(),
                    'metrics': {'price': price, 'change': change},
                })
            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error', 'data': str(e), 'timestamp': time.time()})

            time.sleep(self.interval)
