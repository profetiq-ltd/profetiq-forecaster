# Contributing

ProfetiQ Forecaster is published primarily as a customer SDK and examples repository.

## Issues

Use GitHub issues for SDK usability problems, documentation gaps, and reproducible client-side errors. Do not include API tokens, customer data, private forecasts, or proprietary datasets in an issue.

## Pull Requests

Pull requests are welcome for:

- documentation improvements
- example fixes
- SDK ergonomics
- typing improvements
- packaging fixes

Pull requests must not add:

- API tokens or secrets
- raw DVLA data
- WSI datasets
- Common Crawl code
- build-index code
- proprietary backend or forecasting internals

## Local Validation

Run:

```bash
python3 -m py_compile profetiq_forecaster/client.py examples/forecast_pipeline.py examples/backtest_pipeline.py
python3 -m pip install -e .
python3 -c "from profetiq_forecaster import ProfetiQForecaster"
```

Live API examples require a valid paid ProfetiQ Forecaster API token.
