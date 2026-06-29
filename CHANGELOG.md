# Changelog

## v0.4.2

Bugfix / Cleanup & Stability release.

### Fixed

- `Briefing` showing `Unknown`.
- `GoodWe advies` showing `Unknown`.
- `Aanbevolen exportlimiet` showing `Unknown`.
- Missing fallback values in Decision Engine output.

### Improved

- `decision_engine.py` is now the single source of truth for REA decisions.
- All GoodWe-related fields are always present in the decision output.
- More specific data quality states:
  - `ok`
  - `missing_price`
  - `missing_p1_power`
  - `missing_goodwe_export_limit`

## v0.4.1

Anti Feed-In / GoodWe recommendation.

## v0.4.0

Decision Engine foundation.
