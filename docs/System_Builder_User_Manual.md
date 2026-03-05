# Gambling Excellence - System Builder User Manual

## 1) Purpose
This manual explains how to use the **System Builder** to create, test, and save your own roulette betting systems.

The app is organized into 3 screens:
- **Board**: table view and chip placement.
- **System Creator**: Sections 1-3 (Metrics, Triggers, Actions).
- **Testing / Evaluation**: Section 4 (Modes / Session, Wheel Select, spin application, logs).

The builder is organized into 4 sections:
1. **Metrics**
2. **Triggers**
3. **Actions**
4. **Modes / Session**

Under the hood, your system is a list of rules:

`IF <condition> THEN <action> (optional mode switch)`


## 2) Core Concepts
Before building, understand these terms:

- **Target**: A bet location on the board (for example `column_1`, `dozen_2`, `outside_red`).
- **Metric**: A value the app tracks (for example `loss_streak`, `session_profit`, `miss_streak(column_1)`).
- **Trigger**: The condition that decides when a rule should fire.
- **Action**: What the app does when a trigger fires (set bet amount, clear bets, switch mode, etc.).
- **Mode**: Strategy state (`standard`, `recovery`, `progression`, `repeat`) used to control which rules are active.


## 3) Quick Start (First System)
Use this sequence to create your first automated system:

1. Go to **Testing / Evaluation** and open **4) Modes / Session**.
2. Set **Wheel Select** (`American (0/00)` or `European (0)`).
3. Set **Start bankroll** (example: `10000`) and click **Reset Session**.
4. Go to **System Creator**.
5. In **1) Metrics**, add targets to monitor (start with `column_1`, `column_2`, `column_3`).
6. In **2) Triggers**, choose a trigger condition.
7. In **3) Actions**, choose what should happen when that trigger is true.
8. Click **Add Rule**.
9. Return to **Testing / Evaluation**, enter a spin result and click **Apply** (or click **Random**).
10. Watch **Session Status** and the **log** to see which rules fired.
11. Click **Save JSON** to keep your system.


## 4) Section-by-Section Guide

## 4.1) Metrics
Use Metrics to decide which targets should have hit/miss counters tracked.

- Add a target with **Add**.
- Remove selected target with **Remove**.
- Targets are internal IDs. Common examples:
  - `column_1`, `column_2`, `column_3`
  - `dozen_1`, `dozen_2`, `dozen_3`
  - `outside_red`, `outside_black`, `outside_even`, `outside_odd`, `outside_1_18`, `outside_19_36`

Tracked per monitored target:
- `hit_streak`
- `miss_streak`
- `spins_since_hit`
- `hits_total`
- `miss_total`


## 4.2) Triggers
Define when a rule should run.

- **Mode scope**:
  - `any` = rule can run in any mode
  - `standard`, `recovery`, `progression`, `repeat` = rule only runs in that mode
- **Metric**:
  - Global/session metrics:
    - `win_streak`
    - `loss_streak`
    - `spin_count`
    - `bankroll`
    - `session_profit`
    - `drawdown`
    - `last_spin_net`
  - Target metrics (need a target selected):
    - `hit_streak`
    - `miss_streak`
    - `spins_since_hit`
    - `hits_total`
    - `miss_total`
- **Op**: `>=`, `>`, `<=`, `<`, `==`, `!=`
- **Value**: integer threshold for comparison
- **Priority**:
  - Higher priority runs first.
  - If priorities tie, older rule ID runs first.


## 4.3) Actions
Choose what the system does when the trigger is true.

Available actions:
- `set_bet_amount`
  - **Target** required.
  - **Value** = total dollar amount to set on that target.
  - If value is `0`, that target is cleared.
- `clear_all_bets`
  - Clears all placed bets.
- `switch_mode`
  - **Target** must be one of `standard`, `recovery`, `progression`, `repeat`.
- `set_chip_denom`
  - **Value** must be one of: `1`, `5`, `25`, `100`, `500`, `1000`.
  - Changes currently selected chip denomination for manual betting.

Optional:
- **Optional mode switch** can be set separately and runs after the action.


## 4.4) Modes / Session
Use this panel to control the active session.

- **Wheel Select**:
  - `American (0/00)` allows `00`, `0`, and `1-36`.
  - `European (0)` allows `0` and `1-36` only.
- **Active mode + Set**: manually force current mode.
- **Start bankroll + Reset Session**:
  - Resets spins, streaks, bankroll tracking, and target counters.
  - Keeps your rule list.
- **Spin result + Apply**:
  - Accepts values based on **Wheel Select**.
- **Random**:
  - Applies a randomly generated spin.
- **Save JSON / Load JSON**:
  - Save and reload your strategy configuration.


## 5) Rule Evaluation Order (Important)
On every applied spin, the app does this:

1. Settles current bets and computes spin net result.
2. Updates bankroll, streaks, and monitored target counters.
3. Evaluates rules by priority order.
4. Executes matching rules.
5. Stops after **up to 3 fired rules per spin**.

This max-fire limit prevents runaway rule loops in one spin.


## 6) Strategy JSON (Save/Load)
Saving creates a JSON file with:
- `version`
- `start_bankroll`
- `current_mode`
- `monitored_targets`
- `rules`

The JSON is meant for strategy configuration. It does not act as full session replay.


## 7) Worked Example: Simple Column Recovery
Goal: Bet a column after it has missed 6 spins in a row, then return to standard after a win.

### Step A: Monitor a target
Add `column_1` in **Metrics**.

### Step B: Add entry rule
Trigger:
- Mode scope: `standard`
- Metric: `miss_streak`
- Metric target: `column_1`
- Op: `>=`
- Value: `6`
- Priority: `80`

Action:
- Action: `set_bet_amount`
- Target: `column_1`
- Value: `25`
- Optional mode switch: `progression`

Click **Add Rule**.

### Step C: Add exit rule
Trigger:
- Mode scope: `progression`
- Metric: `last_spin_net`
- Op: `>`
- Value: `0`
- Priority: `90`

Action:
- Action: `switch_mode`
- Target: `standard`
- Optional mode switch: blank

Click **Add Rule**.

### Step D: Add safety rule
Trigger:
- Mode scope: `any`
- Metric: `drawdown`
- Op: `>=`
- Value: `300`
- Priority: `100`

Action:
- Action: `clear_all_bets`
- Optional mode switch: `recovery`

Click **Add Rule**.


## 8) Troubleshooting
- **“Invalid target” when adding rule**
  - Use a target that exists on the board list.
- **Rule does not fire**
  - Check mode scope, operator, threshold, and priority.
  - Confirm target metrics have valid target IDs.
- **No chips appear after set_bet_amount**
  - Verify value is greater than 0 and target is valid.
- **Unexpected mode behavior**
  - Remember both `switch_mode` action and optional mode switch can change mode.


## 9) Best Practices
1. Start with 2-3 rules only, then expand.
2. Use high-priority safety rules (drawdown, bankroll floor).
3. Separate entry and exit logic by mode.
4. Use clear naming in your own notes for each rule’s intent.
5. Save versions often (`strategy_v1.json`, `strategy_v2.json`, etc.).


## 10) Responsible Use
No system guarantees profit. Use bankroll limits, stop conditions, and clear risk controls at all times.
