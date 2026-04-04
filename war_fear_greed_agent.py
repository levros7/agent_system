"""
WarFearGreedAgent — fetches the Crypto Fear & Greed Index every 5 minutes.
API: alternative.me/fng (free, no key needed)

Values:
  0–24   Extreme Fear
  25–49  Fear
  50     Neutral
  51–74  Greed
  75–100 Extreme Greed

During active war, index typically sits in Fear/Extreme Fear territory.
"""
import time
import urllib.request
import json


def _fetch_fear_greed():
    url = 'https://api.alternative.me/fng/?limit=1'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read())
    item = data['data'][0]
    return int(item['value']), item['value_classification']


class WarFearGreedAgent:
    def __init__(self, shared_state):
        self.name     = 'WarFearGreedAgent'
        self.interval = 300  # every 5 minutes (index updates once per day, but API allows more)
        self.state    = shared_state

    def run(self, message_queue):
        print(f'[{self.name}] Started — polling Fear & Greed every {self.interval//60}min')
        while True:
            try:
                value, classification = _fetch_fear_greed()
                self.state.set_fear_greed(value, classification)
                self.state.ping_agent(self.name)

                # Emoji indicator
                if value <= 24:   icon = '😱'
                elif value <= 49: icon = '😰'
                elif value == 50: icon = '😐'
                elif value <= 74: icon = '😊'
                else:             icon = '🤑'

                message_queue.put({
                    'agent': self.name,
                    'type': 'fear_greed',
                    'data': f'{icon} Fear & Greed: {value} — {classification}',
                    'timestamp': time.time(),
                    'metrics': {'value': value, 'classification': classification},
                })
            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error', 'data': str(e), 'timestamp': time.time()})

            # Sleep in 60s chunks — ping each time so health monitor doesn't flag as down
            for _ in range(self.interval // 60):
                time.sleep(60)
                self.state.ping_agent(self.name)
