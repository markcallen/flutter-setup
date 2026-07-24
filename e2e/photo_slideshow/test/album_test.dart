import 'package:flutter_test/flutter_test.dart';
import 'package:photo_slideshow/models/album.dart';

void main() {
  group('Album', () {
    const baseAlbum = Album(
      id: '1',
      name: 'Vacation',
      photoPaths: ['a.jpg', 'b.jpg', 'c.jpg'],
    );

    test('photoCount returns length of photoPaths', () {
      expect(baseAlbum.photoCount, 3);
    });

    test('coverPhotoPath returns first photo', () {
      expect(baseAlbum.coverPhotoPath, 'a.jpg');
    });

    test('coverPhotoPath is null when album is empty', () {
      const empty = Album(id: '2', name: 'Empty', photoPaths: []);
      expect(empty.coverPhotoPath, isNull);
    });

    test('copyWith replaces only specified fields', () {
      final updated = baseAlbum.copyWith(name: 'Summer 2024');
      expect(updated.name, 'Summer 2024');
      expect(updated.photoPaths, baseAlbum.photoPaths);
      expect(updated.id, baseAlbum.id);
    });

    test('default slide duration is 5 seconds', () {
      expect(baseAlbum.slideDuration, const Duration(seconds: 5));
    });

    test('default transition duration is 3 seconds', () {
      expect(baseAlbum.transitionDuration, const Duration(seconds: 3));
    });
  });
}
