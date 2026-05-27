# ProfetiQ Forecaster

Python SDK and examples for the ProfetiQ Forecaster API.

ProfetiQ Forecaster helps subscription customers forecast UK vehicle segment market-share movement and observed registration demand for the next three quarters. The product uses ProfetiQ WSI signals, including current/latest available Brand Attractiveness and Brand Strength, to parameterize an ETS-style forecasting model.

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

The API forecasts `segment_share` for UK vehicle entities. Segment share is calculated within the model's assigned vehicle segment, such as `mass`, `premium`, or `luxury`.

For each forecast, the API:

1. Finds the selected make or model entity.
2. Uses the latest/current available WSI quarter for that entity.
3. Reads that quarter's Brand Attractiveness and Brand Strength signals.
4. Uses those signals to parameterize ETS market-share movement.
5. Returns forecasts for the requested horizons, normally Q+1, Q+2, and Q+3.
6. Derives registration forecasts from predicted segment share and a segment registration baseline.

Manual scenario inputs for arbitrary Brand Attractiveness and Brand Strength values are not part of this SDK version. The service uses the current/latest ProfetiQ WSI values available to the API.

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

job = client.forecast(
    level="model",
    entity_id="model:example:example:premium",
    horizons=[1, 2, 3],
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
- `POST /v1/forecasts`
- `POST /v1/backtests`
- `GET /v1/jobs/{job_id}`

Token management happens in the ProfetiQ user portal and is not required for normal SDK use.

## Common Errors

`401 Unauthorized`

- Token is missing, invalid, expired, or revoked.
- Confirm `PROFETIQ_FORECASTER_API_TOKEN` is set.

`403 Forbidden`

- A paid subscription or active entitlement is required.

`400 Bad Request`

- The entity cannot be resolved.
- The selected make/model/segment is unavailable in the current forecast panel.

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
