"""
War News Agent — fetches latest Iran/Israel war headlines every 5 minutes via GNews.
"""
import time
import urllib.request
import urllib.parse
import json
import os


GNEWS_KEY = os.getenv('GNEWS_API_KEY', '')


class WarNewsAgent:
    def __init__(self, shared_state):
        self.name = 'WarNewsAgent'
        self.interval = 300  # every 5 minutes
        self.state = shared_state

    def run(self, message_queue):
        print(f'[{self.name}] Started — fetching war news every {self.interval}s')
        while True:
            try:
                if GNEWS_KEY:
                    q   = urllib.parse.quote('Iran Israel war 2026')
                    url = f'https://gnews.io/api/v4/search?q={q}&lang=en&max=5&sortby=publishedAt&apikey={GNEWS_KEY}'
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=8) as r:
                        data = json.loads(r.read())

                    articles = [
                        {
                            'title':  a['title'],
                            'source': a.get('source', {}).get('name', 'News'),
                            'url':    a['url'],
                            'date':   a['publishedAt'][:10],
                        }
                        for a in data.get('articles', [])
                    ]
                    self.state.set_news(articles)

                    headlines = ' | '.join(a['title'][:60] for a in articles[:3])
                    message_queue.put({
                        'agent': self.name,
                        'type': 'news_update',
                        'data': f'{len(articles)} headlines fetched: {headlines}',
                        'timestamp': time.time(),
                        'articles': articles,
                    })
                else:
                    message_queue.put({
                        'agent': self.name,
                        'type': 'news_update',
                        'data': 'GNEWS_API_KEY not set — skipping news fetch',
                        'timestamp': time.time(),
                    })

            except Exception as e:
                print(f'[{self.name}] Error: {e}')
                message_queue.put({'agent': self.name, 'type': 'error', 'data': str(e), 'timestamp': time.time()})

            time.sleep(self.interval)
