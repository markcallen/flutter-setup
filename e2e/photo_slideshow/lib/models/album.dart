class Album {
  const Album({
    required this.id,
    required this.name,
    required this.photoPaths,
    this.transitionDuration = const Duration(seconds: 3),
    this.slideDuration = const Duration(seconds: 5),
  });

  final String id;
  final String name;
  final List<String> photoPaths;
  final Duration transitionDuration;
  final Duration slideDuration;

  int get photoCount => photoPaths.length;

  String? get coverPhotoPath => photoPaths.isEmpty ? null : photoPaths.first;

  Album copyWith({
    String? name,
    List<String>? photoPaths,
    Duration? transitionDuration,
    Duration? slideDuration,
  }) {
    return Album(
      id: id,
      name: name ?? this.name,
      photoPaths: photoPaths ?? this.photoPaths,
      transitionDuration: transitionDuration ?? this.transitionDuration,
      slideDuration: slideDuration ?? this.slideDuration,
    );
  }
}
