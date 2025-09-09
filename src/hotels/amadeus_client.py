"""
Lightweight Amadeus API client (Auth + Hotels + Offers).

Usage (raw JSON only; no business logic here):
    from hotels.amadeus_client import AmadeusClient

    client = AmadeusClient()  # reads env vars by default
    token = client.get_access_token()

    hotels = client.get_hotels_by_city(city_code="NCE", max_hotels=40)
    hotel_ids = [h["hotelId"] for h in hotels]

    offers = client.get_hotel_offers(
        hotel_ids=hotel_ids,
        check_in="2025-09-20",
        nights=2,
        adults=1,
        rooms=1,
        currency="EUR",
    )
"""

from __future__ import annotations

import os
import time
from typing import Dict, List, Optional, Any, Iterable
import logging
import requests

logger = logging.getLogger(__name__)

AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_BASE_URL = "https://test.api.amadeus.com"

DEFAULT_TIMEOUT = (5, 20)  # (connect, read) seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # exponential backoff base


class AmadeusAuthError(RuntimeError):
    pass


class AmadeusRateLimitError(RuntimeError):
    pass


class AmadeusClient:
    """
    Minimal client focused on:
      - OAuth2 client_credentials
      - /v1/reference-data/locations/hotels/by-city
      - /v3/shopping/hotel-offers
    Returns RAW JSON (dicts/lists). Storage/flattening happens elsewhere.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: str = AMADEUS_BASE_URL,
        timeout: tuple = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing Amadeus credentials. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._access_token: Optional[str] = None
        self._session = session or requests.Session()

    # ---------- Internal helpers ----------

    def _headers(self) -> Dict[str, str]:
        if not self._access_token:
            self.get_access_token()
        return {"Authorization": f"Bearer {self._access_token}"}

    def _post_form(self, url: str, data: Dict[str, str]) -> Dict[str, Any]:
        for attempt in range(1, MAX_RETRIES + 1):
            resp = self._session.post(url, data=data, timeout=self.timeout)
            if resp.status_code == 429:
                self._handle_rate_limit(resp, attempt)
                continue
            if 200 <= resp.status_code < 300:
                return resp.json()
            if 500 <= resp.status_code < 600 and attempt < MAX_RETRIES:
                self._sleep_backoff(attempt)
                continue
            raise AmadeusAuthError(
                f"Auth request failed: {resp.status_code} {resp.text[:500]}"
            )
        raise AmadeusAuthError("Auth failed after retries.")

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        for attempt in range(1, MAX_RETRIES + 1):
            resp = self._session.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            if resp.status_code == 429:
                self._handle_rate_limit(resp, attempt)
                continue
            if resp.status_code == 401 and attempt < MAX_RETRIES:
                # token expired → refresh once
                logger.info("Token expired; refreshing…")
                self.get_access_token(force=True)
                continue
            if 200 <= resp.status_code < 300:
                return resp.json()
            if 500 <= resp.status_code < 600 and attempt < MAX_RETRIES:
                self._sleep_backoff(attempt)
                continue
            raise RuntimeError(
                f"GET {url} failed: {resp.status_code} {resp.text[:500]}"
            )
        raise RuntimeError(f"GET {url} failed after retries.")

    def _sleep_backoff(self, attempt: int) -> None:
        sleep_s = (RETRY_BACKOFF ** (attempt - 1))
        time.sleep(sleep_s)

    def _handle_rate_limit(self, resp: requests.Response, attempt: int) -> None:
        retry_after = resp.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            delay = int(retry_after)
        else:
            delay = max(1, int(RETRY_BACKOFF ** attempt))
        logger.warning("Rate limited (429). Sleeping %ss then retrying…", delay)
        time.sleep(delay)
        if attempt >= MAX_RETRIES:
            raise AmadeusRateLimitError("Exceeded max retries due to rate limiting.")

    # ---------- Public API ----------

    def get_access_token(self, force: bool = False) -> str:
        """
        Fetch and cache an OAuth2 access token using client_credentials.
        """
        if self._access_token and not force:
            return self._access_token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        data = self._post_form(AMADEUS_AUTH_URL, payload)
        token = data.get("access_token")
        if not token:
            raise AmadeusAuthError(f"Missing access_token in response: {data}")
        self._access_token = token
        return token
    
    def get_hotels_by_geocode(self, lat: float, lon: float, radius_km: int = 5, max_hotels: int = 50):
        url = f"{self.base_url}/v1/reference-data/locations/hotels/by-geocode"
        params = {
            "latitude": f"{lat:.6f}",
            "longitude": f"{lon:.6f}",
            "radius": int(radius_km),           # keep it simple
            # omit radiusUnit and page[limit] to avoid format issues
        }
        data = self._get(url, params)
        hotels = data.get("data", [])
        return hotels[:max_hotels]



    def get_hotels_by_city(self, city_code: str, max_hotels: int = 50) -> List[Dict[str, Any]]:
        """
        Returns a list of hotel summaries for a given IATA city code (e.g., 'NCE').
        Endpoint: /v1/reference-data/locations/hotels/by-city
        """
        url = f"{self.base_url}/v1/reference-data/locations/hotels/by-city"
        # API accepts page[limit] up to 100; free tier behaves conservatively.
        page_limit = min(100, max_hotels)
        params = {
            "cityCode": city_code.upper(),
            "page[limit]": page_limit,
        }
        data = self._get(url, params)
        hotels = data.get("data", [])
        return hotels[:max_hotels]

    def get_hotel_offers(
        self,
        hotel_ids: Iterable[str],
        check_in: str,
        nights: int = 1,
        adults: int = 1,
        rooms: int = 1,
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch offers for up to ~20 hotelIds per request (chunked automatically).
        Endpoint: /v3/shopping/hotel-offers
        Returns the RAW merged JSON: {"batches": [ {request_hotel_ids: [...], response: {...}}, ... ]}
        """
        hotel_ids = list(hotel_ids)
        if not hotel_ids:
            return {"batches": []}

        all_batches: List[Dict[str, Any]] = []
        for chunk in _chunks(hotel_ids, 20):
            params: Dict[str, Any] = {
                "hotelIds": ",".join(chunk),
                "checkInDate": check_in,        # YYYY-MM-DD
                "roomQuantity": rooms,
                "adults": adults,
                "paymentPolicy": "NONE",        # broaden results; we’ll interpret policy later
                "includeClosed": "false",
                "bestRateOnly": "true",
                "nights": nights,
            }
            if currency:
                params["currency"] = currency

            url = f"{self.base_url}/v3/shopping/hotel-offers"
            resp_json = self._get(url, params)
            all_batches.append({
                "request_hotel_ids": chunk,
                "response": resp_json,
            })

        return {"batches": all_batches}
    

# ---------- small utilities ----------

def _chunks(seq: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]
