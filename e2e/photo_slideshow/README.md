# Photo Slideshow

Group photos from your device into named albums and play them back as a
full-screen slideshow with crossfade transitions.

## Status

Partially implemented. Core models and screens are in place; photo library
integration and persistence are still stubs.

## What's done

- `Album` model with name, photo paths, and playback timing
- Album list screen — create, view, and delete albums
- Slideshow screen — play/pause, skip, fade transitions
- `PhotoGrid` widget — selectable grid (pending real photo_manager wiring)
- Unit tests for the `Album` model

## What's missing

- **Photo picker**: `PhotoGrid` uses placeholder `Image.asset` calls;
  needs `photo_manager` permission flow and real asset loading
- **Persistence**: albums are held in a top-level list; needs SQLite or
  shared_preferences to survive restarts
- **CI/CD**: no workflows yet
- **Makefile**: no build automation
- **VS Code config**: no launch.json or settings.json

Run flutter-setup append to add the missing tooling:

```bash
flutter-setup append --dir .
```

## Running locally

```bash
flutter pub get
flutter run
```

## Project structure

```
lib/
  main.dart                  # App entry point
  models/
    album.dart               # Album data class
  screens/
    album_list_screen.dart   # Home screen — list of slideshows
    slideshow_screen.dart    # Full-screen playback with controls
  widgets/
    photo_grid.dart          # Reusable selectable photo grid
test/
  album_test.dart            # Unit tests for Album model
```
