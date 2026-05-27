from __future__ import annotations

from profetiq_forecaster import ProfetiQForecaster


def main() -> None:
    client = ProfetiQForecaster()
    entities = client.entities(level="model", segment="premium")
    if not entities:
        raise SystemExit("No forecast entities returned.")

    entity = entities[0]
    forecast = client.forecast(
        level="model",
        entity_id=entity["entity_id"],
        horizons=[1, 2, 3],
    )
    print(forecast)


if __name__ == "__main__":
    main()
