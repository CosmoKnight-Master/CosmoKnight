# System Validator Agent Spec

## Purpose
Continuously verify roulette bet coverage and payout logic to prevent regressions in Board.py and future engine modules.

## Scope (Phase 1)
- Validate `spot_id -> covered outcomes` mapping correctness.
- Validate net math consistency for each outcome under deterministic bet snapshots.
- Validate American table support including `0` and `00`.

## Inputs
- `Board.py`
- Strategy snapshots serialized from `strategy_config` entries.

## Outputs
- JSON report (`reports/system_validator_report.json`)
- Non-zero exit code on failure for CI/background scheduler.

## Run Cadence
- Trigger on every commit touching betting logic.
- Nightly scheduled run against a curated regression suite.

## Pass/Fail Rules
- Every tested `spot_id` must return expected covered outcomes.
- For each scenario, `net = total_return - total_stake` must match expected value.
- No unhandled `spot_id` patterns in active strategy configs.

## Minimum Regression Suite
- Straight bet win/loss (`straight_17`).
- Split bet win/loss (`split_h_17_20` style).
- Corner win/loss.
- Street and sixline win/loss.
- Column/dozen/outside win/loss.
- Zero-family bets (`split_0_00`, trio variants, topline, basket).

## Operational Notes
- Keep this agent deterministic for repeatable debugging.
- Treat any payout-table change as high-risk and require validator pass before release.
- Store failing scenario payloads for exact replay.
