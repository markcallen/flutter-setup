# Shopping List App

A Flutter app for managing household shopping lists. Users can create multiple lists,
add items with quantities and categories, check off items while shopping, and share
lists with family members.

## Project Goal

Replace the household's shared notes app with a dedicated shopping experience that
works offline, syncs across devices, and remembers frequently bought items.

## Key Features

- Create and name multiple lists (Groceries, Hardware, Pharmacy)
- Add items with quantity, unit, and aisle/category
- Check off items while walking the store; checked items move to the bottom
- Archive completed lists for reference
- Share a list with other household members via a join code
- Suggest previously bought items when typing

## Screens

### List Overview
Shows all active lists as cards with item count and last-updated time.
Tap a card to open the list. Long-press to rename or delete.

### Shopping List
Scrollable list of items grouped by category (Produce, Dairy, Meat, etc.).
Each row shows item name, quantity, and a checkbox. A floating action button
opens the Add Item sheet.

### Add / Edit Item Sheet
Bottom sheet with fields: name (autocomplete from history), quantity (numeric),
unit (dropdown: each, kg, g, L, mL, pack), category (dropdown).

### Shared List View
Read-only view of a list shared from another household member's device.
Shows who last edited each item and when.

## Data Model

```
ShoppingList
  id: String
  name: String
  ownerId: String
  memberIds: List<String>
  createdAt: DateTime
  updatedAt: DateTime

ShoppingItem
  id: String
  listId: String
  name: String
  quantity: double
  unit: String        // each | kg | g | L | mL | pack
  category: String    // Produce | Dairy | Meat | Bakery | Frozen | Other
  checked: bool
  addedBy: String
  updatedAt: DateTime
```

## Architecture

Clean architecture with three layers:

- **Presentation** – Flutter widgets and BLoC state management
- **Domain** – Use cases: `CreateList`, `AddItem`, `CheckItem`, `ShareList`
- **Data** – Local SQLite via Drift, remote sync via Firestore

Offline-first: all writes go to SQLite immediately; a background sync worker
pushes deltas to Firestore when online.

## Tech Stack

| Concern | Choice |
|---|---|
| State management | flutter_bloc |
| Local storage | Drift (SQLite) |
| Remote sync | Firestore |
| Auth | Firebase Auth (Google + Apple sign-in) |
| Testing | mocktail |
| Navigation | go_router |

## Getting Started

This directory contains design documentation only. To scaffold the Flutter
project run:

```bash
flutter-setup create shopping_list ios android \
  --org com.example \
  --architecture clean \
  --database sqlite \
  --testing mocktail \
  --auth-provider firebase \
  --cloud-database firestore
```

## Open Questions

- Should checked items disappear immediately or linger until the list is archived?
- Maximum list members: unlimited or capped (e.g. 10)?
- Offline conflict resolution: last-write-wins or show conflict UI?
