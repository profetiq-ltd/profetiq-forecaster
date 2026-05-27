# Examples

These examples show how to use the public ProfetiQ Forecaster SDK.

## Setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export PROFETIQ_FORECASTER_API_TOKEN="pfq_..."
export PROFETIQ_FORECASTER_BASE_URL="https://profetiq-api.azurewebsites.net"
```

## Forecast Pipeline

```bash
python examples/forecast_pipeline.py
```

The script:

- creates a `ProfetiQForecaster` client
- lists premium model-level entities
- forecasts the first returned entity for Q+1, Q+2, and Q+3

## Backtest Pipeline

```bash
python examples/backtest_pipeline.py
```

The script runs the model-level backtest endpoint and prints summary accuracy rows.

## Notebook

Open:

```bash
examples/notebooks/forecast_pipeline.ipynb
```

The notebook follows the same flow as the forecast example.

## Notes

Live requests require a valid paid API token. The examples do not include proprietary WSI data, DVLA data, Common Crawl code, or build-index code.
