# src/utils/ratelimiter.py
import time


class RateLimiter:
    def __init__(self, requests_per_minute=10):
        self.requests_per_minute = requests_per_minute
        self.interval = 60 / requests_per_minute
        self.last_request_time = 0

    def wait(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_request_time

        if elapsed_time < self.interval:
            sleep_time = self.interval - elapsed_time
            time.sleep(sleep_time)

        self.last_request_time = time.time()
