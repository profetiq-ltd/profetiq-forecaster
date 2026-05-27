# ProfetiQ Forecaster

Python SDK and examples for the ProfetiQ Forecaster API.

ProfetiQ Forecaster helps subscription customers forecast UK vehicle segment market-share movement and observed registration demand for the next three quarters. The product uses current/latest ProfetiQ WSI Brand Attractiveness and Brand Strength inputs to parameterize an ETS-style movement model.

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

The recommended workflow is a scenario forecast. You provide:

- vehicle segment: `mass`, `premium`, or `luxury`
- make/model and origin quarter so the API can resolve ProfetiQ Brand Attractiveness and Brand Strength from proprietary WSI
- your constrained customer sales forecast for Q+1 to Q+3

The model is trained from historical UK DVLA registrations and ProfetiQ WSI at make + model + segment grain. At scenario inference time, make and model identity are not model features. Movement is driven by segment, `wsi_ba`, and `wsi_bs`.

You may also pass `wsi_ba` and `wsi_bs` explicitly. If either is omitted, the API resolves both values from the ProfetiQ WSI dataset using make/model/segment/quarter, then runs the forecast only from the resolved BA/BS values and segment.

Each customer forecast row must include either:

- `constrained_segment_share`, or
- `constrained_units` plus `segment_total_units`

The response separates:

- `customer_constrained`
- `profetiq_unconstrained`
- `delta_to_customer`

Entity forecasts are still available for compatibility, but scenario forecasts are the product workflow for customer-specific constrained forecasts.

## Scenario Forecast

```python
from profetiq_forecaster import ProfetiQForecaster

client = ProfetiQForecaster()

forecast = client.scenario_forecast(
    segment="premium",
    make="BMW",
    model="X3",
    origin_quarter="2025-Q3",
    origin_segment_share=0.0226,
    customer_forecast=[
        {
            "horizon": 1,
            "quarter": "2025-Q4",
            "constrained_segment_share": 0.021,
            "segment_total_units": 110000,
        },
        {
            "horizon": 2,
            "quarter": "2026-Q1",
            "constrained_segment_share": 0.020,
            "segment_total_units": 105000,
        },
        {
            "horizon": 3,
            "quarter": "2026-Q2",
            "constrained_segment_share": 0.022,
            "segment_total_units": 120000,
        },
    ],
)

for point in forecast["points"]:
    print(point["forecast_quarter"])
    print("customer", point["customer_constrained"]["segment_share"])
    print("profetiq", point["profetiq_unconstrained"]["segment_share"])
    print("delta", point["delta_to_customer"]["segment_share"])
```

Make/model labels are returned for readability. They do not alter scenario output when segment, BA/BS, and constrained forecasts are identical.

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

This endpoint is useful for inspecting the proprietary BA/BS values the scenario forecast will use. The forecast calculation still uses only segment plus the resolved BA/BS values.

## Discover Entities

```python
from profetiq_forecaster import ProfetiQForecaster

client = ProfetiQForecaster()

entities = client.entities(level="model", segment="premium")
for entity in entities[:5]:
    print(entity["entity_id"], entity["name"], entity["latest_quarter"])
```

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
from profetiq_forecaster import ProfetiQForecaster

client = ProfetiQForecaster()

entities = client.entities(level="model", segment="premium")
entity = entities[0]

forecast = client.forecast(
    level="model",
    entity_id=entity["entity_id"],
    horizons=[1, 2, 3],
)

print(forecast["entity"])
print(forecast["origin"])
for point in forecast["points"]:
    print(
        point["forecast_quarter"],
        point["segment_share"],
        point["registrations"],
    )
```

Typical response fields:

- `forecast_id`
- `entity`
- `origin.quarter`
- `origin.wsi_ba`
- `origin.wsi_bs`
- `points[].forecast_quarter`
- `points[].horizon`
- `points[].segment_share`
- `points[].registrations`
- `points[].segment_total_registrations_baseline`

## Make-Level Forecast

Make-level forecasts are segment-specific. A single make may appear in multiple segments if different models belong to different segments.

```python
client = ProfetiQForecaster()

forecast = client.forecast(
    level="make",
    make="BMW",
    segment="premium",
    horizons=[1, 2, 3],
)

for point in forecast["points"]:
    print(point)
```

If multiple entities match your request, provide `entity_id` from `client.entities(...)` to remove ambiguity.

## Backtest

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

job = client.scenario_forecast(
    segment="premium",
    make="BMW",
    model="X3",
    origin_quarter="2025-Q3",
    customer_forecast=[
        {"horizon": 1, "constrained_segment_share": 0.021},
        {"horizon": 2, "constrained_segment_share": 0.020},
        {"horizon": 3, "constrained_segment_share": 0.022},
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
- `POST /v1/forecasts` for scenario and entity forecasts
- `POST /v1/backtests`
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
- The selected make/model/segment is unavailable in the current forecast panel.
- Scenario rows using `constrained_units` must also provide `segment_total_units`.
- Scenario BA/BS values must be finite numbers.

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
