# Product Requirements — Shopping List App

## Problem Statement

Household members use a shared notes app to manage shopping lists. The current
solution has no structure (items mix with notes), no offline support, and no
way to collaborate in real time while one person is in the store.

## Goals

1. Make adding and checking off items frictionless — fewer taps than the notes app.
2. Work fully offline; sync automatically when connectivity returns.
3. Support households of up to 10 members sharing the same list.

## Non-Goals

- Price comparison or store integration (v2)
- Barcode scanning (v2)
- Recipe import (v2)

## User Stories

### MVP (v1.0)

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| US-01 | As a shopper, I can create a named list | List appears on the overview screen; name is editable |
| US-02 | As a shopper, I can add an item with name, quantity, and unit | Item appears in the list immediately, even offline |
| US-03 | As a shopper, I can check off an item while in the store | Item moves to a "done" section; tap again to uncheck |
| US-04 | As a shopper, I can delete an item | Item is removed; action is undoable within 5 seconds |
| US-05 | As a shopper, I can share a list with a household member | Member receives a join code; on joining, both see the same list |
| US-06 | As a shopper, changes sync automatically when I come back online | No manual refresh required; conflicts resolve silently |

### Post-MVP (v1.1)

| ID | Story |
|----|-------|
| US-07 | Autocomplete item names from purchase history |
| US-08 | Group items by aisle/category automatically |
| US-09 | Archive completed lists and browse history |

## Acceptance Criteria — Core Flow

1. App launches in under 2 seconds on a mid-range Android device.
2. Adding an item takes 3 taps or fewer from the list view.
3. Checked items persist across app restarts.
4. Offline writes are queued and sync within 10 seconds of reconnection.
5. Two members checking different items simultaneously converges without data loss.

## UX Constraints

- Minimum tap target: 48 × 48 dp (Material guidelines).
- Font size: minimum 16 sp for item names; respect system font scale.
- Dark mode: supported from day one.
- Accessibility: all interactive elements labelled for screen readers.

## Technical Constraints

- iOS 16+ and Android 8+ (API 26+).
- App size budget: under 20 MB download.
- No background location access required.
- Firebase project must be separate from any existing company project.

## Success Metrics

- 80% of household members use the app instead of the notes app within 4 weeks.
- Average time to add an item under 8 seconds (measured by usability test).
- Zero data-loss incidents in the first 3 months.

## Milestones

| Milestone | Scope | Target |
|-----------|-------|--------|
| M1 — Scaffold | flutter-setup create, CI/CD green | Week 1 |
| M2 — Local lists | US-01 through US-04, Drift schema | Week 3 |
| M3 — Sharing | US-05, US-06, Firebase integration | Week 6 |
| M4 — Polish | Animations, accessibility audit, TestFlight beta | Week 8 |
