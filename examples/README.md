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
- loads the BYD make-level and model-level sample customer sales forecast CSVs
- lets the API resolve current-quarter BA/BS from ProfetiQ SQLite WSI
- sends production `registrations` forecasts for make-level and model-level flows
- prints profetiQ forecast units, customer units, and gap output

Sample files live in `examples/data/`:

- `byd_model_customer_sales_forecast_2026.csv`
- `byd_make_customer_sales_forecast_2026.csv`

The BYD values are synthetic manual-test inputs informed by public BYD UK growth reporting, including BYD UK's Q1 2026 sales update and published 2025 UK sales coverage. They are not official BYD or ProfetiQ forecasts.

## Backtest Pipeline

```bash
python examples/backtest_pipeline.py
```

The script runs the legacy model-level backtest endpoint and prints summary accuracy rows. Backtests require the API to be configured with `FORECASTER_USE_LEGACY_PANEL=true`.

## Notebook

Open:

```bash
examples/notebooks/forecast_pipeline.ipynb
```

The notebook follows the same flow as the forecast example.

## Notes

Live requests require a valid paid API token. The examples do not include proprietary WSI data, DVLA data, Common Crawl code, or build-index code.
