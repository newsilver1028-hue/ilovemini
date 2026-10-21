# 계정 삭제 배포 설정

앱 빌드 346의 삭제 흐름은 `GET /api/me/account/`로 확인한 뒤 같은 주소로 DELETE 요청을 보냅니다.
배포 때 `python manage.py migrate --noinput`을 먼저 실행합니다.

## Apple 연결 해제

Render 웹서비스 환경변수에 다음을 설정합니다. 키 내용은 Git이나 모바일 앱에 넣지 않습니다.

- `APPLE_CLIENT_ID`: `com.ilovemini.ilovemini` (네이티브 앱 Bundle ID)
- `APPLE_TEAM_ID`: Apple Developer 팀 ID
- `APPLE_KEY_ID`: Sign in with Apple 권한으로 발급한 키 ID
- `APPLE_PRIVATE_KEY`: 해당 키의 p8 PEM 내용 (실제 줄바꿈 또는 `\n` 지원)

App Store Connect 업로드 키와 Sign in with Apple용 키는 권한이 다를 수 있으므로 혼용하지 않습니다.
앱 삭제 시 Apple 본인 확인 → 일회성 authorization code 교환 → 교환 토큰의 회원 식별값 확인 →
Apple 토큰 철회 순서로 실행합니다. 연결 해제 실패 시 로컬 계정을 삭제 완료로 처리하지 않습니다.
서버는 Apple 인증 코드·access/refresh token을 DB나 로그에 남기지 않습니다.

## 보관기간 만료 자료 자동 파기

Render Cron Job을 웹서비스와 같은 리전/저장소/브랜치로 설정합니다.

- Root directory: `platform/api`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Command: `python manage.py purge_expired_member_history`
- Schedule: `0 18 * * *` (UTC, 매일 한국시간 오전 3시)
- 환경변수: 웹서비스와 같은 `DATABASE_URL`, `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS=ilovemini.onrender.com`

별도 Cron Job 서비스는 추가 비용이 있으므로 실제 생성·활성화 전 확인합니다.
이 문서와 관리 명령만 배포해도 자동 일정이 등록되는 것은 아닙니다.
현재 이용자가 있는 차량은 파기 대상에서 제외하며 수동 확인 메시지를 남깁니다.

## 검증

1. 네이버/심사 계정은 확인창 후 삭제되어야 합니다.
2. Apple 계정은 가입에 사용한 Apple 계정으로 재인증해야 합니다.
3. 다른 Apple 계정/취소/연결 해제 실패 때 회원·차량 자료가 그대로 남아야 합니다.
4. 인증 기록의 첨부 이미지와 외부 영수증 URL/자유입력 내용이 제거되고 기록 검증이 유지되어야 합니다.
5. 보관기간이 지난 익명 차량의 자료만 정기 작업으로 파기되어야 합니다.
