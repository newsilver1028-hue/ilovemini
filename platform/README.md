# ILOVEMINI 정식 앱 개발 기반

Flutter + Django REST API + PostgreSQL입니다. 모바일 앱은 시스템 설정에 맞춰 라이트/다크 모드로 전환하고, 지정된 아이러브미니 로고를 사용합니다. 협력업체 상세정보에서 주소, 전화, 지도, 카페 링크와 진행 중인 혜택을 보여줍니다. 로그인한 회원은 차량을 등록하고 차계부 기록과 날짜/주행거리 정비 알림을 관리할 수 있습니다. 차량을 중고로 판매할 때 일회용 인계 코드를 발급해 구매자 계정으로 차량과 기록을 이전할 수 있습니다. Firebase Cloud Messaging을 연결하면 마감일 또는 기록한 주행거리에 도달했을 때 휴대폰 푸시를 보낼 수 있습니다. 회원가입과 로그인을 네이버 OAuth로 통합했습니다. 첫 네이버 인증 후 약관과 개인정보 안내에 동의하면 ILOVEMINI 회원이 자동 생성됩니다. 네이버 비밀번호와 Client Secret은 앱에 저장하지 않습니다.

## 핵심 데이터 구조: Vehicle Passport

차량을 데이터의 기준점으로 둡니다. `Vehicle`은 소유자가 바뀌어도 유지되고, `VehicleOwnership`은 각 소유 기간과 확인 수준을 별도로 쌓습니다. 기존 `Vehicle.owner` 데이터는 마이그레이션에서 최초 소유 이력으로 옮기며, 현재 계정 등록은 법적 소유권 검증과 구분해 `차주 등록`으로 표시합니다. 차량에는 개인정보를 포함하지 않는 무작위 `public_id`와 VIN 원문 대신 사용할 `vin_hash` 자리가 있습니다.

승인된 협력업체 담당자는 차량 QR을 스캔해 정비이력을 바로 등록합니다. 건별 차주 승인은 요구하지 않습니다. 차주의 이력 공개 동의는 업체의 기록 등록 권한과 별도이며, QR 스캔이나 앱 인계 코드만으로 자동차의 법적 소유권을 검증했다고 표시하지 않습니다. 공개 Passport에는 공개에 동의한 차량의 정비 사실만 내보내고 계정·연락처·개인 메모·원본 영수증은 제외합니다.

## 서버 실행

```sh
cd platform
cp api/.env.example .env
```

`.env`에 네이버 로그인 Client ID/Secret과 Callback URL을 넣습니다. 카페 공개글 검색에는 별도로 NAVER Cloud Platform의 NAVER API HUB에서 발급한 검색용 Client ID/Secret이 필요하며, 키는 서버에만 저장합니다.
`LEDGER_INTEGRITY_KEY`에는 별도의 긴 무작위 비밀값을 넣고 서버 비밀 저장소에 영구 보관합니다. 이 키를 잃거나 임의로 교체하면 기존 업체 인증기록의 무결성 검증이 실패하므로 운영 중 변경할 때는 별도 키 버전 이전 절차가 필요합니다.

```sh
docker compose up --build
```

네이버 개발자센터의 Callback URL은 `https://<API 도메인>/api/auth/naver/callback/`으로 등록합니다. 앱 복귀 URI는 `ilovemini://auth`이며 Android/iOS 앱 설정과 일치해야 합니다. 첫 운영자 계정은 API 컨테이너에서 `python manage.py createsuperuser`로 생성합니다.

## 협력업체 목록 초기 동기화

운영자 제공 카페 게시글 기준 23개 업체를 데이터베이스에 추가하거나 기존 표기를 바로잡으려면 API 컨테이너에서 아래 명령을 실행합니다. 업체별 카페 게시글 주소와 이름, 지역, 서비스 분야가 반영되며 전화번호·주소 등 확인되지 않은 정보는 임의로 채우지 않습니다. 재실행해도 중복으로 생성되지 않습니다.

```sh
cd platform
docker compose exec api python manage.py sync_ilovemini_partners
```

동기화된 업체는 앱 공개 목록에 표시되도록 활성화됩니다. 업체 상세의 카페 게시글 링크에서 최신 정보와 문의 방법을 확인할 수 있습니다.

