"""
Agent3 — War Dashboard Monitor
Pings the live war dashboard every 60s and reports uptime + response time.
Alerts if the dashboard goes down.
"""
import time
import urllib.request


DASHBOARD_URL = 'https://vigilant-forgiveness-production-6c0f.up.railway.app'


class Agent3:
    def __init__(self, shared_state=None):
        self.name = 'WarDashboardAgent'
        self.interval = 60
        self.state = shared_state
        self._was_down = False

    def run(self, message_queue):
        print(f'[{self.name}] Started — monitoring dashboard every {self.interval}s')
        while True:
            try:
                start = time.time()
                req = urllib.request.Request(DASHBOARD_URL, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as r:
                    status = r.status
                elapsed_ms = int((time.time() - start) * 1000)

                if self.state:
                    self.state.ping_agent(self.name)

                if self._was_down:
                    self._was_down = False
                    msg_type = 'dashboard_recovered'
                    msg_data = f'Dashboard BACK ONLINE  {elapsed_ms}ms'
                else:
                    msg_type = 'dashboard_ok'
                    msg_data = f'Dashboard UP  {elapsed_ms}ms  (HTTP {status})'

                message_queue.put({
                    'agent': self.name,
                    'type': msg_type,
                    'data': msg_data,
                    'timestamp': time.time(),
                    'metrics': {'response_ms': elapsed_ms, 'status': status},
                })

            except Exception as e:
                self._was_down = True
                print(f'[{self.name}] Dashboard unreachable: {e}')
                message_queue.put({
                    'agent': self.name,
                    'type': 'dashboard_down',
                    'data': f'Dashboard UNREACHABLE: {e}',
                    'timestamp': time.time(),
                })

            time.sleep(self.interval)
