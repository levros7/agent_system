"""
Agent1 — War Gold Agent
Fetches Gold futures (GC=F) every 60s via Yahoo Finance.
Gold is a key war-hedge indicator: spikes when conflict escalates.
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


class Agent1:
    def __init__(self, shared_state=None):
        self.name = 'WarGoldAgent'
        self.interval = 60
        self.state = shared_state

    def run(self, message_queue):
        print(f'[{self.name}] Started — polling Gold (GC=F) every {self.interval}s')
        while True:
            try:
                price, change = _fetch_yahoo('GC=F')
                if self.state:
                    self.state.set_market('gold', price, change)
                    self.state.ping_agent(self.name)

                message_queue.put({
                    'agent': self.name,
                    'type': 'gold_price',
                    'data': f'Gold  ${price:,.2f}  ({change:+.2f}%)',
                    'timestamp': time.time(),
                    'metrics': {'price': price, 'change': change},
                })
            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error', 'data': str(e), 'timestamp': time.time()})

            time.sleep(self.interval)