## 앱 공지와 협력업체 관리

운영자는 `https://<API 도메인>/admin/`에 접속해 공지, 협력업체, 혜택을 등록합니다.

- 공지: 제목과 요약을 입력하고 게시 시각·선택 종료 시각을 설정합니다. 앱에 공개하려면 `게시 중`을 켭니다. 종료 시각이 게시 시각보다 이르면 저장되지 않습니다.
- 협력업체: 확인된 업체명, 지역, 서비스 분야, 소개, 주소, 전화번호, 영업시간, 링크를 입력합니다. 서비스 분야는 `정비, 튜닝, 부품`처럼 쉼표로 구분합니다. 공개하려면 `앱 노출`을 켭니다.
- 혜택: 협력업체 편집 화면 아래에서 제목, 설명, 시작·종료 시각, 이용 방법을 입력합니다. 앱 노출을 켜고 날짜 범위를 맞추면 유효 기간에 앱에 표시됩니다.

목록 화면에서는 공지 게시·고정, 업체 노출·제휴 표시·정렬 순서, 혜택 활성화를 빠르게 바꿀 수 있습니다. 전화번호와 주소는 업체가 확인해 준 실제 정보만 등록합니다.

## 중고차 판매 시 차량 기록 인계

판매자와 구매자 모두 아이러브미니 앱 회원이어야 합니다. 판매자는 차계부의 `판매 차량 인계`로 24시간 유효한 10자리 일회용 코드를 만들고, 구매자에게 직접 전달합니다. 구매자가 로그인한 앱에서 코드를 확인하면 차종·연식·주행거리·기록 건수를 미리 볼 수 있고, 승인해야 인계가 완료됩니다. 코드는 새로 만들면 이전 코드가 무효화되고, 판매자는 승인 전에 직접 취소할 수 있으며, 구매자가 승인하면 다시 사용할 수 없습니다.

인계 시 차량, 기존 차계부 기록, 정비 알림이 구매자 계정으로 이동합니다. 완료 뒤 판매자는 해당 차량과 기록에 접근할 수 없습니다. 이 앱 기능은 판매자와 구매자의 계정 동의를 처리하며, 차량의 법적 소유권이나 거래 사실을 별도로 확인하지 않습니다. 따라서 코드를 전달하기 전 차량과 구매자 계정을 서로 확인해야 합니다.

## 예약 접수와 협력업체 권한

운영자는 관리자 화면의 `협력업체 담당자`에서 업체별 담당 계정을 연결하고 아래 권한을 각각 켭니다.

- `인증기록 발행 권한`: 해당 업체의 담당자가 차량 QR을 조회하고 업체 인증 정비이력을 등록할 수 있습니다.
- `예약 관리 권한`: 해당 업체로 들어온 예약만 확인하고 확정·거절·완료 처리할 수 있습니다.

회원은 업체 상세에서 예약 요청을 만들고 MY의 `업체 예약` 목록에서 상태를 확인하거나 접수 대기·확정 예약을 취소할 수 있습니다. 요청은 `접수 대기 → 예약 확정/거절 → 완료`로 저장됩니다. 예약 알림은 Firebase 설정이 켜져 있고 담당자가 알림 기기를 등록한 경우 담당자에게, 상태가 바뀌면 예약 회원에게 전송됩니다. 예약 요청은 업체의 수락 전까지 확정된 예약이 아닙니다. 앱은 직원 개인 캘린더를 자동으로 읽거나 수정하지 않습니다.

`/api/bookings/`는 본인 예약 또는 본인이 권한을 가진 업체 예약만 반환합니다. 고객 연락처는 고객 본인과 지정 업체 담당자만 볼 수 있습니다.

## 협력업체 인증 정비이력

일반 차계부는 `차주 입력`, 승인된 협력업체가 발행한 기록은 `업체 인증`으로 구분됩니다.

