"""
War News Agent — fetches latest Iran/Israel war headlines every 30min via GNews.
Features: deduplication, ceasefire detection, missile count extraction.
"""
import time
import urllib.request
import urllib.parse
import json
import re
import os

GNEWS_KEY = os.getenv('GNEWS_API_KEY', '')

CEASEFIRE_KEYWORDS = ['ceasefire', 'cease fire', 'peace deal', 'truce', 'armistice', 'agreement reached', 'halt fighting']
MISSILE_KEYWORDS   = ['missile', 'ballistic', 'rocket', 'drone', 'barrage', 'salvo', 'strike', 'attack']


class WarNewsAgent:
    def __init__(self, shared_state):
        self.name     = 'WarNewsAgent'
        self.interval = 7200   # 2 hours — 12 req/day
        self.state    = shared_state
        self._seen    = set()  # deduplication: seen headline titles

    def _is_ceasefire(self, title):
        t = title.lower()
        return any(k in t for k in CEASEFIRE_KEYWORDS)

    def _has_missile(self, title):
        t = title.lower()
        return any(k in t for k in MISSILE_KEYWORDS)

    def run(self, message_queue):
        print(f'[{self.name}] Started — fetching war news every {self.interval//3600}h (budget: ~12 req/day)')
        while True:
            try:
                if not GNEWS_KEY:
                    message_queue.put({'agent': self.name, 'type': 'warning',
                                       'data': 'GNEWS_API_KEY not set', 'timestamp': time.time()})
                    for _ in range(self.interval // 60):
                        time.sleep(60)
                        self.state.ping_agent(self.name)
                    continue

                q   = urllib.parse.quote('Iran Israel war 2026')
                url = f'https://gnews.io/api/v4/search?q={q}&lang=en&max=5&sortby=publishedAt&apikey={GNEWS_KEY}'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = json.loads(r.read())

                articles = [
                    {'title': a['title'], 'source': a.get('source', {}).get('name', 'News'),
                     'url': a['url'], 'date': a['publishedAt'][:10]}
                    for a in data.get('articles', [])
                ]

                # ── Deduplication ──────────────────────────────────────
                new_articles = [a for a in articles if a['title'] not in self._seen]
                for a in new_articles:
                    self._seen.add(a['title'])
                # Keep seen set bounded
                if len(self._seen) > 500:
                    self._seen = set(list(self._seen)[-200:])

                self.state.set_news(articles)

                # ── Ceasefire detection ────────────────────────────────
                ceasefire_hits = [a for a in new_articles if self._is_ceasefire(a['title'])]
                if ceasefire_hits:
                    self.state.set_ceasefire(True, ceasefire_hits[0]['title'])
                    message_queue.put({'agent': self.name, 'type': 'ceasefire_detected',
                                       'data': f'CEASEFIRE SIGNAL: {ceasefire_hits[0]["title"]}',
                                       'timestamp': time.time()})

                # ── Missile mention counter ────────────────────────────
                missile_hits = [a for a in new_articles if self._has_missile(a['title'])]
                if missile_hits:
                    self.state.increment_news_strikes(len(missile_hits))
                    message_queue.put({'agent': self.name, 'type': 'missile_detected',
                                       'data': f'{len(missile_hits)} new missile/strike headlines',
                                       'timestamp': time.time()})

                summary = f'{len(new_articles)} new / {len(articles)} total headlines'
                message_queue.put({'agent': self.name, 'type': 'news_update',
                                   'data': summary, 'timestamp': time.time(), 'articles': articles})

            except Exception as e:
                err = str(e)
                print(f'[{self.name}] Error: {err}')
                status = 'rate-limited (free tier)' if '403' in err else err
                message_queue.put({'agent': self.name, 'type': 'warning',
                                   'data': f'GNews: {status}', 'timestamp': time.time()})

            # Sleep in 60s chunks — ping so health monitor doesn't flag as down
            for _ in range(self.interval // 60):
                time.sleep(60)
                self.state.ping_agent(self.name)
