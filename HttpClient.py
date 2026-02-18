import random
import time
import requests
from typing import Optional

# ---------------------------------------------------------------------------
# HTTP klient s retry a delay logikou
# ---------------------------------------------------------------------------

class HttpClient:
    """Obaluje requests s User-Agent, random delay a retry logikou."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "cs,en;q=0.9",
    }

    def __init__(self, delay_range: tuple = (2.0, 5.0), max_retries: int = 3):
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def delay(self) -> None:
        """Náhodné zpoždění mezi požadavky."""
        wait = random.uniform(*self.delay_range)
        time.sleep(wait)

    def get(self, url: str, delay: bool = True) -> Optional[requests.Response]:
        """
        Stáhne URL s retry logikou.

        Returns:
            Response objekt nebo None pokud všechny pokusy selhaly.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                if delay and attempt > 1:
                    self.delay()
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                resp.encoding = "utf-8"
                return resp
            except requests.RequestException as e:
                print(f"    ✗ Pokus {attempt}/{self.max_retries} selhal pro {url}: {e}")
                if attempt < self.max_retries:
                    self.delay()
        return None
