import 'dart:async';
import 'package:flutter/material.dart';
import '../models/album.dart';

class SlideshowScreen extends StatefulWidget {
  const SlideshowScreen({super.key, required this.album});

  final Album album;

  @override
  State<SlideshowScreen> createState() => _SlideshowScreenState();
}

class _SlideshowScreenState extends State<SlideshowScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _fadeController;
  late final Animation<double> _fadeAnimation;

  int _currentIndex = 0;
  Timer? _slideTimer;
  bool _isPlaying = false;
  bool _showControls = true;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: widget.album.transitionDuration,
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _slideTimer?.cancel();
    _fadeController.dispose();
    super.dispose();
  }

  void _play() {
    setState(() => _isPlaying = true);
    _scheduleNext();
  }

  void _pause() {
    _slideTimer?.cancel();
    setState(() => _isPlaying = false);
  }

  void _scheduleNext() {
    _slideTimer?.cancel();
    _slideTimer = Timer(widget.album.slideDuration, _advanceSlide);
  }

  void _advanceSlide() {
    if (!mounted) return;
    _fadeController.forward(from: 0).then((_) {
      if (!mounted) return;
      setState(() {
        _currentIndex = (_currentIndex + 1) % widget.album.photoPaths.length;
      });
      _fadeController.reverse();
      if (_isPlaying) _scheduleNext();
    });
  }

  void _toggleControls() {
    setState(() => _showControls = !_showControls);
  }

  @override
  Widget build(BuildContext context) {
    final photos = widget.album.photoPaths;

    if (photos.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.album.name)),
        body: const Center(
          child: Text('No photos in this slideshow yet.\nAdd photos to get started.'),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: _toggleControls,
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Photo
            FadeTransition(
              opacity: _fadeAnimation,
              child: Image.asset(
                photos[_currentIndex],
                fit: BoxFit.contain,
              ),
            ),

            // Controls overlay
            if (_showControls) ...[
              // Top bar
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: AppBar(
                  backgroundColor: Colors.black54,
                  title: Text(
                    widget.album.name,
                    style: const TextStyle(color: Colors.white),
                  ),
                  iconTheme: const IconThemeData(color: Colors.white),
                ),
              ),

              // Bottom controls
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  color: Colors.black54,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Photo counter
                      Text(
                        '${_currentIndex + 1} / ${photos.length}',
                        style: const TextStyle(color: Colors.white70),
                      ),
                      const SizedBox(height: 8),

                      // Playback controls
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.skip_previous, color: Colors.white),
                            onPressed: () {
                              setState(() {
                                _currentIndex =
                                    (_currentIndex - 1 + photos.length) % photos.length;
                              });
                            },
                          ),
                          const SizedBox(width: 16),
                          IconButton(
                            iconSize: 48,
                            icon: Icon(
                              _isPlaying ? Icons.pause_circle : Icons.play_circle,
                              color: Colors.white,
                            ),
                            onPressed: _isPlaying ? _pause : _play,
                          ),
                          const SizedBox(width: 16),
                          IconButton(
                            icon: const Icon(Icons.skip_next, color: Colors.white),
                            onPressed: () {
                              setState(() {
                                _currentIndex = (_currentIndex + 1) % photos.length;
                              });
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
