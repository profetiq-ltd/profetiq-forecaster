from __future__ import annotations

from typing import Any

from profetiq_forecaster import ProfetiQForecaster


def test_scenario_forecast_payload_shape() -> None:
    client = ProfetiQForecaster(api_token="pfq_test")
    captured: dict[str, Any] = {}

    def fake_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        captured.update({"method": method, "path": path, **kwargs})
        return {"forecast_type": "scenario", "points": []}

    client._request = fake_request  # type: ignore[method-assign]
    result = client.scenario_forecast(
        segment="premium",
        origin_quarter="2025-Q3",
        make="BMW",
        model="X3",
        customer_forecast=[
            {"horizon": 1, "constrained_segment_share": 0.04},
            {"horizon": 2, "constrained_units": 1200, "segment_total_units": 30000},
        ],
    )

    assert result["forecast_type"] == "scenario"
    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/forecasts"
    payload = captured["json"]
    assert payload["scenario"]["segment"] == "premium"
    assert "wsi_ba" not in payload["scenario"]
    assert payload["scenario"]["customer_forecast"][1]["segment_total_units"] == 30000


def test_wsi_signal_request_shape() -> None:
    client = ProfetiQForecaster(api_token="pfq_test")
    captured: dict[str, Any] = {}

    def fake_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        captured.update({"method": method, "path": path, **kwargs})
        return {"signal": {"make": "BMW", "model": "X3", "segment": "premium"}}

    client._request = fake_request  # type: ignore[method-assign]
    result = client.wsi_signal(make="BMW", model="X3", segment="premium", quarter="2025-Q3")

    assert result["model"] == "X3"
    assert captured["method"] == "GET"
    assert captured["path"] == "/v1/wsi-signals"
    assert captured["params"]["quarter"] == "2025-Q3"
