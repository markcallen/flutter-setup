import 'package:flutter/material.dart';

// TODO: wire up photo_manager to load real device photos
class PhotoGrid extends StatelessWidget {
  const PhotoGrid({
    super.key,
    required this.photoPaths,
    this.selectedPaths = const {},
    this.onPhotoTap,
    this.selectable = false,
  });

  final List<String> photoPaths;
  final Set<String> selectedPaths;
  final ValueChanged<String>? onPhotoTap;
  final bool selectable;

  @override
  Widget build(BuildContext context) {
    if (photoPaths.isEmpty) {
      return const Center(child: Text('No photos'));
    }

    return GridView.builder(
      padding: const EdgeInsets.all(4),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 4,
        crossAxisSpacing: 4,
      ),
      itemCount: photoPaths.length,
      itemBuilder: (context, index) {
        final path = photoPaths[index];
        final isSelected = selectedPaths.contains(path);

        return GestureDetector(
          onTap: () => onPhotoTap?.call(path),
          child: Stack(
            fit: StackFit.expand,
            children: [
              Image.asset(path, fit: BoxFit.cover),
              if (selectable)
                Positioned(
                  top: 4,
                  right: 4,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 150),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isSelected
                          ? Theme.of(context).colorScheme.primary
                          : Colors.black38,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                    width: 24,
                    height: 24,
                    child: isSelected
                        ? const Icon(Icons.check, size: 16, color: Colors.white)
                        : null,
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}
