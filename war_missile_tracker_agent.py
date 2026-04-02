"""
WarMissileTrackerAgent — monitors RSS news feeds every 2 minutes for missile/launch events.
When a launch is detected: immediate Telegram alert + posts to activity feed.

Sources: Reuters, Times of Israel, CNN, Al Jazeera (free RSS, no API key)
"""
import time
import urllib.request
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8619883125:AAFUcPGAecAqFVmRz3c7vr5uO5YY5qx9m2s')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID', '603046431')

RSS_FEEDS = [
    ('Reuters',          'https://feeds.reuters.com/reuters/topNews'),
    ('Times of Israel',  'https://www.timesofisrael.com/feed/'),
    ('CNN World',        'https://rss.cnn.com/rss/edition_world.rss'),
    ('Al Jazeera',       'https://www.aljazeera.com/xml/rss/all.xml'),
]

MISSILE_KEYWORDS = [
    'missile', 'ballistic', 'rocket launched', 'rockets fired', 'drone attack',
    'drone strike', 'barrage', 'salvo', 'airstrike', 'air strike', 'bombardment',
    'fired at', 'launched at', 'attack on', 'struck', 'explosion', 'warhead',
]

ORIGIN_MAP = [
    (['iran', 'irgc', 'revolutionary guard'],          'Iran'),
    (['hezbollah', 'lebanon'],                          'Hezbollah/Lebanon'),
    (['houthi', 'yemen'],                               'Yemen (Houthi)'),
    (['hamas', 'gaza', 'islamic jihad'],                'Gaza'),
    (['israel', 'idf', 'israeli air force'],            'Israel'),
    (['united states', 'u.s. military', 'pentagon'],   'US Forces'),
]

TARGET_MAP = [
    (['israel', 'tel aviv', 'haifa', 'jerusalem', 'ben gurion'], 'Israel'),
    (['iran', 'tehran', 'natanz', 'isfahan', 'parchin'],         'Iran'),
    (['bahrain', 'manama'],                                       'Bahrain'),
    (['qatar', 'doha'],                                           'Qatar'),
    (['uae', 'dubai', 'abu dhabi'],                               'UAE'),
    (['kuwait'],                                                   'Kuwait'),
    (['saudi', 'riyadh'],                                         'Saudi Arabia'),
    (['iraq', 'baghdad'],                                         'Iraq'),
    (['syria', 'damascus'],                                       'Syria'),
]


def _fetch_rss(url):
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/rss+xml,text/xml,*/*'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode('utf-8', errors='replace')


def _parse_rss(xml_text):
    """Return list of {title, link} from RSS."""
    items = []
    # Strip namespaces for easier parsing
    xml_text = re.sub(r' xmlns[^"]*"[^"]*"', '', xml_text)
    try:
        root = ET.fromstring(xml_text)
        for item in root.iter('item'):
            title_el = item.find('title')
            link_el  = item.find('link') or item.find('guid')
            title = (title_el.text or '').strip() if title_el is not None else ''
            link  = (link_el.text or '').strip() if link_el is not None else ''
            if title:
                items.append({'title': title, 'link': link})
    except ET.ParseError:
        # Fallback: regex
        for m in re.finditer(r'<title[^>]*><!\[CDATA\[(.*?)\]\]></title>|<title[^>]*>(.*?)</title>', xml_text, re.S):
            title = (m.group(1) or m.group(2) or '').strip()
            if title and title not in ('', 'RSS', 'Feed'):
                items.append({'title': title, 'link': ''})
    return items


def _detect_location(title, location_map):
    t = title.lower()
    for keywords, name in location_map:
        if any(k in t for k in keywords):
            return name
    return None


def _missile_type(title):
    t = title.lower()
    if 'ballistic' in t:  return 'ballistic'
    if 'cruise'    in t:  return 'cruise'
    if 'drone'     in t:  return 'drone'
    if 'rocket'    in t:  return 'rocket'
    if 'airstrike' in t or 'air strike' in t: return 'airstrike'
    return 'missile'


def _send_telegram(text):
    try:
        body = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}).encode()
        req  = urllib.request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            data=body, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print(f'[WarMissileTrackerAgent] Telegram error: {e}')


class WarMissileTrackerAgent:
    def __init__(self, shared_state):
        self.name     = 'WarMissileTrackerAgent'
        self.interval = 120   # scan every 2 minutes
        self.state    = shared_state
        self._seen    = set()
        self._count   = 0

    def run(self, message_queue):
        print(f'[{self.name}] Started — scanning {len(RSS_FEEDS)} RSS feeds every {self.interval}s')
        while True:
            detected = 0
            for source_name, feed_url in RSS_FEEDS:
                try:
                    xml  = _fetch_rss(feed_url)
                    items = _parse_rss(xml)

                    for item in items:
                        title = item['title']
                        if not title or title in self._seen:
                            continue
                        t = title.lower()
                        if not any(kw in t for kw in MISSILE_KEYWORDS):
                            continue

                        self._seen.add(title)
                        if len(self._seen) > 500:  # prevent unbounded growth
                            self._seen = set(list(self._seen)[-200:])

                        self._count += 1
                        detected += 1

                        origin  = _detect_location(title, ORIGIN_MAP)
                        target  = _detect_location(title, TARGET_MAP)
                        m_type  = _missile_type(title)
                        icon    = '🛸' if m_type == 'drone' else '✈️' if m_type == 'airstrike' else '🚀'

                        # Immediate Telegram alert
                        tg = (
                            f'{icon} <b>MISSILE TRACKER ALERT #{self._count}</b>\n\n'
                            f'{title}\n\n'
                            f'{"📍 Origin: " + origin + chr(10) if origin else ""}'
                            f'{"🎯 Target: " + target + chr(10) if target else ""}'
                            f'⚔️ Type: {m_type.upper()}\n'
                            f'📡 Source: {source_name}\n'
                            f'🕐 {datetime.now(timezone.utc).strftime("%H:%M UTC")}\n'
                            f'{"🔗 " + item["link"] if item["link"] else ""}'
                        )
                        _send_telegram(tg)

                        # Store in shared state
                        if hasattr(self.state, 'add_missile_event'):
                            self.state.add_missile_event({
                                'title': title, 'source': source_name,
                                'origin': origin, 'target': target,
                                'type': m_type, 'timestamp': time.time(),
                            })

                        message_queue.put({
                            'agent':     self.name,
                            'type':      'missile_detected',
                            'data':      f'{icon} #{self._count} {m_type.upper()} | {origin or "?"} → {target or "?"} | {title[:80]}',
                            'timestamp': time.time(),
                        })

                except Exception as e:
                    print(f'[{self.name}] Feed error ({source_name}): {e}')

            if detected == 0:
                message_queue.put({
                    'agent':     self.name,
                    'type':      'scan_complete',
                    'data':      f'Scanned {len(RSS_FEEDS)} feeds — no new missile events',
                    'timestamp': time.time(),
                })

            self.state.ping_agent(self.name)
            time.sleep(self.interval)
