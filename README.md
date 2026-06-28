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
