# ILOVEMINI 앱 소스 (GitHub 업로드용)

이 폴더에는 ILOVEMINI Flutter 앱, Django REST API, PostgreSQL 개발용 Docker Compose 설정이 들어 있습니다.

## GitHub에 올리는 방법

1. GitHub에서 **New repository**를 눌러 비공개 저장소를 만듭니다.
2. 이 ZIP 파일을 컴퓨터에서 압축 해제합니다.
3. 저장소 화면의 **Add file → Upload files**를 눌러 압축 해제한 폴더 안의 파일과 폴더를 업로드합니다. ZIP 파일 자체를 올리는 것이 아닙니다.
4. 업로드 전에 `.env`, 네이버 Client Secret, Firebase 서비스 계정 키 파일을 추가하지 않았는지 확인합니다.

## 폴더 안내

- `api/`: Django API 서버
- `mobile/`: Flutter Android/iOS 앱 소스
- `docker-compose.yml`: 로컬 개발용 API + PostgreSQL 실행 설정
- `README.md`: 설치, 실행, 앱 기능 및 API 안내

## 지금 상태와 다음 단계

이 코드는 개발 중인 MVP입니다. GitHub 업로드만으로 앱이 공개되지는 않습니다. Render 같은 호스팅 서비스에서 API 서버와 PostgreSQL을 별도로 배포하고, 네이버 로그인 키 및 공개 Callback URL을 설정해야 합니다. 모바일 앱은 Android/iOS 빌드와 스토어 심사도 별도로 필요합니다.

운영 배포 전에는 개발자가 서버의 운영용 실행 설정, 보안 환경변수, 데이터베이스 연결, HTTPS, 백업을 점검해야 합니다. `.env.example`은 설정 항목 예시이며 실제 비밀값을 포함하지 않습니다.
