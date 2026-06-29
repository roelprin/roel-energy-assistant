# Changelog

## v0.4.0

Decision Engine foundation.

### Added

- New `decision_engine.py` module.
- New `Decision Engine` sensor.
- One central decision object with status, advice, score, reasons, daily plan, market status and grid status.

### Notes

This is a safe foundation release. The current stable analyzer remains active and the Decision Engine wraps it. Future versions can move more logic into the Decision Engine without changing dashboards or automations.

## v0.3.3

Stabilization release.
