ILOVEMINI iOS·Android 카페 화면 패치

포함 기능
- 검색 입력칸 한 줄 + 네이버 AI 검색 / 아이러브미니 카페 검색 버튼
- 아래 별도 영역에서 네이버 카페 API 최신 공개글 최대 10개 표시
- 최신글 API: GET /api/cafe/latest/

적용 방법
1. ZIP을 풀고, 안의 mobile/ 및 api/ 폴더를 GitHub 저장소 루트에 업로드합니다.
   저장소 루트에 이미 mobile/ 및 api/ 폴더가 있다면 해당 파일만 같은 경로에 덮어씁니다.
2. GitHub에 커밋/푸시하면 Render API가 재배포됩니다. Render 환경변수에
   NAVER_API_HUB_CLIENT_ID와 NAVER_API_HUB_CLIENT_SECRET가 설정되어 있어야 최신글이 나옵니다.
3. 앱을 배포하려면 Flutter 프로젝트 mobile/에서 패키지를 받고 iOS/Android 빌드를 다시 해야 합니다.
   이 ZIP은 앱 소스 패치이며 설치 가능한 IPA/APK는 아닙니다.

주의
- Flutter 코드는 iOS와 Android가 공유합니다. 두 OS에서 각각 빌드 및 기기 테스트가 필요합니다.
- 백엔드 테스트와 Flutter 테스트는 이 환경에 pytest/Flutter SDK가 없어 실행하지 못했습니다.
- Python 파일 문법 컴파일과 git diff --check는 통과했습니다.
