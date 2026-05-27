from __future__ import annotations

from profetiq_forecaster import ProfetiQForecaster


def main() -> None:
    client = ProfetiQForecaster()
    result = client.backtest(level="model", horizons=[1, 2, 3])
    for row in result.get("accuracy", []):
        print(row)


if __name__ == "__main__":
    main()
