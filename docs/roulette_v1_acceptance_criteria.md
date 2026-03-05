# Roulette V1 Acceptance Criteria

## How To Use
- A feature is done only when all criteria in its section pass.
- If any criterion fails, the feature returns to active work.
- Use `Pass`, `Fail`, or `N/A` for each line during review.

## Feature 1: Board Normalization
### Functional Criteria
- [ ] All supported wheel boards render on one shared base canvas size (American `000` footprint).
- [ ] Non-`000` boards include left-side spacer area and do not stretch betting cells.
- [ ] Bet marker coordinates still map to correct logical bet targets.
- [ ] Existing chip placement remains correct after normalization.

### UX Criteria
- [ ] `SPIN`, `+`, `-` action area anchors consistently in bottom-left below zero region.
- [ ] No overlap between action controls and board hit areas.
- [ ] Text, chips, and markers remain readable at normal window size.

### Regression Criteria
- [ ] No click-target offset bugs introduced.
- [ ] No board clipping at default app window dimensions.

## Feature 2: Settings Foundation
### Functional Criteria
- [ ] App loads settings from defaults when no user settings file exists.
- [ ] App validates loaded settings against schema.
- [ ] Invalid settings recover safely to defaults without crash.
- [ ] App saves user settings and reloads same values on restart.
- [ ] Settings include version number and migration path hook.

### UX Criteria
- [ ] Settings UI clearly groups controls by category.
- [ ] Changed settings apply predictably (live or on apply, but consistent).
- [ ] Reset-to-default behavior is available and confirmed.

### Regression Criteria
- [ ] No startup failure when settings file is missing or malformed.
- [ ] No silent data loss for valid saved settings.

## Feature 3: Hover Popup Behavior
### Functional Criteria
- [ ] Popup can be enabled or disabled.
- [ ] Popup supports compact and detailed modes.
- [ ] Hover delay setting is respected.
- [ ] Popup supports configured target types (bet marker, chip, chip stack).

### UX Criteria
- [ ] Popup positioning does not block core interaction.
- [ ] Popup text remains readable against configured theme colors.
- [ ] Popup dismiss behavior is predictable when cursor exits target.

### Regression Criteria
- [ ] No popup flicker loop on rapid cursor movement.
- [ ] No measurable input lag introduced by popup rendering.

## Feature 4: Core Streak Counters
### Functional Criteria
- [ ] Track hit and miss streaks for dozens.
- [ ] Track hit and miss streaks for columns.
- [ ] Track hit and miss streaks for even-money bets.
- [ ] Streak display can be toggled on or off.
- [ ] Win-streak display uses configured dark-blue color.
- [ ] Loss-streak display uses configured bright-red color.

### Data Correctness Criteria
- [ ] Streak increments and resets correctly after each spin.
- [ ] Separate categories do not leak state into each other.
- [ ] Streak state remains correct after repeat spins and settings changes.

### Regression Criteria
- [ ] No mismatch between displayed streak and internal tracked value.
- [ ] No crash when streak display is toggled mid-session.

## Feature 5: Rules and Edge Cases
### Functional Criteria
- [ ] Spin outcomes for `0/00/000` evaluate correctly for all impacted outside bets.
- [ ] French `en prison` handling behaves as configured by rules settings.
- [ ] Auto-clear behavior respects `en prison` preservation rule.

### Regression Criteria
- [ ] No rule-evaluation deadlocks or unresolved spin states.
- [ ] No incorrect payout state after edge-case outcomes.

## Global Beta Release Criteria
- [ ] No blocker severity bugs open.
- [ ] No data corruption bugs open.
- [ ] Smoke test pass from app launch to multiple completed spins.
- [ ] Settings persist correctly across restart.
- [ ] Changelog entry added for V1 beta scope.

## Review Log
- Review date:
- Reviewer:
- Build/version:
- Result:
- Notes:

