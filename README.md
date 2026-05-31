# ProfetiQ Forecaster

Python SDK and examples for the ProfetiQ Forecaster API.

ProfetiQ Forecaster helps subscription customers compare their current sales forecast with a ProfetiQ BA/BS-adjusted demand forecast at make or model level. The product uses current/latest ProfetiQ WSI Brand Attractiveness and Brand Strength values from production SQLite-backed WSI tables.

This public repository contains only the client SDK, usage examples, and setup instructions. It does not contain ProfetiQ's proprietary WSI generation, Common Crawl ingestion, build-index code, model-training data, DVLA/WSI raw data, backend auth/payment services, or private forecasting internals.

## What You Need

- Python 3.9 or newer.
- A paid ProfetiQ Forecaster subscription.
- A ProfetiQ Forecaster API token, issued from the ProfetiQ user portal after subscription approval.

API tokens usually start with `pfq_`. Treat them like passwords.

## Clone And Install

```bash
git clone https://github.com/profetiq-ltd/profetiq-forecaster.git
cd profetiq-forecaster
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows PowerShell:

```powershell
git clone https://github.com/profetiq-ltd/profetiq-forecaster.git
cd profetiq-forecaster
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## Configure

Set your API token and API base URL:

```bash
export PROFETIQ_FORECASTER_API_TOKEN="pfq_..."
export PROFETIQ_FORECASTER_BASE_URL="https://profetiq-api.azurewebsites.net"
```

PowerShell:

```powershell
$env:PROFETIQ_FORECASTER_API_TOKEN="pfq_..."
$env:PROFETIQ_FORECASTER_BASE_URL="https://profetiq-api.azurewebsites.net"
```

You can also pass these directly:

```python
from profetiq_forecaster import ProfetiQForecaster

client = ProfetiQForecaster(
    api_token="pfq_...",
    base_url="https://profetiq-api.azurewebsites.net",
)
```

## Forecasting Logic

The recommended workflow is a production customer sales forecast. You provide:

- `level="make"` or `level="model"`
- a selected make, or make + model
- the relevant segment when multiple entities match
- a customer sales forecast CSV or list of rows

Make-level forecasts resolve BA/BS from `brand_wsi_make`. Model-level forecasts resolve BA/BS from `brand_wsi_model`. The API returns the raw BA/BS values, cohort percentiles, source table, market, vehicle class, signal quarter, ProfetiQ forecast units, customer units, and gap fields.

CSV columns:

- make-level: `make`, `forecast_quarter`, and one unit column
- model-level: `make`, `model`, `forecast_quarter`, and one unit column

Accepted unit columns are `forecasted_sells_units`, `forecasted_sales_units`, `forecast_units`, or `units`.

Scenario forecasts and DVLA-panel backtests are legacy/internal compatibility workflows. Production API and SDK usage should use the SDK `forecast()` method, which sends `target="registrations"` automatically.

The repository includes synthetic BYD manual-test CSVs under `examples/data/`. They are informed by public BYD UK growth reporting, including BYD UK's Q1 2026 sales update and published 2025 UK sales coverage, but they are not official BYD or ProfetiQ forecasts.

## Resolve WSI Signal

```python
signal = client.wsi_signal(
    make="BMW",
    model="X3",
    segment="premium",
    quarter="2025-Q3",
)

print(signal["wsi_ba"], signal["wsi_bs"])
```

This endpoint is useful for inspecting the proprietary BA/BS values that production forecasts resolve from the current WSI tables.

## Discover Entities

```python
from profetiq_forecaster import ProfetiQForecaster

client = ProfetiQForecaster()

entities = client.entities(level="model", segment="premium")
for entity in entities[:5]:
    print(entity["entity_id"], entity["name"], entity["latest_quarter"])
```

Optional filters include `market`, `vehicle_class`, and `record_quarter`. Defaults are the latest dashboard quarter, `market="UK&I"`, and `vehicle_class="Passenger"`.

Supported levels:

- `model`
- `make`

Supported segments:

- `mass`
- `premium`
- `luxury`

Trim-level forecasting is not supported in v1.

## Model-Level Forecast

```python
from pathlib import Path

from profetiq_forecaster import ProfetiQForecaster, load_customer_sales_forecast_csv

client = ProfetiQForecaster()

customer_rows = load_customer_sales_forecast_csv(
    Path("examples/data/byd_model_customer_sales_forecast_2026.csv"),
    level="model",
)

forecast = client.forecast(
    level="model",
    make="BYD",
    model="Seal",
    segment="premium",
    customer_sales_forecast=customer_rows,
)

print(forecast["entity"])
print(forecast["origin"])
for point in forecast["points"]:
    print(
        point["forecast_quarter"],
        point["registrations"],
        point["customer_forecast_units"],
        point["gap_units"],
    )
```

Typical response fields:

- `forecast_id`
- `entity`
- `origin.record_quarter`
- `origin.wsi_ba`
- `origin.wsi_bs`
- `origin.wsi_ba_percentile`
- `origin.wsi_bs_percentile`
- `origin.source_table`
- `points[].forecast_quarter`
- `points[].horizon`
- `points[].registrations`
- `points[].customer_forecast_units`
- `points[].gap_units`
- `points[].gap_percent`

## Make-Level Forecast

Make-level forecasts are segment-specific. A single make may appear in multiple segments if different models belong to different segments.

```python
from pathlib import Path

from profetiq_forecaster import ProfetiQForecaster, load_customer_sales_forecast_csv

client = ProfetiQForecaster()

customer_rows = load_customer_sales_forecast_csv(
    Path("examples/data/byd_make_customer_sales_forecast_2026.csv"),
    level="make",
)

forecast = client.forecast(
    level="make",
    make="BYD",
    segment="mass",
    customer_sales_forecast=customer_rows,
)

for point in forecast["points"]:
    print(point)
```

If multiple entities match your request, provide `entity_id` from `client.entities(...)` to remove ambiguity.

## Backtest

Backtests are legacy/internal compatibility endpoints. They require the backend to be configured with `FORECASTER_USE_LEGACY_PANEL=true`.

```python
client = ProfetiQForecaster()

result = client.backtest(level="model", horizons=[1, 2, 3])

for row in result["accuracy"]:
    print(row)

for row in result["registration_accuracy"]:
    print(row)
```

Backtest responses include:

- segment-share accuracy
- registration accuracy
- accuracy by segment
- mapping summary
- model metadata

## Async Jobs

For larger jobs, request async execution and poll the job endpoint:

```python
client = ProfetiQForecaster()

job = client.forecast(
    level="model",
    make="BYD",
    model="Seal",
    segment="premium",
    customer_sales_forecast=[
        {"make": "BYD", "model": "Seal", "forecast_quarter": "2026-Q2", "forecasted_sells_units": 2600},
        {"make": "BYD", "model": "Seal", "forecast_quarter": "2026-Q3", "forecasted_sells_units": 3000},
    ],
    async_job=True,
)

job_id = job["job_id"]

while True:
    status = client.job(job_id)
    print(status["status"])
    if status["status"] in {"completed", "failed"}:
        break
```

## API Endpoints

The SDK wraps these API endpoints:

- `GET /v1/entities`
- `GET /v1/wsi-signals`
- `POST /v1/forecasts` for make-level and model-level production customer sales forecasts
- `POST /v1/backtests` for legacy/internal compatibility
- `GET /v1/jobs/{job_id}`
- `GET /v1/tokens`
- `POST /v1/tokens`

Token creation is normally handled in the ProfetiQ user portal. SDK users only need the issued token.

## Common Errors

`401 Unauthorized`

- Token is missing, invalid, expired, or revoked.
- Confirm `PROFETIQ_FORECASTER_API_TOKEN` is set.

`403 Forbidden`

- A paid subscription or active entitlement is required.

`400 Bad Request`

- The entity cannot be resolved.
- The selected make/model/segment is unavailable in the current WSI table.
- The customer sales forecast is missing required CSV fields.
- No customer sales forecast rows match the selected make/model.
- BA or BS is missing for the selected WSI entity.

`422 Unprocessable Entity`

- Request shape is invalid.
- Trim-level forecasting was requested; v1 supports make and model only.

## Token Security

- Do not commit API tokens to Git.
- Prefer environment variables or a secret manager.
- Rotate tokens if they are exposed.
- Use separate tokens for production, notebooks, and CI where possible.

## Repository Boundaries

Included:

- Python SDK.
- Simple examples.
- Notebook-style starter workflow.
- Public API usage docs.

Excluded:

- Common Crawl pipeline.
- Build-index code.
- WSI generation code.
- DVLA data files.
- Raw or generated WSI datasets.
- Backend auth/payment internals.
- Proprietary forecasting model internals.

## Support

For subscription, token, or API-access issues, contact ProfetiQ through your customer support channel.
