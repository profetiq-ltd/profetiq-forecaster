from __future__ import annotations

from profetiq_forecaster import ProfetiQForecaster


def main() -> None:
    client = ProfetiQForecaster()
    forecast = client.scenario_forecast(
        segment="premium",
        make="BMW",
        model="X3",
        origin_quarter="2025-Q3",
        origin_segment_share=0.0226,
        customer_forecast=[
            {"horizon": 1, "quarter": "2025-Q4", "constrained_segment_share": 0.021},
            {"horizon": 2, "quarter": "2026-Q1", "constrained_segment_share": 0.020},
            {"horizon": 3, "quarter": "2026-Q2", "constrained_segment_share": 0.022},
        ],
    )
    print(forecast)


if __name__ == "__main__":
    main()
