# Contributing

Thanks for helping improve Krama's clients and integrations.

1. Open an issue first for anything larger than a small fix, so we can agree on the approach.
2. Python client (`clients/python`): standard library only for the core client; keep `pandas` and
   `great_expectations` optional. Run `pytest -q` and `ruff check` before opening a pull request.
3. Excel add-in (`integrations/excel`): keep `src/logic.js` free of Office.js so it stays unit-testable
   with `node --test`.
4. By contributing you agree that your contribution is licensed under Apache-2.0.

Ideas for new integrations (dbt, Google Sheets, Zoho, Tally exports) are especially welcome.
