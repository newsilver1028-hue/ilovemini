# Render에 API 배포하기

이 문서는 Flutter 앱이 실제 회원 계정, 차량 이력, 예약, 카페 공개 검색을 쓰도록 Django API를 Render에 올리는 절차입니다. 이 저장소 변경만으로 Render 계정의 서비스가 자동 수정되거나 배포되지는 않습니다.

## Render Web Service 설정

1. GitHub 저장소에서 `New` → `Web Service`를 선택합니다.
2. Root Directory를 `platform/api`로 지정하고 Runtime은 `Docker`로 둡니다. Render가 이 경로의 `Dockerfile`을 빌드합니다.
3. PostgreSQL을 만들거나 기존 데이터베이스를 연결합니다. 같은 Render 리전에 있는 DB의 Internal Database URL을 복사합니다.
4. Web Service의 Environment에 아래 값을 등록합니다. `DATABASE_URL`, Client Secret, Firebase 서비스 계정 값은 Secret 입력란에 넣습니다.

| Key | Value |
|---|---|
| `DJANGO_SECRET_KEY` | 길고 무작위인 새 비밀값 |
| `LEDGER_INTEGRITY_KEY` | DJANGO 키와 별도로 만든 비밀값. 정비 인증기록이 생긴 뒤에는 바꾸지 마세요. |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_ALLOWED_HOSTS` | Render 서비스 주소의 호스트만 입력. 예: `ilovemini-api.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | 브라우저에서 API를 부를 시제품 사이트의 전체 주소. 예: `https://ilovemini-app-preview.newsilver1028.chatgpt.site` |
| `DATABASE_URL` | 연결할 PostgreSQL의 Internal Database URL |
| `NAVER_CLIENT_ID` | 네이버 로그인 애플리케이션 Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 로그인 Client Secret |
| `NAVER_REDIRECT_URI` | `https://<API 호스트>/api/auth/naver/callback/` |
| `MOBILE_AUTH_REDIRECT_URI` | `ilovemini://auth` |
| `NAVER_API_HUB_CLIENT_ID` | 카페글 검색용 NAVER API HUB Client ID |
| `NAVER_API_HUB_CLIENT_SECRET` | 카페글 검색용 NAVER API HUB Client Secret |
| `OPENAI_API_KEY` | MINI 박사 Q&A의 질문별 웹 검색·AI 답변용 비밀키. Render 환경변수에만 저장하고 사이트/앱에는 넣지 않습니다. |
| `OPENAI_SEARCH_MODEL` | Responses API 웹 검색 지원 모델. 기본값은 `gpt-5.5`입니다. |
| `FCM_ENABLED` | Firebase 푸시를 연결하기 전에는 `0` |

`DATABASE_URL`의 암호를 포함한 전체 주소를 Key와 Value 두 칸에 나누지 말고, Key=`DATABASE_URL`, Value=전체 URL 한 줄로 저장합니다. 저장 후 Deploy를 실행합니다. 컨테이너 시작 시 DB migration과 정적 파일 수집을 실행하고 Gunicorn으로 서버를 띄웁니다. Health Check Path는 `/api/health/`로 지정합니다.

## 네이버 연결

- 네이버 로그인 앱 Callback URL에는 위 `NAVER_REDIRECT_URI`의 전체 주소를 등록합니다. 서비스 URL이 바뀌면 둘 다 맞춰야 합니다.
- `NAVER_API_HUB_CLIENT_ID/SECRET`은 로그인용 키가 아닙니다. NCP 콘솔에서 NAVER API HUB 키를 만들고 Search의 Cafe Article API를 켭니다.
- 검색 API는 공개 검색 결과만 반환합니다. 비공개 회원 전용 글까지 가져오거나 API 결과를 쌓아 AI 학습 데이터로 만드는 기능은 포함하지 않았습니다. 네이버 API 이용 조건에서 검색 결과의 별도 저장·재가공이 제한되어 있으므로, AI Q&A는 카페 운영자가 별도로 제공·사용 허락한 원문 자료를 확보한 뒤 붙입니다.

## 앱을 실제 API에 연결하기

개발 컴퓨터의 에뮬레이터 주소 `10.0.2.2`는 출시 앱에서 쓸 주소가 아닙니다. Flutter 앱 빌드할 때 Render API 주소를 전달합니다.

```sh
cd platform/mobile
flutter build appbundle --release --dart-define=ILOVEMINI_API_URL=https://<API 호스트>/api
```

Android 설치 파일이 필요한 경우 `appbundle` 대신 `apk`를 사용합니다. API 주소는 `https://`로 시작해야 합니다. 앱이 새 API를 호출하는지 실제 로그인, 내 차량 등록, 업체 예약 요청, 업체 권한 계정의 예약 확정, 차량 QR 정비이력 등록으로 각각 확인합니다.

## 업체별 계정 권한

운영자 계정으로 `https://<API 호스트>/admin/`에 들어가 업체와 회원을 먼저 등록합니다. `협력업체 담당자`에서 회원과 업체를 연결한 다음 예약을 받을 업체에는 `예약 관리 권한`, 차량 정비를 기록할 업체에는 `인증기록 발행 권한`을 켭니다. 실제 직원 계정에 권한을 연결하고 푸시를 시험하기 전에는 해당 업체가 예약을 처리할 수 없습니다.

## 운영 전에 결정할 항목

- 회원에게 고지할 정식 이용약관·개인정보 처리방침, 운영자 연락처, 데이터 보유 기간과 삭제 요청 방법
- Render PostgreSQL 백업·복구 계획과 운영 알림
- iOS/Android Firebase·Apple/Google 스토어 설정과 실기기 푸시 검증
- 업체 예약 접수 담당 계정·전화번호 정확성, 취소·노쇼 안내 정책
- 실제 네이버 API HUB 키의 Search/Cafe Article 권한과 운영 쿼터
