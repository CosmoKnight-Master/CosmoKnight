import argparse
import json
import os
import sys
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Board import RouletteBoardApp


class HeadlessVar:
    """Tiny StringVar-like shim for headless validation."""

    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


def build_headless_app() -> RouletteBoardApp:
    """Create an app instance without tkinter boot, only logic fields required for validation."""
    app = RouletteBoardApp.__new__(RouletteBoardApp)
    app.cols = 12
    app.RED_NUMBERS = RouletteBoardApp.RED_NUMBERS
    app.WHEEL_FAMILIES = RouletteBoardApp.WHEEL_FAMILIES
    app.EUROPEAN_BET_OPTIONS = RouletteBoardApp.EUROPEAN_BET_OPTIONS
    app.spots = {}
    app.bets = defaultdict(list)
    app.en_prison_pending = set()
    app.wheel_family_var = HeadlessVar(app.WHEEL_FAMILIES[0])
    app.european_bet_option_var = HeadlessVar(app.EUROPEAN_BET_OPTIONS[0])
    return app


def expected_net(total_stake: int, chip: int, payout: int, hit: bool) -> int:
    if hit:
        return chip * (payout + 1) - total_stake
    return -total_stake


def run_basic_suite() -> dict:
    app = build_headless_app()

    scenarios = [
        {"id": "straight_17", "payout": "35:1", "chip": 10, "win_outcome": 17, "lose_outcome": 18},
        {"id": "split_h_17_20", "payout": "17:1", "chip": 10, "win_outcome": 17, "lose_outcome": 18},
        {"id": "corner_17_18_20_21", "payout": "8:1", "chip": 10, "win_outcome": 21, "lose_outcome": 22},
        {"id": "street_6", "payout": "11:1", "chip": 10, "win_outcome": 18, "lose_outcome": 19},
        {"id": "sixline_6_7", "payout": "5:1", "chip": 10, "win_outcome": 20, "lose_outcome": 23},
        {"id": "column_1", "payout": "2:1", "chip": 10, "win_outcome": 34, "lose_outcome": 35},
        {"id": "dozen_2", "payout": "2:1", "chip": 10, "win_outcome": 18, "lose_outcome": 25},
        {"id": "outside_red", "payout": "1:1", "chip": 10, "win_outcome": 3, "lose_outcome": 4},
        {"id": "split_0_00", "payout": "17:1", "chip": 10, "win_outcome": "00", "lose_outcome": 1},
        {"id": "topline_0_00_1_2_3", "payout": "6:1", "chip": 10, "win_outcome": 2, "lose_outcome": 4},
        {"id": "trio_0_1_2", "payout": "11:1", "chip": 10, "win_outcome": 1, "lose_outcome": 3},
        {"id": "basket_0_1_2_3", "payout": "8:1", "chip": 10, "win_outcome": 0, "lose_outcome": 4},
    ]

    failures = []

    for sc in scenarios:
        app.spots = {sc["id"]: {"payout": sc["payout"]}}
        app.bets = defaultdict(list, {sc["id"]: [sc["chip"]]})
        payout = int(sc["payout"].split(":")[0])
        total_stake = sc["chip"]

        net_win = app._net_for_outcome(sc["win_outcome"])
        net_lose = app._net_for_outcome(sc["lose_outcome"])
        exp_win = expected_net(total_stake, sc["chip"], payout, True)
        exp_lose = expected_net(total_stake, sc["chip"], payout, False)

        if net_win != exp_win:
            failures.append(
                {
                    "scenario": sc["id"],
                    "kind": "win_net_mismatch",
                    "expected": exp_win,
                    "actual": net_win,
                    "outcome": sc["win_outcome"],
                }
            )

        if net_lose != exp_lose:
            failures.append(
                {
                    "scenario": sc["id"],
                    "kind": "lose_net_mismatch",
                    "expected": exp_lose,
                    "actual": net_lose,
                    "outcome": sc["lose_outcome"],
                }
            )

    return {
        "suite": "basic_system_validator",
        "total_scenarios": len(scenarios),
        "failed": len(failures),
        "passed": len(scenarios) - len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run roulette system validation checks.")
    parser.add_argument(
        "--report",
        default="reports/system_validator_report.json",
        help="Report output path (default: reports/system_validator_report.json)",
    )
    args = parser.parse_args()

    report = run_basic_suite()

    report_path = args.report
    report_dir = report_path.rsplit("/", 1)[0] if "/" in report_path else report_path.rsplit("\\", 1)[0]
    if report_dir and report_dir != report_path:
        import os

        os.makedirs(report_dir, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

