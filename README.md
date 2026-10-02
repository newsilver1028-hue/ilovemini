# ILOVEMINI 앱

Flutter 앱과 Django REST API를 연결한 ILOVEMINI 앱 MVP입니다. 네이버 로그인, MINI 차계부·정비 알림, 공지·제휴 콘텐츠, 차량과 기록의 회원 간 인계 흐름을 포함합니다.

설계·실행·운영자 콘텐츠 등록 방법: [platform/README.md](platform/README.md)

API 테스트는 `platform/api`에서 `python manage.py test`로 실행합니다. Flutter 기기 빌드와 서버 API 테스트는 개발 환경에 Flutter SDK, Android SDK, Django 의존성을 설치한 뒤 검증해야 합니다. 앱스토어 제출 전에는 네이버 개발자 앱 설정, iOS/Android 딥링크, 실제 약관·개인정보 안내, Apple 로그인 심사 요건과 운영 배포 검증이 필요합니다.
