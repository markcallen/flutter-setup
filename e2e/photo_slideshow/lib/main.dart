import 'package:flutter/material.dart';
import 'screens/album_list_screen.dart';

void main() {
  runApp(const PhotoSlideshowApp());
}

class PhotoSlideshowApp extends StatelessWidget {
  const PhotoSlideshowApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Photo Slideshow',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      darkTheme: ThemeData.dark(useMaterial3: true),
      themeMode: ThemeMode.system,
      home: const AlbumListScreen(),
    );
  }
}
