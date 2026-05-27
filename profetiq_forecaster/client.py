from __future__ import annotations

import os
from typing import Any, Optional

import httpx


DEFAULT_BASE_URL = "https://profetiq-api.azurewebsites.net"


class ProfetiQForecasterError(RuntimeError):
    pass


class ProfetiQForecaster:
    def __init__(
        self,
        *,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_token = api_token or os.getenv("PROFETIQ_FORECASTER_API_TOKEN")
        if not self.api_token:
            raise ProfetiQForecasterError("PROFETIQ_FORECASTER_API_TOKEN is required.")
        self.base_url = (base_url or os.getenv("PROFETIQ_FORECASTER_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = float(timeout)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_token}"
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, url, headers=headers, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail")
            except Exception:
                detail = response.text
            raise ProfetiQForecasterError(f"{response.status_code}: {detail}")
        return response.json()

    def entities(
        self,
        *,
        level: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        params = {}
        if level:
            params["level"] = level
        if segment:
            params["segment"] = segment
        payload = self._request("GET", "/v1/entities", params=params)
        return list(payload.get("entities") or [])

    def forecast(
        self,
        *,
        level: str = "model",
        entity_id: Optional[str] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        segment: Optional[str] = None,
        horizons: Optional[list[int]] = None,
        async_job: bool = False,
    ) -> dict[str, Any]:
        return dict(
            self._request(
                "POST",
                "/v1/forecasts",
                json={
                    "market": "UK",
                    "level": level,
                    "target": "segment_share",
                    "entity_id": entity_id,
                    "make": make,
                    "model": model,
                    "segment": segment,
                    "horizons": horizons or [1, 2, 3],
                    "async_job": async_job,
                },
            )
        )

    def scenario_forecast(
        self,
        *,
        segment: str,
        wsi_ba: float,
        wsi_bs: float,
        customer_forecast: list[dict[str, Any]],
        origin_quarter: Optional[str] = None,
        origin_segment_share: Optional[float] = None,
        origin_units: Optional[float] = None,
        origin_segment_total_units: Optional[float] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        horizons: Optional[list[int]] = None,
        async_job: bool = False,
    ) -> dict[str, Any]:
        scenario: dict[str, Any] = {
            "segment": segment,
            "wsi_ba": wsi_ba,
            "wsi_bs": wsi_bs,
            "customer_forecast": customer_forecast,
        }
        optional_values = {
            "origin_quarter": origin_quarter,
            "origin_segment_share": origin_segment_share,
            "origin_units": origin_units,
            "origin_segment_total_units": origin_segment_total_units,
            "make": make,
            "model": model,
        }
        scenario.update({key: value for key, value in optional_values.items() if value is not None})
        return dict(
            self._request(
                "POST",
                "/v1/forecasts",
                json={
                    "market": "UK",
                    "level": "model",
                    "target": "segment_share",
                    "horizons": horizons or [1, 2, 3],
                    "async_job": async_job,
                    "scenario": scenario,
                },
            )
        )

    def backtest(
        self,
        *,
        level: str = "model",
        horizons: Optional[list[int]] = None,
        async_job: bool = False,
    ) -> dict[str, Any]:
        return dict(
            self._request(
                "POST",
                "/v1/backtests",
                json={
                    "market": "UK",
                    "level": level,
                    "horizons": horizons or [1, 2, 3],
                    "async_job": async_job,
                },
            )
        )

    def job(self, job_id: str) -> dict[str, Any]:
        return dict(self._request("GET", f"/v1/jobs/{job_id}"))