1. 운영자가 관리자 화면의 `협력업체 담당자`에서 회원 계정과 업체를 연결하고 `인증기록 발행 권한`을 켭니다. 업체와 담당자 권한은 언제든 비활성화할 수 있습니다.
2. 승인된 업체 담당자가 로그인한 앱에서 차량의 Vehicle Passport QR을 스캔합니다. QR에는 무작위 차량 ID만 들어 있고 차주 개인정보는 포함되지 않습니다. 서버는 업체 권한을 확인하고 차종·세대·연식·주행거리와 요약 이력을 반환합니다.
3. 업체 담당자는 작업내용, 주행거리, 금액, 부품번호와 증빙 링크를 입력해 등록합니다. 서버는 담당자의 활성 업체 권한을 확인한 뒤 업체·담당자·작업시각을 묶은 HMAC 검증값을 생성합니다.
4. 같은 차량·작업일·주행거리·작업내용이 이미 등록되어 있으면 서버가 중복 등록을 거절합니다. 등록 즉시 차계부에 업체 인증이력으로 추가됩니다. 건별 차주 승인은 받지 않습니다. 차주는 이력을 조회하고 오류 정정을 요청할 수 있으며, 정정은 기존 기록을 보존한 별도 연결 기록으로만 추가합니다.
5. 업체 인증기록은 차주나 업체가 덮어쓰거나 삭제할 수 없습니다. 저장 내용이 달라지면 `검증 이상`으로 표시됩니다. 향후 차주 알림과 이의제기 기능을 연결하되, 이는 정비기록 등록 전 승인 절차가 아닙니다.

이 기능의 `업체 인증`은 승인된 업체 계정이 해당 내용을 등록했고 이후 무결성 검사를 통과했다는 의미입니다. 국가기관의 공증이나 차량 전체 이력의 완전성을 의미하지 않습니다. 업체 인증이 한 건이라도 있는 차량은 기록 보존을 위해 앱과 관리자 화면에서 삭제할 수 없습니다. 증빙 파일 자체 업로드는 운영 스토리지 연결 후 추가하며, 현재 MVP는 HTTPS 증빙 링크를 기록합니다.

## 앱 실행

Android 테스트에는 Mac이 필요하지 않습니다. Windows, macOS, Linux 컴퓨터에 Flutter SDK와 Android Studio를 설치하고 Android Emulator를 만들거나 Android 휴대폰의 USB 디버깅을 켜면 됩니다. 이 앱은 Flutter 3.27 이상(Dart 3.6 이상)을 요구합니다. Flutter 플러그인만 설치하는 것으로는 부족하고 Flutter SDK 자체가 필요합니다.

