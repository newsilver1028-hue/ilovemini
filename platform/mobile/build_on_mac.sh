#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v flutter >/dev/null || { echo 'Flutter를 설치하고 PATH를 설정하세요.'; exit 1; }
if [[ "$(uname -s)" != Darwin ]]; then echo '두 플랫폼 빌드는 Xcode가 설치된 Mac에서 실행하세요.'; exit 1; fi
command -v xcodebuild >/dev/null || { echo 'Xcode를 설치하세요.'; exit 1; }
if [[ ! -d android || ! -d ios ]]; then
  native_temp="$(mktemp -d)"
  trap 'rm -rf "$native_temp"' EXIT
  flutter create --platforms=android,ios --org com.ilovemini --project-name ilovemini "$native_temp/ilovemini"
  [[ -d android ]] || cp -R "$native_temp/ilovemini/android" android
  [[ -d ios ]] || cp -R "$native_temp/ilovemini/ios" ios
fi
python3 configure_native.py
flutter pub get
flutter analyze lib test
flutter test
flutter build apk --release --dart-define=ILOVEMINI_API_URL=https://ilovemini.onrender.com/api
flutter build ios --simulator --debug --dart-define=ILOVEMINI_API_URL=https://ilovemini.onrender.com/api
echo 'Android APK: build/app/outputs/flutter-apk/app-release.apk'
echo 'iOS 시뮬레이터 앱: build/ios/iphonesimulator/Runner.app'
echo '실제 iPhone 설치는 Xcode 서명 설정 후 flutter run으로 진행하세요.'
