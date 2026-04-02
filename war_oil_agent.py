"""
War Oil Agent — fetches WTI Crude Oil futures every 60s via Yahoo Finance.
"""
import time
import urllib.request
import urllib.parse
import json


def _fetch_yahoo(ticker):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval=1d&range=2d'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read())
    result = data['chart']['result'][0]
    closes = [c for c in result['indicators']['quote'][0]['close'] if c is not None]
    price  = closes[-1]
    prev   = result['meta'].get('previousClose') or closes[-2]
    change = ((price - prev) / prev) * 100
    return price, change


class WarOilAgent:
    def __init__(self, shared_state):
        self.name = 'WarOilAgent'
        self.interval = 60
        self.state = shared_state

    def run(self, message_queue):
        print(f'[{self.name}] Started — polling WTI Oil every {self.interval}s')
        while True:
            try:
                price, change = _fetch_yahoo('CL=F')
                self.state.set_market('oil', price, change)

                message_queue.put({
                    'agent': self.name,
                    'type': 'oil_price',
                    'data': f'WTI Oil  ${price:.2f}  ({change:+.2f}%)',
                    'timestamp': time.time(),
                    'metrics': {'price': price, 'change': change},
                })
            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error', 'data': str(e), 'timestamp': time.time()})

            time.sleep(self.interval)
