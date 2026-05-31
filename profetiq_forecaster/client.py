from __future__ import annotations

import os
import csv
from pathlib import Path
from typing import Any, Optional

import httpx


DEFAULT_BASE_URL = "https://profetiq-api.azurewebsites.net"


class ProfetiQForecasterError(RuntimeError):
    pass


UNIT_COLUMNS = ("forecasted_sells_units", "forecasted_sales_units", "forecast_units", "units")


def load_customer_sales_forecast_csv(path: str | Path, *, level: str = "model") -> list[dict[str, Any]]:
    """Load a make-level or model-level customer sales forecast CSV."""
    if level not in {"make", "model"}:
        raise ProfetiQForecasterError("level must be 'make' or 'model'.")

    csv_path = Path(path)
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = {str(name or "").strip().lower() for name in (reader.fieldnames or [])}
        required = {"make", "forecast_quarter"}
        if level == "model":
            required.add("model")
        missing = sorted(required - headers)
        if missing:
            raise ProfetiQForecasterError(f"CSV missing required columns: {', '.join(missing)}.")
        unit_column = next((column for column in UNIT_COLUMNS if column in headers), None)
        if not unit_column:
            raise ProfetiQForecasterError(f"CSV must include one unit column: {', '.join(UNIT_COLUMNS)}.")

        for index, raw in enumerate(reader, start=2):
            row = {str(key or "").strip().lower(): value for key, value in raw.items()}
            make = str(row.get("make") or "").strip()
            model = str(row.get("model") or "").strip()
            quarter = str(row.get("forecast_quarter") or "").strip().upper()
            if not make:
                raise ProfetiQForecasterError(f"Row {index} is missing make.")
            if level == "model" and not model:
                raise ProfetiQForecasterError(f"Row {index} is missing model.")
            if not quarter:
                raise ProfetiQForecasterError(f"Row {index} is missing forecast_quarter.")
            try:
                units = float(str(row.get(unit_column) or "").replace(",", ""))
            except ValueError as exc:
                raise ProfetiQForecasterError(f"Row {index} has invalid forecast units.") from exc
            if units < 0:
                raise ProfetiQForecasterError(f"Row {index} has invalid forecast units.")
            parsed = {
                "make": make,
                "forecast_quarter": quarter,
                "forecasted_sells_units": units,
            }
            if level == "model":
                parsed["model"] = model
            rows.append(parsed)
    if not rows:
        raise ProfetiQForecasterError("CSV must contain at least one data row.")
    return rows


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
        market: Optional[str] = None,
        vehicle_class: Optional[str] = None,
        record_quarter: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        params = {}
        if level:
            params["level"] = level
        if segment:
            params["segment"] = segment
        if market:
            params["market"] = market
        if vehicle_class:
            params["vehicle_class"] = vehicle_class
        if record_quarter:
            params["record_quarter"] = record_quarter
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
        customer_sales_forecast: Optional[list[dict[str, Any]]] = None,
        wsi_market: Optional[str] = None,
        vehicle_class: Optional[str] = None,
        record_quarter: Optional[str] = None,
        horizons: Optional[list[int]] = None,
        async_job: bool = False,
    ) -> dict[str, Any]:
        if level not in {"make", "model"}:
            raise ProfetiQForecasterError("Production forecasts require level='make' or level='model'.")
        if not customer_sales_forecast:
            raise ProfetiQForecasterError("customer_sales_forecast is required for production forecasts.")
        payload: dict[str, Any] = {
            "market": "UK",
            "level": level,
            "target": "registrations",
            "entity_id": entity_id,
            "make": make,
            "model": model,
            "segment": segment,
            "customer_sales_forecast": customer_sales_forecast,
            "async_job": async_job,
        }
        if horizons:
            payload["horizons"] = horizons
        if wsi_market:
            payload["wsi_market"] = wsi_market
        if vehicle_class:
            payload["vehicle_class"] = vehicle_class
        if record_quarter:
            payload["record_quarter"] = record_quarter
        return dict(
            self._request(
                "POST",
                "/v1/forecasts",
                json=payload,
            )
        )

    def scenario_forecast(
        self,
        *,
        segment: str,
        customer_forecast: list[dict[str, Any]],
        wsi_ba: Optional[float] = None,
        wsi_bs: Optional[float] = None,
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
            "customer_forecast": customer_forecast,
        }
        optional_values = {
            "wsi_ba": wsi_ba,
            "wsi_bs": wsi_bs,
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

    def wsi_signal(
        self,
        *,
        make: str,
        segment: str,
        model: Optional[str] = None,
        quarter: Optional[str] = None,
    ) -> dict[str, Any]:
        params = {"make": make, "segment": segment}
        if model:
            params["model"] = model
        if quarter:
            params["quarter"] = quarter
        payload = self._request("GET", "/v1/wsi-signals", params=params)
        return dict(payload.get("signal") or {})

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
