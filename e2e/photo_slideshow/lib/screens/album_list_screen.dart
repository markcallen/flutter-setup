import 'package:flutter/material.dart';
import '../models/album.dart';
import 'slideshow_screen.dart';

// TODO: replace in-memory list with persistent storage
final List<Album> _albums = [];

class AlbumListScreen extends StatefulWidget {
  const AlbumListScreen({super.key});

  @override
  State<AlbumListScreen> createState() => _AlbumListScreenState();
}

class _AlbumListScreenState extends State<AlbumListScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Slideshows'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _showCreateAlbumDialog,
            tooltip: 'New slideshow',
          ),
        ],
      ),
      body: _albums.isEmpty ? _buildEmptyState() : _buildAlbumGrid(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.photo_library_outlined, size: 72, color: Colors.grey),
          const SizedBox(height: 16),
          Text(
            'No slideshows yet',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          const Text('Tap + to create your first slideshow'),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _showCreateAlbumDialog,
            icon: const Icon(Icons.add),
            label: const Text('Create slideshow'),
          ),
        ],
      ),
    );
  }

  Widget _buildAlbumGrid() {
    return GridView.builder(
      padding: const EdgeInsets.all(12),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.85,
      ),
      itemCount: _albums.length,
      itemBuilder: (context, index) => _AlbumCard(
        album: _albums[index],
        onTap: () => _openSlideshow(_albums[index]),
        onDelete: () => setState(() => _albums.removeAt(index)),
      ),
    );
  }

  void _showCreateAlbumDialog() {
    final controller = TextEditingController();
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('New slideshow'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Album name'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              final name = controller.text.trim();
              if (name.isNotEmpty) {
                setState(() {
                  _albums.add(Album(
                    id: DateTime.now().millisecondsSinceEpoch.toString(),
                    name: name,
                    photoPaths: [],
                  ));
                });
                Navigator.pop(ctx);
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  void _openSlideshow(Album album) {
    // TODO: navigate to photo picker first if album is empty
    Navigator.push(
      context,
      MaterialPageRoute<void>(
        builder: (_) => SlideshowScreen(album: album),
      ),
    );
  }
}

class _AlbumCard extends StatelessWidget {
  const _AlbumCard({
    required this.album,
    required this.onTap,
    required this.onDelete,
  });

  final Album album;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        onLongPress: () => _confirmDelete(context),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: album.coverPhotoPath != null
                  ? Image.asset(album.coverPhotoPath!, fit: BoxFit.cover)
                  : Container(
                      color: Colors.grey[300],
                      child: const Icon(Icons.photo, size: 48, color: Colors.grey),
                    ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    album.name,
                    style: Theme.of(context).textTheme.titleSmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    '${album.photoCount} photo${album.photoCount == 1 ? '' : 's'}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmDelete(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete slideshow?'),
        content: Text('This will remove "${album.name}" and all its photos.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            onPressed: () {
              Navigator.pop(ctx);
              onDelete();
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}
