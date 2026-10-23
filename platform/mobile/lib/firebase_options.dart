import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Firebase app options for the registered ILOVEMINI Android and iOS apps.
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) throw UnsupportedError('ILOVEMINI Firebase is configured for Android and iOS.');
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      default:
        throw UnsupportedError('ILOVEMINI Firebase is configured for Android and iOS.');
    }
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyCtDHH5pMARfo055M7yFAJuB0PEVTgC11Y',
    appId: '1:622867711681:android:01635cb055d79a3ebcf640',
    messagingSenderId: '622867711681',
    projectId: 'ilovemini',
    storageBucket: 'ilovemini.firebasestorage.app',
  );
  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyAw3UPPSFGF5qPP5ydffCWk2hn8KthsQIY',
    appId: '1:622867711681:ios:5924b2a707aa6dd5bcf640',
    messagingSenderId: '622867711681',
    projectId: 'ilovemini',
    storageBucket: 'ilovemini.firebasestorage.app',
    iosBundleId: 'com.ilovemini.ilovemini',
  );
}
