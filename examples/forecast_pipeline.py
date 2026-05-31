from __future__ import annotations

from pathlib import Path

from profetiq_forecaster import ProfetiQForecaster, load_customer_sales_forecast_csv


def main() -> None:
    client = ProfetiQForecaster()

    data_dir = Path(__file__).resolve().parent / "data"
    model_rows = load_customer_sales_forecast_csv(
        data_dir / "byd_model_customer_sales_forecast_2026.csv",
        level="model",
    )
    make_rows = load_customer_sales_forecast_csv(
        data_dir / "byd_make_customer_sales_forecast_2026.csv",
        level="make",
    )

    model_forecast = client.forecast(
        level="model",
        make="BYD",
        model="Seal",
        segment="premium",
        customer_sales_forecast=model_rows,
    )
    make_forecast = client.forecast(
        level="make",
        make="BYD",
        segment="mass",
        customer_sales_forecast=make_rows,
    )
    print(model_forecast)
    print(make_forecast)


if __name__ == "__main__":
    main()
