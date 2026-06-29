# Roel Energy Assistant

Personal Home Assistant energy assistant for Roel.

This integration uses the existing **Essent Dynamic Prices** integration as a price source and creates personal advice, scores and a daily plan.

## v0.1.0

Initial version.

### Sensors

- Advisor
- Score
- Status
- Dagplanning
- Briefing

### Binary sensors

- Goed moment
- Groot verbruik vermijden
- Goedkoop blok actief

## Required

This first version expects these Essent Dynamic Prices entities:

- `sensor.essent_dynamic_prices_stroomprijs_nu`
- `sensor.essent_dynamic_prices_stroomprijs_volgend_uur`
- `sensor.essent_dynamic_prices_gemiddelde_stroomprijs_vandaag`
- `sensor.essent_dynamic_prices_laagste_stroomprijs_vandaag`
- `sensor.essent_dynamic_prices_hoogste_stroomprijs_vandaag`
- `sensor.essent_dynamic_prices_uurprijzen_2`

## Installation

Install as a HACS custom integration or copy `custom_components/roel_energy_assistant` to Home Assistant.


## v0.2.0

Adds a richer daily planner and a longer briefing suitable for dashboards and notifications.

The `Briefing` sensor now has a full text state and exposes:

- status
- score
- stars
- recommended actions
- avoid actions
- daily plan
- reasons


## v0.3.0 - Negative prices step 1

REA now detects negative market prices and negative total prices.

New entities:

- `Marktstatus`
- `Negatieve beursprijs`
- `Negatieve totaalprijs`

This is the preparation for the next step: calculating feed-in power and loss per hour using the HomeWizard P1 meter.


## v0.3.1 - PV Analyzer

REA now reads the HomeWizard P1 net power sensor:

```yaml
sensor.p1_meter_vermogen
```

Assumption:

- Negative value = feed-in / teruglevering
- Positive value = grid import / netafname

New entities:

- Teruglevering
- Netstatus
- Verlies per uur
- Solar advisor
- Teruglevering actief


## v0.3.2 - Solar Utilization Engine

REA now estimates available solar surplus from the P1 net power sensor.

New entities:

- Zonnestroom overschot
- Virtuele batterij
- Eigen verbruik advies
- Veel zonnestroom over

The virtual battery score is based on the amount of power currently being fed back to the grid.


## v0.3.3 - Stabilization

This release focuses on stability and diagnostics.

New entities:

- Datakwaliteit
- Data OK

REA now reports whether its required P1 data is available and includes more diagnostic attributes.


## v0.4.0 - Decision Engine foundation

REA now exposes one central Decision Engine entity.

New file:

```text
custom_components/roel_energy_assistant/decision_engine.py
```

New entity:

- Decision Engine

This is the new central place for status, advice, score, reasons, daily plan, market status, grid status and feed-in information.


## v0.4.1 - Anti Feed-In / GoodWe recommendation

REA now understands your GoodWe export limit entity:

```yaml
number.goodwe_grid_export_limit
```

Range used:

- `0 W` = no export
- `10000 W` = normal/max export

New entities:

- GoodWe advies
- Aanbevolen exportlimiet
- GoodWe begrenzen aanbevolen
- Anti Feed-In actief

This version is advice-only. It does not automatically change the GoodWe export limit yet.


## v0.4.2 - Bugfix / Cleanup & Stability

This release fixes `Unknown` values for:

- Briefing
- GoodWe advies
- Aanbevolen exportlimiet

It also makes `decision_engine.py` the single source of truth for all REA decisions.