공식 설치 안내: [Flutter SDK 설치](https://docs.flutter.dev/install), [Android 개발 환경 설정](https://docs.flutter.dev/platform-integration/android/setup). Android Studio의 SDK Manager에서 Android SDK, Android SDK Command-line Tools, Android Emulator를 설치하고 Device Manager에서 가상 기기를 생성합니다. 설치 후 터미널에서 아래 명령이 오류 없이 끝나야 합니다.

```sh
flutter doctor
flutter doctor --android-licenses
```

저장소를 컴퓨터에 내려받은 뒤, **Windows PowerShell**에서는 다음 명령으로 Android 실행 폴더를 준비합니다.

```sh
cd .\platform\mobile
flutter create --platforms=android --project-name=ilovemini --org=com.ilovemini "$env:TEMP\ilovemini-native-shell"
Copy-Item -Recurse "$env:TEMP\ilovemini-native-shell\android" "."
flutter pub get
flutter devices
flutter run --dart-define=ILOVEMINI_DEMO=true
```

**macOS/Linux 터미널**에서는 같은 작업을 아래처럼 실행합니다.

```sh
cd platform/mobile
flutter create --platforms=android --project-name=ilovemini --org=com.ilovemini /tmp/ilovemini-native-shell
cp -R /tmp/ilovemini-native-shell/android .
flutter pub get
flutter devices
flutter run --dart-define=ILOVEMINI_DEMO=true
```

Android Studio에서 Device Manager의 ▶ 버튼으로 가상 기기를 먼저 켜면 앱이 실행됩니다. 미리보기에는 예시 공지·업체·혜택과 데모 MINI가 나옵니다. 차계부 기록·정비 알림·차량 추가는 앱이 켜져 있는 동안 시험할 수 있고, 앱을 종료하면 데모 변경 사항은 초기화됩니다. 미리보기 데이터는 서버에 저장되지 않으며 로그인·푸시·실제 회원 간 차량 인계는 API 연동 후 확인합니다.

실제 API를 연결할 때 Android Emulator의 개발 컴퓨터 주소는 `10.0.2.2`입니다. 실제 휴대폰에서는 컴퓨터와 같은 Wi-Fi에 연결하고 컴퓨터의 내부 IP를 사용합니다. 운영 API는 HTTPS여야 합니다. 앱 실행 전 Flutter SDK와 Android SDK가 준비됐는지 `flutter doctor`와 `flutter devices`로 확인할 수 있습니다.

네이버 로그인과 iOS 실행을 붙이는 설정은 Android 미리보기 다음 단계입니다. 로그인에는 `ilovemini://auth` 딥링크를 Android Manifest와 iOS URL Types에 등록하고 네이버 개발자센터에 플랫폼 정보를 입력해야 합니다. 협력업체 QR 스캔을 iOS에서 실행할 때는 `ios/Runner/Info.plist`에 `NSCameraUsageDescription`을 추가해 카메라가 차량 QR 스캔에 쓰인다고 안내해야 합니다. iOS 앱을 빌드하거나 테스트하려면 Mac과 Xcode가 필요합니다.

## 푸시 알림 설정

1. 위의 네이티브 실행 폴더 생성 명령을 먼저 완료한 뒤 Firebase Console에서 프로젝트를 만들고 Android 및 iOS 앱을 등록합니다. Firebase CLI가 없다면 `npm install -g firebase-tools`로 설치합니다. `platform/mobile`에서 `firebase login`, `dart pub global activate flutterfire_cli`, `flutterfire configure`를 차례로 실행합니다. 이 마지막 명령이 `lib/firebase_options.dart`의 임시 파일을 실제 앱 설정으로 교체합니다. iOS 최소 버전을 15로 설정하고, Xcode에서 Push Notifications와 Background Modes(Remote notifications)를 켠 뒤 APNs 인증 키를 Firebase에 등록해야 합니다.
2. 서버용 Firebase Admin 서비스 계정 JSON을 만들고 안전한 서버 비밀 저장소에 둡니다. JSON 파일을 저장소에 추가하거나 앱에 넣지 않습니다.
3. 로컬에서는 `FIREBASE_ADMIN_KEY_FILE=/절대경로/firebase-admin.json`을 `platform/.env`에 지정하고 다음처럼 Firebase Compose override를 함께 사용합니다.

```sh
cd platform
docker compose -f docker-compose.yml -f docker-compose.firebase.example.yml up --build
```

회원은 내 정보 화면의 `정비 푸시 알림` 스위치로 수신을 직접 켜고 끌 수 있습니다. 허용한 기기의 Firebase Installation ID(FID)는 `/api/push/devices/`에 등록됩니다. 서버는 FCM 권장 방식인 FID를 사용해 기기를 지정합니다. 스케줄러는 한 시간마다 오늘까지 날짜가 도래한 알림과 차량 주행거리 알림을 확인합니다. 주행거리 판정은 차계부에 입력된 주행거리를 기준으로 합니다. 수동 점검은 API 컨테이너에서 `python manage.py send_due_reminders`로 실행할 수 있습니다.

## OAuth 흐름 및 API

1. 앱이 `/api/auth/naver/start/`에서 로그인 URL을 받습니다.
2. 네이버 인증 뒤 `/api/auth/naver/callback/`에서 서버가 code를 교환하고 고유 사용자 ID를 확인합니다.
3. 서버가 3분 만료 일회용 ticket을 `ilovemini://auth`로 전달합니다.
4. 앱은 필수 약관·개인정보 동의와 ticket을 `/api/auth/naver/complete/`로 보내고 자체 JWT를 받습니다.

- `/api/vehicles/`, `/api/ledger/`, `/api/reminders/`: 로그인 회원의 본인 데이터만 조회/수정
- `/api/vehicles/{id}/maintenance-summary/`: 최근 정비, 협력업체 인증기록 수, 정정 수, 예정·경과 정비 알림 요약
- `/api/vehicles/{id}/transfer-code/`, `/api/vehicles/{id}/cancel-transfer/`, `/api/vehicles/preview-transfer/`, `/api/vehicles/accept-transfer/`: 로그인 회원 간 차량·기록 인계
- `/api/partners/my-workplaces/`, `/api/vehicles/scan-passport/`, `/api/ledger/partner-verified/`: 승인된 협력업체 계정의 QR 이력 조회와 인증기록 등록
- `/api/bookings/`, `/api/bookings/{id}/cancel/`, `/api/bookings/{id}/respond/`: 예약 요청, 취소와 업체별 접수 처리
- `/api/notices/`, `/api/partners/`, `/api/offers/`: 게시/활성 상태 공개 조회, 운영자 관리
- `/api/cafe/search/?q=검색어`: NAVER API HUB 공개 카페글 검색. Naver 로그인 키와는 별도인 NAVER API HUB 키가 필요합니다.
- 관리자: `/admin/`

## 검증

```sh
cd platform/api
DATABASE_ENGINE=sqlite python manage.py test
python manage.py check
```

테스트는 OAuth 신규 가입과 필수 동의, 일회용 ticket, 회원별 데이터 분리, 공개 자료 노출, 푸시 기기 등록 권한, 주행거리 갱신, 업체 인증·정정기록 권한과 무결성을 확인합니다. 현재 앱스토어 제출용 운영 빌드는 아닙니다. 출시 전 실제 약관/개인정보 문서와 링크, 계정 삭제, Apple 로그인 심사 요건, 운영 서버 보안·백업·모니터링을 마쳐야 합니다.

## 2026-09-26 기능 검토 후 반영

- Flutter 업체 탭: 스크롤, 새로고침, 업체명·지역·분야 검색, 분야/수도권 필터, 실제 목록 개수 표시.
- 공지 및 혜택 카드: 상세 본문, 카페 원문 연결, 혜택의 업체 문의 화면 연결.
- Flutter API: 페이지네이션 전체 조회, 외부 주소/순환 페이지 거절, 동시 요청의 토큰 갱신 통합, 갱신 거절 시 재로그인 안내. 일시적인 서버/통신 장애는 저장된 로그인 정보를 삭제하지 않음.
- Gunfactory 데모 혜택: 제공된 3개 패키지 안내 및 방문 전 가격 확인 문구 반영.
- Django: 토큰 갱신 경로 추가, 인계 취소의 update 반환값 처리 오류 수정.
- 인계 후 기존 기록은 수정·삭제할 수 없으며 원본을 보존. 현재 소유기간 이전 기록의 자유서술·부품 자유입력·증빙 링크·비용은 일반 새 차주 응답에서 숨김. 날짜·주행거리·분류·업체·출처 검증은 유지. 이전 차주의 개인 알림과 차량 별명은 승계하지 않고 공개 설정도 해제.

### 검증과 한계

- SQLite 테스트 DB에서 `DATABASE_ENGINE=sqlite python manage.py test core`: **28개 성공**. 인계 후 목록/단건/요약 응답의 개인정보 제한, 변경 방지, 알림 격리, 새 차주 기록 생성, JWT 갱신을 포함.
- 테스트 간 요청 제한 캐시를 초기화해 독립 실행과 전체 실행 결과를 일치시킴. 실제 서비스 요청 제한은 유지.
- `mobile/test/catalog_api_test.dart`에 페이지네이션, 외부 주소 차단, 동시 갱신, 갱신 실패, 23개 업체 스크롤/검색, 공지 상세 화면 회귀 테스트 추가. **실행 미완료**: 이 작업 환경에서 Flutter 부트스트랩 실행이 자동 보안 검토에 의해 클라우드 메타데이터 주소 접근 위험으로 차단됨. 실행 가능한 개발 환경에서 `flutter pub get`, `flutter analyze`, `flutter test` 검증 필요.
- 실기기 iOS/Android, 네이버 실제 로그인, Firebase 실발송, PostgreSQL 동시 인계는 이번 검증에 포함하지 않음.
- 현재 이력의 정비 상세는 자유입력이라 개인정보와 작업 사실을 자동 구분할 수 없어 인계 후 보수적으로 숨김. 상세 작업까지 안전하게 승계하려면 표준 정비항목과 공개용 검토 필드를 별도 도입해야 함. 증빙 원본 URL 자체의 저장소 접근 통제도 운영 배포 전 필요.
- 이번 변경은 Flutter/Django 개발 소스에 적용. 정적 HTML 미리보기는 실제 서버/앱 배포를 대신하지 않으며 운영 API 배포와 앱 빌드·배포는 별도.
