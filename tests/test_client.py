from __future__ import annotations

from typing import Any

from profetiq_forecaster import ProfetiQForecaster, load_customer_sales_forecast_csv


def test_production_model_forecast_payload_shape() -> None:
    client = ProfetiQForecaster(api_token="pfq_test")
    captured: dict[str, Any] = {}

    def fake_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        captured.update({"method": method, "path": path, **kwargs})
        return {"forecast_type": "production_customer_sales", "points": []}

    client._request = fake_request  # type: ignore[method-assign]
    result = client.forecast(
        level="model",
        make="BYD",
        model="Seal",
        segment="premium",
        customer_sales_forecast=[
            {
                "make": "BYD",
                "model": "Seal",
                "forecast_quarter": "2026-Q2",
                "forecasted_sells_units": 2600,
            }
        ],
    )

    assert result["forecast_type"] == "production_customer_sales"
    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/forecasts"
    payload = captured["json"]
    assert payload["level"] == "model"
    assert payload["target"] == "registrations"
    assert payload["customer_sales_forecast"][0]["model"] == "Seal"


def test_production_make_forecast_payload_shape() -> None:
    client = ProfetiQForecaster(api_token="pfq_test")
    captured: dict[str, Any] = {}

    def fake_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        captured.update({"method": method, "path": path, **kwargs})
        return {"forecast_type": "production_customer_sales", "points": []}

    client._request = fake_request  # type: ignore[method-assign]
    client.forecast(
        level="make",
        make="BYD",
        segment="mass",
        customer_sales_forecast=[
            {"make": "BYD", "forecast_quarter": "2026-Q2", "forecasted_sells_units": 12000}
        ],
        wsi_market="UK&I",
        vehicle_class="Passenger",
    )

    payload = captured["json"]
    assert payload["level"] == "make"
    assert payload["target"] == "registrations"
    assert payload["wsi_market"] == "UK&I"
    assert "model" not in payload["customer_sales_forecast"][0]


def test_csv_helper_loads_make_and_model_files(tmp_path) -> None:
    model_path = tmp_path / "model.csv"
    model_path.write_text(
        "make,model,forecast_quarter,forecast_units\nBYD,Seal,2026-Q2,2600\n",
        encoding="utf-8",
    )
    make_path = tmp_path / "make.csv"
    make_path.write_text(
        "make,forecast_quarter,units\nBYD,2026-Q2,12000\n",
        encoding="utf-8",
    )

    model_rows = load_customer_sales_forecast_csv(model_path, level="model")
    make_rows = load_customer_sales_forecast_csv(make_path, level="make")

    assert model_rows == [
        {
            "make": "BYD",
            "model": "Seal",
            "forecast_quarter": "2026-Q2",
            "forecasted_sells_units": 2600.0,
        }
    ]
    assert make_rows == [
        {
            "make": "BYD",
            "forecast_quarter": "2026-Q2",
            "forecasted_sells_units": 12000.0,
        }
    ]


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
