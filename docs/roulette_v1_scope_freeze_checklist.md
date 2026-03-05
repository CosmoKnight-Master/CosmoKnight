# Roulette V1 Scope Freeze Checklist

## Purpose
Use this checklist to lock V1 scope and prevent feature drift.

- Product goal: Deliver a stable Windows V1 beta that feels excellent, trustworthy, and easy to use.
- Scope window: `2026-03-05` to V1 beta ship.

## Scope Rules
- Only one active build goal at a time.
- Every new idea must be put in `Later` unless it replaces an in-scope item.
- In-scope items cannot expand unless a current item is removed.
- Out-of-scope items are tracked but not built in this cycle.

## In-Scope Features (V1)
- [ ] Board normalization to American `000` footprint baseline.
- [ ] Left spacer support for non-`000` layouts to keep board size consistent.
- [ ] Settings foundation:
  - [ ] `board-settings.schema.json` (versioned).
  - [ ] `settings.default.json`.
  - [ ] Load, validate, save flow.
  - [ ] Migration hook for future settings versions.
- [ ] Hover popup behavior controls:
  - [ ] Enable or disable.
  - [ ] Compact or detailed mode.
  - [ ] Delay control.
- [ ] Core streak counters for:
  - [ ] Dozens.
  - [ ] Columns.
  - [ ] Even-money bets.
  - [ ] Toggle display on or off.
- [ ] Rules-safe handling for edge cases:
  - [ ] `0/00/000`.
  - [ ] French `en prison` behavior where applicable.

## Explicitly Out of Scope (V1)
- [ ] Full wheel animation popup.
- [ ] Advanced wheel texture rendering.
- [ ] Creator distribution program tooling.
- [ ] macOS/Linux/mobile ports.
- [ ] Multi-tier pricing mechanics.
- [ ] Non-essential UI experiments not tied to V1 acceptance criteria.

## Quality Gates (Must Pass)
- [ ] No critical rule regressions in spin evaluation.
- [ ] No settings load/save data loss.
- [ ] No layout break on supported board types.
- [ ] No blocker bug open at beta cut.
- [ ] User flow from launch to first spin completes without workaround.

## Scope Freeze Sign-Off
- Scope freeze date:
- Version tag:
- Owner:
- Notes:

## Change Control (After Freeze)
Any new feature request requires all fields:
- Request:
- Why now:
- What in-scope item is removed:
- Risk if deferred:
- Decision (Approve/Reject):

