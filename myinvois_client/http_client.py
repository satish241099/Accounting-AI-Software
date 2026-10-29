"""
HTTP client for MyInvois API interactions.
"""

import time
from typing import Any

import httpx

from .config import MyInvoisConfig, SecretProvider
from .exceptions import APIError, AuthenticationError, RateLimitError


class MyInvoisHTTPClient:
    """HTTP client for MyInvois API with retry logic and rate limiting."""

    def __init__(self, config: MyInvoisConfig, secret_provider: SecretProvider):
        self.config = config
        self.secret_provider = secret_provider

        # HTTP client with timeout and retry configuration
        self.client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=60.0),
            headers={
                "User-Agent": "MyInvois-Client/1.0.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        # Rate limiting state
        self.rate_limit_state = {"last_request_time": 0, "request_count": 0, "burst_reset_time": 0}

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limits."""
        current_time = time.time()

        # Reset burst counter if needed
        if current_time > self.rate_limit_state["burst_reset_time"]:
            self.rate_limit_state["request_count"] = 0
            self.rate_limit_state["burst_reset_time"] = current_time + 60  # Reset every minute

        # Check burst limit
        if self.rate_limit_state["request_count"] >= self.config.rate_limit_burst_size:
            time_since_reset = current_time - self.rate_limit_state["burst_reset_time"]
            retry_after = max(0, 60 - time_since_reset)
            raise RateLimitError(
                f"Rate limit exceeded. Burst limit reached. Retry after {retry_after:.1f} seconds",
                retry_after=int(retry_after),
            )

        # Check per-minute limit
        time_since_last_request = current_time - self.rate_limit_state["last_request_time"]
        if time_since_last_request < (60.0 / self.config.rate_limit_requests_per_minute):
            sleep_time = (
                60.0 / self.config.rate_limit_requests_per_minute
            ) - time_since_last_request
            time.sleep(sleep_time)

        self.rate_limit_state["last_request_time"] = time.time()
        self.rate_limit_state["request_count"] += 1

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response and raise appropriate errors."""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"Rate limit exceeded by server. Retry after {retry_after} seconds",
                retry_after=retry_after,
            )

        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed", {"status_code": response.status_code}
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"message": response.text}

            error_message = error_data.get("message", f"HTTP {response.status_code}")
            error_data.get("code", "UNKNOWN_ERROR")

            raise APIError(error_message, response.status_code, error_data)

        try:
            return response.json()
        except ValueError:
            return {"data": response.text}

    def _retry_request(self, request_func, *args, **kwargs) -> Any:
        """Execute a request with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                self._check_rate_limit()
                return request_func(*args, **kwargs)
            except RateLimitError as e:
                if attempt == self.config.max_retries:
                    raise
                last_error = e
                time.sleep(e.retry_after or self.config.retry_delay_seconds)
            except (APIError, AuthenticationError) as e:
                if attempt == self.config.max_retries:
                    raise
                last_error = e
                time.sleep(self.config.retry_delay_seconds * (2**attempt))  # Exponential backoff
            except Exception as e:
                if attempt == self.config.max_retries:
                    raise
                last_error = e
                time.sleep(self.config.retry_delay_seconds)

        if last_error:
            raise last_error

    def get(
        self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Make GET request with retry logic."""

        def _make_request():
            response = self.client.get(url, params=params, headers=headers or {})
            return self._handle_response(response)

        return self._retry_request(_make_request)

    def post(self, url: str, data: Any, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Make POST request with retry logic."""

        def _make_request():
            response = self.client.post(
                url,
                json=data if isinstance(data, dict) else None,
                content=data if not isinstance(data, dict) else None,
                headers=headers or {},
            )
            return self._handle_response(response)

        return self._retry_request(_make_request)

    def put(self, url: str, data: Any, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Make PUT request with retry logic."""

        def _make_request():
            response = self.client.put(
                url,
                json=data if isinstance(data, dict) else None,
                content=data if not isinstance(data, dict) else None,
                headers=headers or {},
            )
            return self._handle_response(response)

        return self._retry_request(_make_request)

    def delete(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Make DELETE request with retry logic."""

        def _make_request():
            response = self.client.delete(url, headers=headers or {})
            return self._handle_response(response)

        return self._retry_request(_make_request)

    def set_auth_headers(self, access_token: str) -> None:
        """Set authentication headers for subsequent requests."""
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    def clear_auth_headers(self) -> None:
        """Clear authentication headers."""
        self.client.headers.pop("Authorization", None)

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
