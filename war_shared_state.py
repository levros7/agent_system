"""
Shared state for the War Monitor agent team.
All 5 agents read/write this thread-safe object.
"""
import threading
from datetime import datetime, timezone

WAR_START = datetime(2026, 2, 28, tzinfo=timezone.utc)

class WarSharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self.btc        = None
        self.btc_change = None
        self.sp500        = None
        self.sp500_change = None
        self.oil        = None
        self.oil_change = None
        self.latest_news     = []   # list of {title, source, url, date}
        self.last_briefing_day = None
        self.alerts_sent = {}       # ticker -> last alerted price

    def set_market(self, ticker, price, change):
        with self._lock:
            setattr(self, ticker, price)
            setattr(self, f'{ticker}_change', change)

    def get_snapshot(self):
        with self._lock:
            return {
                'btc': self.btc, 'btc_change': self.btc_change,
                'sp500': self.sp500, 'sp500_change': self.sp500_change,
                'oil': self.oil, 'oil_change': self.oil_change,
                'war_day': (datetime.now(timezone.utc) - WAR_START).days + 1,
            }

    def set_news(self, articles):
        with self._lock:
            self.latest_news = articles

    def get_news(self):
        with self._lock:
            return list(self.latest_news)

    def should_alert(self, ticker, price, threshold=2.0):
        """Returns (should_alert, move_pct). True if price moved > threshold since last alert."""
        with self._lock:
            last = self.alerts_sent.get(ticker)
            if last is None:
                self.alerts_sent[ticker] = price
                return False, 0
            move = ((price - last) / last) * 100
            if abs(move) >= threshold:
                self.alerts_sent[ticker] = price
                return True, move
            return False, move

    def should_send_daily_briefing(self):
        with self._lock:
            today = datetime.now(timezone.utc).date()
            hour  = datetime.now(timezone.utc).hour
            if hour == 9 and self.last_briefing_day != today:
                self.last_briefing_day = today
                return True
            return False
