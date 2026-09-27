import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:app_links/app_links.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:firebase_app_installations/firebase_app_installations.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'api_client.dart';
import 'firebase_options.dart';

final scaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();
bool firebaseReady = false;

@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
    firebaseReady = true;
    FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);
  } catch (_) {
    // Firebase is configured per app bundle after the project is linked to a Firebase project.
  }
  runApp(const IloveMiniApp());
}

const ink = Color(0xFF202125);
const brandRed = Color(0xFFBD2434);
const paper = Color(0xFFF4F4F6);

const favouredF66PhotoAsset = 'assets/images/mini_f66_favoured_red.png';
const maybachS580FrontAsset = 'assets/images/maybach-s580-front.webp';
const cafeMiniAlbumUrl = 'https://cafe.naver.com/f-e/cafes/13071593';
const partnerInquiryUrl = 'https://naver.me/xTb4h7ZR';
const iloveMiniWebsiteUrl = 'https://ilovemini.co.kr';

const iloveMiniCafeNotices = <Map<String, String>>[
  {'title': '[추석 이벤트] 우리 가족 자동차 자랑대회 🧧', 'category': '추석 이벤트', 'url': 'https://m.site.naver.com/2hkWt'},
  {'title': '6WB 디지털계기판 리콜가능성이 보일수도...', 'category': 'MINI 차량 정보', 'url': 'https://m.site.naver.com/2hkX3'},
  {'title': '9월에 어디 가지? 전국 가을 축제 드라이브 지도!', 'category': '드라이브 정보', 'url': 'https://m.site.naver.com/2hkX5'},
  {'title': '드라이아이스 에바클리닝+에어컨 필터 교체 이벤트!', 'category': '협력업체 이벤트', 'url': 'https://m.site.naver.com/2hkX7'},
  {'title': '[이벤트] 여름의 끝자락, 시원한 혜택은 계속! KUMHO:T SUMMER PROMOTION', 'category': '타이어 프로모션', 'url': 'https://m.site.naver.com/2hkXc'},
  {'title': '협력업체 군팩토리 카오디오 이벤트 START!', 'category': '협력업체 이벤트', 'url': 'https://m.site.naver.com/2hkXh'},
  {'title': '락업클러치 이상으로 인한 미션교체 대상(보증기간은 지난상황)', 'category': '정비 정보', 'url': 'https://naver.me/FlBvjooR'},
  {'title': '🏆 아이러브미니 공식랭킹 - 실시간 업데이트 (2026. 08. 31) 🏆', 'category': '공식 랭킹', 'url': 'https://m.site.naver.com/2hkXs'},
  {'title': '코스텔 충전기 사용하시는분들 참고하세요~', 'category': '전기차 정보', 'url': 'https://naver.me/G6RXgbZY'},
  {'title': '셀프 세차 중 잠금 이슈(+미니코리아 답변)', 'category': '사용자 정보', 'url': 'https://m.site.naver.com/2hkXw'},
  {'title': '신입등급일 때 등업이나 스티커 신청 시 유의할 점(신입이 적은 글)', 'category': '카페 이용 안내', 'url': 'https://naver.me/GGGDgrEP'},
];

Future<void> _openCafeNotice(BuildContext context, String url) async {
  final uri = Uri.tryParse(url);
  try {
    if (uri == null || uri.scheme != 'https' || uri.host.isEmpty ||
        !await launchUrl(uri, mode: LaunchMode.externalApplication)) throw Exception();
  } catch (_) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('카페 원문을 열지 못했습니다.')),
    );
  }
}

class CafeNoticeFeed extends StatelessWidget {
  const CafeNoticeFeed({this.previewCount = 2, super.key});
  final int previewCount;
  @override
  Widget build(BuildContext context) {
    final items = iloveMiniCafeNotices.take(previewCount).toList();
    final rest = iloveMiniCafeNotices.skip(previewCount).toList();
    return Column(children: [
      ...items.map((notice) => CafeNoticeTile(notice: notice, pinned: true)),
      if (rest.isNotEmpty) Card(clipBehavior: Clip.antiAlias, child: ExpansionTile(
        leading: const Icon(Icons.expand_more),
        title: const Text('나머지 공지 보기', style: TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text('${rest.length}건'),
        children: rest.map((notice) => CafeNoticeTile(notice: notice)).toList(),
      )),
    ]);
  }
}

const partnerBanners = <Map<String, String>>[
  {'asset': 'assets/images/partner-banner-kumho.webp', 'alt': '금호타이어와 타이어프로의 아이러브미니 제휴 회원 이벤트', 'url': 'https://m.site.naver.com/2hkXc'},
  {'asset': 'assets/images/partner-banner-deutsch.webp', 'alt': '도이치모터스 MINI 전시장 전차종 시승 안내'},
  {'asset': 'assets/images/partner-banner-printtrap.webp', 'alt': '프린트랩 수입차 부품과 자가 정비 지원 안내'},
  {'asset': 'assets/images/partner-banner-greeting.webp', 'alt': '같은 미니를 만나면 반가운 인사 캠페인'},
];

class AffiliateBannerCarousel extends StatefulWidget {
  const AffiliateBannerCarousel({super.key});
  @override
  State<AffiliateBannerCarousel> createState() => _AffiliateBannerCarouselState();
}

class _AffiliateBannerCarouselState extends State<AffiliateBannerCarousel> {
  int currentPage = 0;

  Future<void> _openBanner(Map<String, String> banner) async {
    final url = banner['url'];
    if (url != null) await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const SectionHeading(title: '제휴 배너', subtitle: '카페 제휴 소식'),
    const SizedBox(height: 9),
    SizedBox(height: 76, child: PageView.builder(
      itemCount: partnerBanners.length,
      onPageChanged: (index) => setState(() => currentPage = index),
      itemBuilder: (context, index) {
        final banner = partnerBanners[index];
        final image = ClipRRect(borderRadius: BorderRadius.circular(12), child: Image.asset(
          banner['asset']!, width: double.infinity, height: 76, fit: BoxFit.cover,
          semanticLabel: banner['alt'],
        ));
        final url = banner['url'];
        return Padding(padding: const EdgeInsets.only(right: 2), child: url == null
          ? image
          : Semantics(button: true, label: '${banner['alt']} 자세히 보기', child: InkWell(
              borderRadius: BorderRadius.circular(12), onTap: () => _openBanner(banner), child: image,
            )));
      },
    )),
    const SizedBox(height: 7),
    Row(mainAxisAlignment: MainAxisAlignment.center, children: List.generate(partnerBanners.length, (index) => AnimatedContainer(
      duration: const Duration(milliseconds: 180), margin: const EdgeInsets.symmetric(horizontal: 3),
      width: currentPage == index ? 15 : 5, height: 5,
      decoration: BoxDecoration(color: currentPage == index ? brandRed : const Color(0xFFD4D5D8), borderRadius: BorderRadius.circular(4)),
    ))),
  ]);
}

class CafeNoticeListPage extends StatelessWidget {
  const CafeNoticeListPage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('카페 공지사항')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      const Padding(padding: EdgeInsets.fromLTRB(4, 0, 4, 12), child: Text('제목을 누르면 아이러브미니 카페 원문이 열립니다.')),
      ...iloveMiniCafeNotices.map((notice) => CafeNoticeTile(notice: notice)),
    ]),
  );
}

class CafeNoticeTile extends StatelessWidget {
  const CafeNoticeTile({required this.notice, this.pinned = false, super.key});
  final Map<String, String> notice;
  final bool pinned;
  @override
  Widget build(BuildContext context) => Card(
    color: Theme.of(context).colorScheme.surface,
    clipBehavior: Clip.antiAlias,
    child: ListTile(
      leading: CircleAvatar(backgroundColor: pinned ? const Color(0xFFFBECEF) : Theme.of(context).colorScheme.primaryContainer,
        child: Icon(pinned ? Icons.push_pin_outlined : Icons.campaign_outlined, color: pinned ? brandRed : null)),
      title: Text(notice['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text('${notice['category'] ?? '카페 공지'} · 원문 열기'),
      trailing: pinned ? const Chip(label: Text('필독')) : const Icon(Icons.open_in_new),
      onTap: () => _openCafeNotice(context, notice['url'] ?? ''),
    ),
  );
}

bool hasFavouredF66Photo(Map<String, dynamic> vehicle) {
  final generation = '${vehicle['generation'] ?? ''}'.toLowerCase();
  final identity = '${vehicle['model_name'] ?? ''} ${vehicle['trim'] ?? ''}'.toLowerCase();
  final isF66 = generation.contains('f66') || generation.contains('4세대');
  final isFavoured = identity.contains('favoured') || identity.contains('페이버드');
  return isF66 && isFavoured;
}

bool hasMaybachPhoto(Map<String, dynamic> vehicle) =>
    '${vehicle['model_name'] ?? ''} ${vehicle['trim'] ?? ''}'.toLowerCase().contains('maybach');

String _favouredVehicleTitle(Map<String, dynamic> vehicle) {
  final model = (vehicle['model_name'] ?? 'MINI Cooper S').toString().trim();
  return model.toLowerCase().contains('favoured') || model.contains('페이버드') ? model : '$model Favoured';
}

class VehiclePhoto extends StatelessWidget {
  const VehiclePhoto({required this.vehicle, this.height = 118, super.key});
  final Map<String, dynamic> vehicle;
  final double height;
  @override
  Widget build(BuildContext context) {
    if (hasMaybachPhoto(vehicle)) {
      return SizedBox(height: height, width: double.infinity, child: Image.asset(
        maybachS580FrontAsset, fit: BoxFit.contain, alignment: Alignment.center,
        semanticLabel: 'Mercedes-Maybach S 580 차량 전면',
        errorBuilder: (context, error, stackTrace) => Center(child: Icon(Icons.directions_car_filled, size: height * .55, color: Theme.of(context).colorScheme.onSurfaceVariant)),
      ));
    }
    if (!hasFavouredF66Photo(vehicle)) return const SizedBox.shrink();
    return SizedBox(height: height, width: double.infinity, child: Image.asset(
      favouredF66PhotoAsset, fit: BoxFit.contain, alignment: Alignment.center,
      semanticLabel: '4세대 MINI Cooper S Favoured 차량 사진',
      errorBuilder: (context, error, stackTrace) => Center(child: Icon(Icons.directions_car_filled, size: height * .55, color: Theme.of(context).colorScheme.onSurfaceVariant)),
    ));
  }
}

String formatKilometers(dynamic value) {
  final raw = value?.toString();
  if (raw == null || raw.isEmpty || raw == '—') return '—';
  return raw.replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',');
}

class IloveMiniApp extends StatelessWidget {
  const IloveMiniApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'ILOVEMINI',
        debugShowCheckedModeBanner: false,
        scaffoldMessengerKey: scaffoldMessengerKey,
        theme: _appTheme(Brightness.light),
        darkTheme: _appTheme(Brightness.dark),
        themeMode: ThemeMode.system,
        home: const MainShell(),
      );
}

ThemeData _appTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;
  final background = isDark ? const Color(0xFF191A1E) : paper;
  final surface = isDark ? const Color(0xFF25262C) : Colors.white;
  final text = isDark ? const Color(0xFFF3F3F5) : ink;
  final muted = isDark ? const Color(0xFFB2B3BC) : const Color(0xFF686B73);
  final accent = isDark ? const Color(0xFFFF939B) : brandRed;
  final border = isDark ? const Color(0xFF3B3D44) : const Color(0xFFDFE0E4);
  final scheme = ColorScheme.fromSeed(seedColor: brandRed, brightness: brightness).copyWith(
    primary: accent, onPrimary: isDark ? ink : Colors.white,
    primaryContainer: isDark ? const Color(0xFF3D282E) : const Color(0xFFFBECEF),
    onPrimaryContainer: accent, surface: surface, onSurface: text,
    onSurfaceVariant: muted, outline: border, outlineVariant: border,
    secondaryContainer: isDark ? const Color(0xFF303137) : const Color(0xFFECECEF),
    onSecondaryContainer: text,
  );
  final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: BorderSide(color: border));
  return ThemeData(
    useMaterial3: true, brightness: brightness, scaffoldBackgroundColor: background,
    colorScheme: scheme, dividerColor: border,
    appBarTheme: AppBarTheme(backgroundColor: background, foregroundColor: text, surfaceTintColor: Colors.transparent, elevation: 0, toolbarHeight: 74),
    cardTheme: CardThemeData(color: surface, surfaceTintColor: Colors.transparent, elevation: 0, margin: const EdgeInsets.symmetric(vertical: 5), shape: shape),
    navigationBarTheme: NavigationBarThemeData(backgroundColor: background, surfaceTintColor: Colors.transparent, indicatorColor: scheme.primaryContainer, height: 76),
    inputDecorationTheme: InputDecorationTheme(filled: true, fillColor: surface,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: border)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: border)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: accent, width: 2))),
    filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(minimumSize: const Size(44, 46), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)))),
    outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(minimumSize: const Size(44, 46), foregroundColor: text, side: BorderSide(color: border), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)))),
    dialogTheme: DialogThemeData(backgroundColor: background, surfaceTintColor: Colors.transparent, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22))),
    bottomSheetTheme: BottomSheetThemeData(backgroundColor: background, surfaceTintColor: Colors.transparent),
  );
}

Future<void> showVehiclePassportQr(BuildContext context, Map<String, dynamic> vehicle) async {
  final publicId = vehicle['public_id']?.toString() ??
      (ApiClient.demoMode ? 'demo-${vehicle['id']}' : null);
  if (publicId == null || publicId.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('차량 QR 정보를 불러오지 못했습니다.')));
    return;
  }
  final data = 'ilovemini://vehicle/$publicId';
  await showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
    title: const Text('Vehicle Passport QR'),
    content: Column(mainAxisSize: MainAxisSize.min, children: [
      Text(vehicle['model_name']?.toString() ?? '등록 차량', style: const TextStyle(fontWeight: FontWeight.w800)),
      const SizedBox(height: 16),
      QrImageView(data: data, size: 220, backgroundColor: Colors.white),
      const SizedBox(height: 12),
      Text(ApiClient.demoMode
          ? '시제품 체험용 차량 QR입니다. 실제 차량이나 서버에 연결되지는 않습니다.'
          : '승인된 협력업체 담당자가 이 QR을 스캔해 정비이력을 등록합니다. 차량 QR 자체에는 차주 개인정보가 들어 있지 않습니다.', textAlign: TextAlign.center),
    ]),
    actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('닫기'))],
  ));
}

class MainShell extends StatefulWidget {
  const MainShell({super.key});
  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int tab = 0;
  bool signedIn = false;
  bool pushEnabled = false;
  final api = ApiClient();
  StreamSubscription<String>? installationSubscription;
  StreamSubscription<RemoteMessage>? messageSubscription;
  StreamSubscription<RemoteMessage>? openedSubscription;
  bool pushConfigured = false;

  @override
  void initState() {
    super.initState();
    ApiClient.sessionExpired.addListener(_onSessionExpired);
    _loadSession();
    if (firebaseReady) {
      openedSubscription = FirebaseMessaging.onMessageOpenedApp.listen(_handlePushOpen);
      FirebaseMessaging.instance.getInitialMessage().then((message) {
        if (message != null) _handlePushOpen(message);
      }, onError: (Object _) {});
    }
  }

  void _onSessionExpired() {
    if (!mounted) return;
    setState(() { signedIn = false; tab = 3; });
    scaffoldMessengerKey.currentState?.showSnackBar(
      const SnackBar(content: Text('로그인이 만료되었습니다. 다시 로그인해 주세요.')));
  }

  Future<void> _loadSession() async {
    if (ApiClient.demoMode) {
      if (mounted) setState(() { signedIn = true; pushEnabled = false; });
      return;
    }
    final values = await Future.wait([api.isSignedIn, api.pushNotificationsEnabled]);
    if (!mounted) return;
    setState(() {
      signedIn = values[0];
      pushEnabled = values[1];
    });
    if (signedIn && pushEnabled) await _configurePush();
  }

  Future<void> _configurePush() async {
    if (!signedIn || !pushEnabled || pushConfigured || !firebaseReady) return;
    pushConfigured = true;
    try {
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission(alert: true, badge: true, sound: true);
      if (settings.authorizationStatus == AuthorizationStatus.denied || settings.authorizationStatus == AuthorizationStatus.notDetermined) {
        pushConfigured = false;
        await api.setPushNotificationsEnabled(false);
        if (mounted) setState(() => pushEnabled = false);
        scaffoldMessengerKey.currentState?.showSnackBar(const SnackBar(content: Text('휴대폰 설정에서 알림 권한을 허용해 주세요.')));
        return;
      }
      final installationId = await FirebaseInstallations.instance.getId();
      await api.registerPushInstallation(installationId, defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android');
      installationSubscription = FirebaseInstallations.instance.onIdChange.listen((newId) {
        api.registerPushInstallation(newId, defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android').then((_) {}, onError: (Object _) {});
      });
      messageSubscription = FirebaseMessaging.onMessage.listen((message) {
        final notice = message.notification;
        if (notice == null) return;
        scaffoldMessengerKey.currentState?.showSnackBar(SnackBar(content: Text('${notice.title ?? '아이러브미니'} · ${notice.body ?? ''}')));
      });
    } catch (_) {
      // Missing Firebase platform configuration must not block sign-in or core app use.
      pushConfigured = false;
      scaffoldMessengerKey.currentState?.showSnackBar(const SnackBar(content: Text('푸시 알림 설정을 완료하지 못했습니다. Firebase 연결을 확인해 주세요.')));
    }
  }

  Future<void> _setPushEnabled(bool enabled) async {
    if (enabled && !firebaseReady) {
      scaffoldMessengerKey.currentState?.showSnackBar(const SnackBar(content: Text('Firebase 앱 연결 설정을 먼저 완료해 주세요.')));
      return;
    }
    await api.setPushNotificationsEnabled(enabled);
    if (mounted) setState(() => pushEnabled = enabled);
    if (enabled) {
      await _configurePush();
    } else {
      await _removePushInstallation();
    }
  }

  void _handlePushOpen(RemoteMessage message) {
    if (message.data['type'] == 'reminder' && mounted) setState(() => tab = 1);
  }

  Future<void> _removePushInstallation() async {
    try {
      final installationId = await FirebaseInstallations.instance.getId();
      await api.unregisterPushInstallation(installationId);
    } catch (_) {
      // The next server send removes expired tokens automatically.
    }
    pushConfigured = false;
    await installationSubscription?.cancel();
    await messageSubscription?.cancel();
  }

  Future<void> _login() async {
    if (ApiClient.demoMode) {
      scaffoldMessengerKey.currentState?.showSnackBar(const SnackBar(content: Text('로그인과 차계부는 API 서버 연결 후 확인할 수 있습니다.')));
      return;
    }
    final ok = await Navigator.of(context).push<bool>(MaterialPageRoute(builder: (_) => LoginPage(api: api)));
    if (ok == true && mounted) {
      setState(() => signedIn = true);
      await _configurePush();
    }
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Semantics(button: true, label: 'ILOVEMINI 홈으로 이동', child: InkWell(
        mouseCursor: SystemMouseCursors.click,
        borderRadius: BorderRadius.circular(8),
        onTap: () => setState(() => tab = 0),
        child: const Row(mainAxisSize: MainAxisSize.min, children: [BrandLogo(height: 52), SizedBox(width: 12), Text('ILOVEMINI', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, letterSpacing: 2))]),
      ))),
      body: switch (tab) {
        0 => HomePage(api: api, signedIn: signedIn, onOpenGarage: () => setState(() => tab = 1), onLogin: _login),
        1 => GaragePage(key: ValueKey('garage-$signedIn'), api: api, signedIn: signedIn, onLogin: _login),
        2 => CatalogPage(api: api, path: 'partners', title: 'ILOVEMINI 협력업체'),
        _ => AccountPage(api: api, signedIn: signedIn, pushEnabled: pushEnabled, onPushChanged: _setPushEnabled, onLogin: _login, onLogout: () async { await _removePushInstallation(); await api.logout(); if (mounted) setState(() { signedIn = false; pushEnabled = false; }); }, onManageVehicles: () => setState(() => tab = 1)),
      },
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: (value) => setState(() => tab = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: '홈'),
          NavigationDestination(icon: Icon(Icons.directions_car_outlined), selectedIcon: Icon(Icons.directions_car), label: '내 차'),
          NavigationDestination(icon: Icon(Icons.storefront_outlined), selectedIcon: Icon(Icons.storefront), label: '업체'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: '마이'),
        ],
      ),
    );
  }

  @override
  void dispose() {
    ApiClient.sessionExpired.removeListener(_onSessionExpired);
    installationSubscription?.cancel();
    messageSubscription?.cancel();
    openedSubscription?.cancel();
    super.dispose();
  }
}

class HomePage extends StatelessWidget {
  const HomePage({required this.api, required this.signedIn, required this.onOpenGarage, required this.onLogin, super.key});
  final VoidCallback onOpenGarage;
  final VoidCallback onLogin;
  final ApiClient api;
  final bool signedIn;
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.fromLTRB(20, 14, 20, 28), children: [
    VehicleOverview(key: ValueKey('overview-$signedIn'), api: api, signedIn: signedIn, onGarage: onOpenGarage),
    const SizedBox(height: 18),
    const CafeKnowledgeSearch(),
    const SizedBox(height: 18),
    AttendanceCheckinCard(api: api, signedIn: signedIn, onLogin: onLogin),
    const SizedBox(height: 8),
    const SectionHeading(title: '카페 공지사항', subtitle: '필독 2건'),
    const CafeNoticeFeed(previewCount: 2),
    const SizedBox(height: 12),
    const CafeMiniAlbumPreview(),
    const SizedBox(height: 12),
    const AffiliateBannerCarousel(),
    if (ApiClient.demoMode) ...[
      const SizedBox(height: 10),
      Text('차량 정보는 시제품 예시입니다.', style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurfaceVariant)),
    ],
  ]);
}

class CafeKnowledgeSearch extends StatefulWidget {
  const CafeKnowledgeSearch({super.key});
  @override
  State<CafeKnowledgeSearch> createState() => _CafeKnowledgeSearchState();
}

class _CafeKnowledgeSearchState extends State<CafeKnowledgeSearch> {
  final queryController = TextEditingController();
  List<Map<String, String>> results = [];
  bool searched = false;

  void search(String value) {
    final query = value.trim().toLowerCase();
    if (query.isEmpty) return;
    final terms = query.split(RegExp(r'\s+')).where((term) => term.length > 1).toList();
    setState(() {
      searched = true;
      results = iloveMiniCafeNotices.where((notice) {
        final text = '${notice['title']} ${notice['category']}'.toLowerCase();
        return terms.any((term) => text.contains(term));
      }).take(3).toList();
    });
  }

  Future<void> searchNaver() async {
    final query = '${queryController.text.trim()} 아이러브미니';
    final uri = Uri.https('search.naver.com', '/search.naver', {'where': 'article', 'query': query});
    try {
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) throw Exception();
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('네이버 검색을 열지 못했습니다.')));
    }
  }

  @override
  void dispose() { queryController.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Row(children: [
      Container(width: 38, height: 38, decoration: BoxDecoration(color: brandRed, borderRadius: BorderRadius.circular(12)), alignment: Alignment.center, child: const Icon(Icons.manage_search_rounded, color: Colors.white)),
      const SizedBox(width: 11),
      const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('MINI 정비 지식 검색', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
        Text('연결된 아이러브미니 카페 공지와 정비 정보를 찾아보세요.', style: TextStyle(fontSize: 12)),
      ])),
    ]),
    const SizedBox(height: 12),
    TextField(controller: queryController, textInputAction: TextInputAction.search, onSubmitted: search,
      decoration: InputDecoration(labelText: '정비 질문 또는 검색어', hintText: '예: 락업클러치 미션 교체', suffixIcon: IconButton(tooltip: '검색', onPressed: () => search(queryController.text), icon: const Icon(Icons.search)))),
    const SizedBox(height: 8),
    Wrap(spacing: 7, runSpacing: 4, children: ['락업클러치·미션', '카오디오·전장', '타이어'].map((prompt) => ActionChip(label: Text(prompt), onPressed: () {
      final query = prompt == '락업클러치·미션' ? '락업클러치 미션 교체' : prompt == '카오디오·전장' ? '카오디오 오디오' : '타이어';
      queryController.text = query;
      search(query);
    })).toList()),
    if (searched) ...[
      const Divider(height: 22),
      Text(results.isEmpty
        ? '연결된 공지 목록에서는 관련 글을 찾지 못했습니다. 네이버 카페 게시글 검색으로 더 찾아보세요.'
        : '연결된 카페 공지에서 관련 글 ${results.length}건을 찾았습니다. 자료가 제목과 링크에 한정되어 있으니 정비 내용은 원문에서 확인해 주세요.',
        style: const TextStyle(fontSize: 13, height: 1.45)),
      ...results.map((notice) => CafeNoticeTile(notice: notice)),
    ],
    Align(alignment: Alignment.centerRight, child: TextButton.icon(onPressed: searchNaver, icon: const Icon(Icons.open_in_new, size: 16), label: const Text('네이버 카페 게시글에서 더 검색'))),
    Text('시제품은 연결된 공지 목록을 검색합니다. 전체 게시글 AI 요약은 허용된 데이터 연동 후 제공됩니다.', style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurfaceVariant)),
  ])));
}

class AttendanceCheckinCard extends StatefulWidget {
  const AttendanceCheckinCard({required this.api, required this.signedIn, required this.onLogin, super.key});
  final ApiClient api;
  final bool signedIn;
  final VoidCallback onLogin;
  @override
  State<AttendanceCheckinCard> createState() => _AttendanceCheckinCardState();
}

class _AttendanceCheckinCardState extends State<AttendanceCheckinCard> {
  late Future<Map<String, dynamic>> summary;
  bool busy = false;
  @override
  void initState() { super.initState(); summary = _load(); }
  @override
  void didUpdateWidget(covariant AttendanceCheckinCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.signedIn != widget.signedIn) summary = _load();
  }
  Future<Map<String, dynamic>> _load() => !widget.signedIn && !ApiClient.demoMode
    ? Future.value({'balance_points': 0, 'streak_days': 0, 'checked_in_today': false, 'checkins': []})
    : widget.api.attendanceSummary();

  Future<void> _checkIn() async {
    if (!widget.signedIn && !ApiClient.demoMode) { widget.onLogin(); return; }
    setState(() => busy = true);
    try {
      final result = await widget.api.checkIn();
      if (!mounted) return;
      setState(() => summary = Future.value(result));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']?.toString() ?? '출석 상태를 확인했어요.')));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('출석 처리에 실패했어요. 잠시 후 다시 시도해 주세요.')));
    } finally { if (mounted) setState(() => busy = false); }
  }

  @override
  Widget build(BuildContext context) => Card(
    clipBehavior: Clip.antiAlias,
    child: Padding(padding: const EdgeInsets.all(16), child: FutureBuilder<Map<String, dynamic>>(
      future: summary,
      builder: (context, snapshot) {
        final data = snapshot.data ?? const <String, dynamic>{};
        final points = (data['balance_points'] as num?)?.toInt() ?? 0;
        final streak = (data['streak_days'] as num?)?.toInt() ?? 0;
        final checked = data['checked_in_today'] == true;
        final checkins = (data['checkins'] as List? ?? const []).take(7).toList();
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.event_available, color: brandRed),
            const SizedBox(width: 8),
            const Expanded(child: Text('오늘의 출석체크', style: TextStyle(fontWeight: FontWeight.w800))),
            Text('$points P', style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900, color: brandRed)),
          ]),
          const SizedBox(height: 6),
          Text('매일 출석 1,000P · 7일 연속 보너스 3,000P · 현재 $streak일 연속', style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
          if (checkins.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(spacing: 6, runSpacing: 6, children: checkins.map((row) => Chip(
              visualDensity: VisualDensity.compact,
              avatar: const Icon(Icons.check, size: 14),
              label: Text('${row['date']} · +${row['points']}P', style: const TextStyle(fontSize: 10)),
            )).toList()),
          ],
          const SizedBox(height: 10),
          SizedBox(width: double.infinity, child: FilledButton.icon(
            onPressed: busy || snapshot.connectionState == ConnectionState.waiting ? null : _checkIn,
            icon: Icon(checked ? Icons.check_circle_outline : Icons.touch_app_outlined),
            label: Text(busy ? '처리 중…' : !widget.signedIn && !ApiClient.demoMode ? '로그인하고 출석하기' : checked ? '오늘 출석 완료' : '출석하고 ${streak > 0 && streak % 7 == 6 ? '4,000' : '1,000'}P 받기'),
          )),
          const SizedBox(height: 3),
          const Center(child: Text('네이버페이 전환은 제휴 확정 후 제공됩니다.', style: TextStyle(fontSize: 12, color: Colors.grey))),
        ]);
      },
    )),
  );
}

class CafeMiniAlbumPreview extends StatelessWidget {
  const CafeMiniAlbumPreview({super.key});
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    const posts = [
      {'image': 'album-01.jpg', 'title': '연휴 끝', 'author': '꼬마악동', 'meta': '01:05 · 조회 137'},
      {'image': 'album-02.jpg', 'title': '명절이라 디테일링 …', 'author': '구름아', 'meta': '26.09.25 · 조회 220'},
      {'image': 'album-03.jpg', 'title': '몇년만에 손세차.. F60', 'author': '케인지F60촌놈', 'meta': '26.09.25 · 조회 147'},
      {'image': 'album-04.jpg', 'title': '블랙의 세차', 'author': '집가이', 'meta': '26.09.25 · 조회 187'},
      {'image': 'album-05.jpg', 'title': '3개월만에 차 받았어…', 'author': '빵빵도우', 'meta': '26.09.23 · 조회 250'},
      {'image': 'album-06.jpg', 'title': '하루를 마감하는 미니', 'author': '집가이', 'meta': '26.09.23 · 조회 159'},
    ];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SectionHeading(title: '미니앨범', subtitle: '카페 회원들의 MINI 이야기'),
      const SizedBox(height: 8),
      Card(
        color: theme.colorScheme.surface,
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: posts.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3, crossAxisSpacing: 9, mainAxisSpacing: 14, mainAxisExtent: 181,
            ),
            itemBuilder: (context, index) {
              final post = posts[index];
              return Semantics(
                button: true,
                label: '${post['title']}, ${post['author']}. 아이러브미니 카페 미니앨범 열기',
                child: InkWell(
                  borderRadius: BorderRadius.circular(10),
                  onTap: () => _openCafeNotice(context, cafeMiniAlbumUrl),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: AspectRatio(
                        aspectRatio: 1,
                        child: Image.asset('assets/images/mini-album/${post['image']}', fit: BoxFit.cover),
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(post['title']!, maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 3),
                    Text(post['author']!, maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface)),
                    const SizedBox(height: 2),
                    Text(post['meta']!, maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurfaceVariant)),
                  ]),
                ),
              );
            },
          ),
        ),
      ),
    ]);
  }
}

class VehicleOverview extends StatefulWidget {
  const VehicleOverview({required this.api, required this.signedIn, required this.onGarage, super.key});
  final ApiClient api;
  final bool signedIn;
  final VoidCallback onGarage;
  @override
  State<VehicleOverview> createState() => _VehicleOverviewState();
}
class _VehicleOverviewState extends State<VehicleOverview> {
  late final Future<List<Map<String, dynamic>>> vehicles;
  @override
  void initState() {
    super.initState();
    vehicles = widget.signedIn || ApiClient.demoMode ? widget.api.list('vehicles') : Future.value([]);
  }
  @override
  Widget build(BuildContext context) => FutureBuilder<List<Map<String, dynamic>>>(future: vehicles, builder: (context, snapshot) {
    final vehicle = snapshot.data?.firstOrNull;
    final loading = snapshot.connectionState == ConnectionState.waiting;
    final subtitle = vehicle == null ? (snapshot.hasError ? '차량 정보를 불러오지 못했습니다' : loading ? '차량 정보를 불러오는 중' : '차량을 등록하고 기록을 시작하세요')
      : [vehicle['generation'], vehicle['trim'], vehicle['model_year'] == null ? null : '${vehicle['model_year']}년형']
          .where((part) => part != null && part.toString().isNotEmpty).join(' · ');
    final modelName = (vehicle?['model_name'] ?? '내 차량').toString();
    final vehicleTitle = vehicle != null && hasFavouredF66Photo(vehicle) && !modelName.toLowerCase().contains('favoured')
        ? '$modelName Favoured' : modelName;
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: widget.onGarage,
      child: Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Expanded(child: Text('내 차량', style: TextStyle(fontWeight: FontWeight.w800))),
          TextButton(onPressed: widget.onGarage, child: const Text('차량 관리')),
        ]),
        if (vehicle != null && (hasFavouredF66Photo(vehicle) || hasMaybachPhoto(vehicle)))
          VehiclePhoto(vehicle: vehicle, height: 118),
        Text(vehicleTitle, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: -.5)),
        const SizedBox(height: 4),
        Text(subtitle, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
        const SizedBox(height: 8),
        Row(children: [
          const Icon(Icons.speed, size: 17), const SizedBox(width: 5),
          Text('현재 주행거리  ${vehicle == null ? '미등록' : '${formatKilometers(vehicle['current_odometer_km'])} km'}', style: const TextStyle(fontWeight: FontWeight.w700)),
          const Spacer(), const Icon(Icons.chevron_right),
        ]),
      ]))),
    );
  });
}

class CatalogPage extends StatefulWidget {
  const CatalogPage({required this.api, required this.path, required this.title, this.compact = false, super.key});
  final ApiClient api;
  final String path, title;
  final bool compact;
  @override
  State<CatalogPage> createState() => _CatalogPageState();
}

class _CatalogPageState extends State<CatalogPage> {
  static const _regionalCollisionPartners = <Map<String, dynamic>>[
    {'id': 'local-koreadiesel', 'name': '한국디젤카연구소 논산', 'region': '충남 논산', 'address': '충남 논산', 'region_group': '전라/경상/충청 협력업체', 'category': '사고수리 전문', 'service_categories': ['사고수리', '판금·도색', '디젤 정비', '정비'], 'cafe_url': 'https://cafe.naver.com/f-e/cafes/13071593/menus/543', 'map_url': 'https://map.naver.com/p/search/%ED%95%9C%EA%B5%AD%EB%94%94%EC%A0%A4%EC%B9%B4%EC%97%B0%EA%B5%AC%EC%86%8C%20%EB%85%BC%EC%82%B0'},
    {'id': 'local-ablemotors', 'name': '에이블모터스 부산', 'region': '부산', 'address': '부산', 'region_group': '전라/경상/충청 협력업체', 'category': '사고수리 전문', 'service_categories': ['사고수리', '판금·도색', '수입차 정비', '정비'], 'cafe_url': 'https://cafe.naver.com/f-e/cafes/13071593/menus/288', 'map_url': 'https://map.naver.com/p/search/%EC%97%90%EC%9D%B4%EB%B8%94%EB%AA%A8%ED%84%B0%EC%8A%A4%20%EB%B6%80%EC%82%B0'},
    {'id': 'local-jetly', 'name': '제틀리시 부산', 'region': '부산', 'address': '부산', 'region_group': '전라/경상/충청 협력업체', 'category': '사고수리 전문', 'service_categories': ['사고수리', '판금·도색', '정비'], 'cafe_url': 'https://cafe.naver.com/f-e/cafes/13071593/menus/636', 'map_url': 'https://map.naver.com/p/search/%EC%A0%9C%ED%8B%80%EB%A6%AC%EC%8B%9C%20%EB%B6%80%EC%82%B0'},
  ];
  List<Map<String, dynamic>> _includeRegionalCollisionPartners(List<Map<String, dynamic>> source) {
    final merged = source.map((item) => Map<String, dynamic>.from(item)).toList();
    for (final local in _regionalCollisionPartners) {
      final index = merged.indexWhere((item) => item['name'] == local['name']);
      if (index < 0) {
        merged.add(Map<String, dynamic>.from(local));
      } else {
        final existing = merged[index];
        final categories = (existing['service_categories'] as List? ?? const []).map((value) => value.toString()).toSet();
        categories.addAll((local['service_categories'] as List).map((value) => value.toString()));
        merged[index] = {...existing, ...local, 'id': existing['id'], 'service_categories': categories.toList()};
      }
    }
    return merged;
  }
  late Future<List<Map<String, dynamic>>> itemsFuture;
  String query = '', filter = '전체';
  @override
  void initState() { super.initState(); itemsFuture = widget.api.list(widget.path); }
  @override
  void didUpdateWidget(covariant CatalogPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path || oldWidget.api != widget.api) {
      itemsFuture = widget.api.list(widget.path); query = ''; filter = '전체';
    }
  }
  Future<void> reload() async {
    final future = widget.api.list(widget.path);
    setState(() => itemsFuture = future);
    try { await future; } catch (_) { /* FutureBuilder displays the error. */ }
  }
  bool matches(Map<String, dynamic> item) {
    final categories = (item['service_categories'] as List? ?? []).join(' ');
    final text = '${item['name']} ${item['region']} $categories'.toLowerCase();
    final region = (item['region'] ?? '').toString();
    final categoryMatch = switch (filter) {
      '정비' => categories.contains('정비') || categories.contains('수입차'),
      '사고수리' => categories.contains('사고') || categories.contains('판금'),
      '차량유리' => categories.contains('유리'),
      '오디오·전장' => categories.contains('오디오') || categories.contains('전장'),
      '휠·타이어' => categories.contains('휠') || categories.contains('타이어'),
      '부품·튜닝' => categories.contains('부품') || categories.contains('튜닝'),
      '신차패키지' => _partnerSpecialty(item) == '신차패키지',
      '수도권' => _partnerRegionGroup(item) == '서울/경기 협력업체' && _partnerSpecialty(item) != '신차패키지',
      '전라/경상/충청' => _partnerRegionGroup(item) == '전라/경상/충청 협력업체',
      _ => true,
    };
    return categoryMatch && text.contains(query.trim().toLowerCase());
  }
  void openItem(Map<String, dynamic> item) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => widget.path == 'partners'
      ? PartnerDetailPage(api: widget.api, partner: item)
      : CatalogDetailPage(api: widget.api, path: widget.path, item: item)));
  }
  String _partnerRegionGroup(Map<String, dynamic> item) {
    final group = '${item['region_group'] ?? item['group'] ?? ''}';
    if (group.contains('신차패키지')) return '신차패키지';
    if (group.contains('전라') || group.contains('경상') || group.contains('충청')) return '전라/경상/충청 협력업체';
    final region = '${item['region'] ?? ''}';
    if (RegExp(r'부산|경남|경북|충남|충북|전남|전북|대전|광주|울산|세종|논산').hasMatch(region)) return '전라/경상/충청 협력업체';
    return '서울/경기 협력업체';
  }
  String _partnerSpecialty(Map<String, dynamic> item) {
    final text = '${item['category'] ?? ''} ${(item['service_categories'] as List? ?? []).join(' ')}';
    if (text.contains('신차')) return '신차패키지';
    if (text.contains('사고')) return '사고수리 전문';
    if (text.contains('유리')) return '차량유리 전문';
    if (RegExp(r'전장|오디오|튜닝|부품').hasMatch(text)) return '전장류 전문';
    if (RegExp(r'휠|타이어').hasMatch(text)) return '휠 전문';
    return '정비 전문';
  }
  bool _partnerHasSpecialty(Map<String, dynamic> item, String specialty) {
    final text = '${item['category'] ?? ''} ${(item['service_categories'] as List? ?? []).join(' ')}';
    return switch (specialty) {
      '사고수리 전문' => text.contains('사고') || text.contains('판금'),
      '차량유리 전문' => text.contains('유리'),
      '전장류 전문' => RegExp(r'전장|오디오').hasMatch(text),
      '휠 전문' => RegExp(r'휠|타이어').hasMatch(text),
      '정비 전문' => RegExp(r'정비|수리|서비스|디젤').hasMatch(text),
      _ => _partnerSpecialty(item) == specialty,
    };
  }
  bool _partnerInfoPending(Map<String, dynamic> item) =>
      (item['region'] ?? '').toString().contains('확인 필요') && (item['cafe_url'] ?? '').toString().isEmpty;
  List<Widget> _partnerGroupTiles(List<Map<String, dynamic>> items) {
    const regions = ['서울/경기 협력업체', '전라/경상/충청 협력업체'];
    const specialties = ['신차패키지', '사고수리 전문', '차량유리 전문', '전장류 전문', '휠 전문', '정비 전문'];
    final packages = items.where((item) => _partnerSpecialty(item) == '신차패키지').toList();
    return [
      if (packages.isNotEmpty) Card(clipBehavior: Clip.antiAlias, child: ExpansionTile(
        title: const Text('신차패키지', style: TextStyle(fontWeight: FontWeight.w800)),
        subtitle: Text('${packages.length}곳 · 지역·연락처 확인 중'),
        children: packages.map((item) => ListTile(
          title: Text((item['name'] ?? '').toString()),
          subtitle: Text(_partnerInfoPending(item) ? '정보 확인 중 · 지역 미확인' : (item['region'] ?? '').toString()),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => openItem(item),
        )).toList(),
      )),
      ...regions.map((region) {
      final regionItems = items.where((item) => _partnerSpecialty(item) != '신차패키지' && _partnerRegionGroup(item) == region).toList();
      final grouped = <String, List<Map<String, dynamic>>>{for (final name in specialties) name: regionItems.where((item) => _partnerHasSpecialty(item, name)).toList()};
      return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(padding: const EdgeInsets.fromLTRB(8, 16, 8, 6), child: Row(children: [
          Expanded(child: Text(region, style: const TextStyle(fontWeight: FontWeight.w800))),
          Text('${regionItems.length}곳', style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant, fontSize: 12)),
        ])),
        ...specialties.where((name) => grouped[name]!.isNotEmpty).map((name) => Card(clipBehavior: Clip.antiAlias, child: ExpansionTile(
          title: Text(name, style: const TextStyle(fontWeight: FontWeight.w700)),
          subtitle: Text('${grouped[name]!.length}곳'),
          children: grouped[name]!.map((item) => ListTile(
            title: Text((item['name'] ?? '').toString()),
            subtitle: Text((item['region'] ?? '').toString()),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => openItem(item),
          )).toList(),
        ))),
      ]);
      }),
    ];
  }
  @override
  Widget build(BuildContext context) {
    final content = FutureBuilder<List<Map<String, dynamic>>>(
      future: itemsFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator()));
        }
        if (snapshot.hasError) return Column(children: [
          const InfoCard(text: '목록을 불러오지 못했습니다. 인터넷 연결과 로그인 상태를 확인해 주세요.'),
          TextButton(onPressed: reload, child: const Text('다시 시도')),
        ]);
        final apiItems = snapshot.data ?? [];
        final isPartners = widget.path == 'partners';
        final all = isPartners ? _includeRegionalCollisionPartners(apiItems) : apiItems;
        final items = isPartners ? all.where(matches).toList() : all;
        return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          if (isPartners) ...[
            if (!widget.compact) ...[
              Text('ILOVEMINI 협력업체\n성지를 찾아요', style: const TextStyle(fontSize: 25, height: 1.12, fontWeight: FontWeight.w900, letterSpacing: -0.7)),
              const SizedBox(height: 8),
              Text('기존에 확인된 협력업체를 분야별로 살펴보고 문의하세요.', style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
              const SizedBox(height: 18),
              TextField(decoration: const InputDecoration(labelText: '업체명, 지역, 서비스 검색', prefixIcon: Icon(Icons.search)),
                onChanged: (value) => setState(() => query = value)),
              const SizedBox(height: 12),
              Wrap(spacing: 8, runSpacing: 8, children: ['전체', '정비', '사고수리', '차량유리', '오디오·전장', '휠·타이어', '부품·튜닝', '신차패키지', '수도권', '전라/경상/충청'].map((name) => ChoiceChip(
                label: Text(name), selected: filter == name,
                onSelected: (_) => setState(() => filter = name))).toList()),
            ],
            Padding(padding: const EdgeInsets.symmetric(vertical: 12),
              child: Text('등록된 협력업체 ${all.length}곳 · 표시 ${items.length}곳')),
          ],
          if (items.isEmpty) InfoCard(text: all.isEmpty ? widget.title : '검색 조건에 맞는 업체가 없습니다.'),
          if (isPartners) ..._partnerGroupTiles(items)
          else ...items.map((item) => Card(clipBehavior: Clip.antiAlias, child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
            leading: CircleAvatar(backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: Text(widget.path == 'notices' ? '📣' : '🎁', style: const TextStyle(fontSize: 21))),
            title: Row(children: [
              Expanded(child: Text((item['title'] ?? item['name'] ?? '').toString(), style: const TextStyle(fontWeight: FontWeight.w800))),
              if (item['is_new'] == true) const _NewBadge(),
              if (item['is_sponsored'] == true) const _SponsoredBadge(),
            ]),
            subtitle: Text((item['summary'] ?? item['region'] ?? item['description'] ?? '').toString(), maxLines: widget.compact ? 2 : 3, overflow: TextOverflow.ellipsis),
            trailing: const Icon(Icons.chevron_right), onTap: () => openItem(item),
          ))),
        ]);
      });
    if (widget.compact) return content;
    return RefreshIndicator(onRefresh: reload, child: ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(20), children: [content]));
  }
}

class CatalogDetailPage extends StatelessWidget {
  const CatalogDetailPage({required this.api, required this.path, required this.item, super.key});
  final ApiClient api;
  final String path;
  final Map<String, dynamic> item;
  Future<void> openLink(BuildContext context, String value) async {
    final uri = Uri.tryParse(value);
    try {
      if (uri == null || !['https', 'http'].contains(uri.scheme) || uri.host.isEmpty ||
          !await launchUrl(uri, mode: LaunchMode.externalApplication)) throw Exception();
    } catch (_) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('원문을 열지 못했습니다.')));
    }
  }
  Future<void> openPartner(BuildContext context) async {
    try {
      final rows = await api.list('partners');
      final partner = rows.where((row) => row['id'] == item['partner']).firstOrNull;
      if (!context.mounted) return;
      if (partner == null) throw Exception();
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => PartnerDetailPage(api: api, partner: partner)));
    } catch (_) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('업체 정보를 불러오지 못했습니다.')));
    }
  }
  @override
  Widget build(BuildContext context) {
    final original = (item['original_url'] ?? '').toString();
    final body = (item['body'] ?? '').toString();
    return Scaffold(appBar: AppBar(title: Text(path == 'notices' ? '카페 소식' : '협력업체 혜택')),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        Text((item['title'] ?? '').toString(), style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 16),
        Text(body.isNotEmpty ? body : (item['summary'] ?? item['description'] ?? '상세 내용이 없습니다.').toString()),
        if ((item['redemption_instructions'] ?? '').toString().isNotEmpty) ...[
          const SizedBox(height: 16), InfoCard(text: item['redemption_instructions'].toString()),
        ],
        if (original.isNotEmpty) TextButton.icon(onPressed: () => openLink(context, original), icon: const Icon(Icons.open_in_new), label: const Text('카페 원문 보기')),
        if (path == 'offers' && item['partner'] != null) FilledButton.icon(onPressed: () => openPartner(context), icon: const Icon(Icons.storefront), label: const Text('업체 정보 및 문의')),
      ]));
  }
}

class PartnerDetailPage extends StatelessWidget {
  const PartnerDetailPage({required this.api, required this.partner, super.key});
  final ApiClient api;
  final Map<String, dynamic> partner;

  Future<void> _launch(BuildContext context, Uri uri) async {
    try {
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication) && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('연결할 앱을 열지 못했습니다.')));
      }
    } catch (_) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('연결할 앱을 열지 못했습니다.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final name = (partner['name'] ?? '협력업체').toString();
    final phone = (partner['phone'] ?? '').toString();
    final address = (partner['address'] ?? '').toString();
    final mapLink = (partner['map_url'] ?? '').toString();
    final cafeLink = (partner['cafe_url'] ?? '').toString();
    final infoPending = (partner['region'] ?? '').toString().contains('확인 필요') && cafeLink.isEmpty;
    final categories = (partner['service_categories'] as List? ?? const []).map((item) => item.toString()).toList();
    final details = <Widget>[
      if (address.isNotEmpty) ListTile(leading: const Icon(Icons.location_on_outlined), title: const Text('주소'), subtitle: Text(address)),
      if (phone.isNotEmpty) ListTile(leading: const Icon(Icons.call_outlined), title: const Text('전화번호'), subtitle: Text(phone)),
      if ((partner['hours'] ?? '').toString().isNotEmpty) ListTile(leading: const Icon(Icons.schedule_outlined), title: const Text('영업시간'), subtitle: Text(partner['hours'].toString())),
    ];
    final mapUri = Uri.tryParse(mapLink) ?? Uri();
    final usableMapUri = mapLink.isNotEmpty && mapUri.hasScheme
        ? mapUri
        : Uri.https('map.naver.com', '/p/search/$name ${address}'.trim());
    return Scaffold(
      appBar: AppBar(title: const Text('업체 정보')),
      body: ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 28), children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(color: ink, borderRadius: BorderRadius.circular(22)),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (partner['is_sponsored'] == true) const _SponsoredBadge(),
            const SizedBox(height: 12),
            Text(name, style: const TextStyle(color: Colors.white, fontSize: 25, fontWeight: FontWeight.w900)),
            if (infoPending) ...[
              const SizedBox(height: 10),
              const Chip(avatar: Icon(Icons.info_outline, size: 18), label: Text('정보 확인 중')),
            ],
            if ((partner['region'] ?? '').toString().isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(partner['region'].toString(), style: const TextStyle(color: Color(0xFFD7DCDD))),
            ],
          ]),
        ),
        if (categories.isNotEmpty) ...[
          const SizedBox(height: 18),
          Wrap(spacing: 8, runSpacing: 8, children: categories.map((category) => Chip(label: Text(category))).toList()),
        ],
        if ((partner['description'] ?? '').toString().isNotEmpty) ...[
          const SizedBox(height: 18),
          const SectionHeading(title: '업체 소개', subtitle: '서비스 안내'),
          Card(child: Padding(padding: const EdgeInsets.all(18), child: Text(partner['description'].toString(), style: const TextStyle(height: 1.5)))),
        ],
        if (details.isNotEmpty) ...[
          const SizedBox(height: 18),
          const SectionHeading(title: '기본 정보', subtitle: '방문 전 확인해 주세요'),
          Card(child: Column(children: details)),
        ],
        const SizedBox(height: 12),
        if (phone.isNotEmpty || mapLink.isNotEmpty || address.isNotEmpty)
          Row(children: [
            if (phone.isNotEmpty) Expanded(child: FilledButton.icon(onPressed: () => _launch(context, Uri(scheme: 'tel', path: phone)), icon: const Icon(Icons.call), label: const Text('전화하기'))),
            if (phone.isNotEmpty && (mapLink.isNotEmpty || address.isNotEmpty)) const SizedBox(width: 10),
            if (mapLink.isNotEmpty || address.isNotEmpty) Expanded(child: OutlinedButton.icon(onPressed: () => _launch(context, usableMapUri), icon: const Icon(Icons.map_outlined), label: const Text('지도 보기'))),
          ]),
        if (infoPending)
          const InfoCard(text: '이 업체는 협력업체 목록에서 확인했지만 지역·연락처·카페 게시글은 아직 확인되지 않았습니다. 확인 전 정보는 표시하지 않습니다.'),
        else if (phone.isEmpty && mapLink.isEmpty && address.isEmpty)
          const InfoCard(text: '업체 연락처와 위치는 실제 정보를 등록한 뒤 표시됩니다.'),
        if (cafeLink.isNotEmpty) ...[
          const SizedBox(height: 8),
          OutlinedButton.icon(onPressed: () => _launch(context, Uri.tryParse(cafeLink) ?? Uri()), icon: const Icon(Icons.open_in_new), label: const Text('카페에서 더 알아보기')),
        ],
        const SizedBox(height: 24),
        const SectionHeading(title: '진행 중인 혜택', subtitle: '협력업체 프로모션'),
        FutureBuilder<List<Map<String, dynamic>>>(
          future: api.list('offers'),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
            if (snapshot.hasError) return const InfoCard(text: '혜택 정보를 불러오지 못했습니다.');
            final partnerId = partner['id'];
            final offers = (snapshot.data ?? []).where((offer) => offer['partner'] == partnerId).toList();
            if (offers.isEmpty) return const InfoCard(text: '현재 진행 중인 혜택이 없습니다.');
            return Column(children: offers.map((offer) => Card(child: ListTile(
              leading: const Icon(Icons.local_offer_outlined),
              title: Text((offer['title'] ?? '').toString(), style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Text([
                if ((offer['description'] ?? '').toString().isNotEmpty) offer['description'].toString(),
                if ((offer['redemption_instructions'] ?? '').toString().isNotEmpty) '이용 방법: ${offer['redemption_instructions']}',
              ].join('\n')),
            ))).toList());
          },
        ),
      ]),
    );
  }
}

class _SponsoredBadge extends StatelessWidget {
  const _SponsoredBadge();
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
    decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer, borderRadius: BorderRadius.circular(20)),
    child: Text('제휴', style: TextStyle(color: Theme.of(context).colorScheme.onPrimaryContainer, fontSize: 11, fontWeight: FontWeight.w900)),
  );
}

class _NewBadge extends StatelessWidget {
  const _NewBadge();
  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(right: 6),
    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
    decoration: BoxDecoration(color: const Color(0xFFFF4E55), borderRadius: BorderRadius.circular(20)),
    child: const Text('N', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w900)),
  );
}

class GaragePage extends StatefulWidget {
  const GaragePage({required this.api, required this.signedIn, required this.onLogin, super.key});
  final ApiClient api;
  final bool signedIn;
  final VoidCallback onLogin;
  @override
  State<GaragePage> createState() => _GaragePageState();
}

class _GaragePageState extends State<GaragePage> {
  late Future<List<Map<String, dynamic>>> vehiclesFuture;
  int? selectedVehicleId;
  String ledgerFilter = '전체';
  int ledgerRevision = 0;
  int reminderRevision = 0;
  final Map<int, Future<Map<String, dynamic>>> maintenanceSummaryFutures = {};

  @override
  void initState() {
    super.initState();
    vehiclesFuture = widget.api.list('vehicles');
  }

  void reloadVehicles() => setState(() {
    vehiclesFuture = widget.api.list('vehicles');
    maintenanceSummaryFutures.clear();
  });

  Future<Map<String, dynamic>> maintenanceSummary(int vehicleId) =>
      maintenanceSummaryFutures.putIfAbsent(vehicleId, () => widget.api.getVehicleMaintenanceSummary(vehicleId));

  void refreshMaintenanceSummary(int vehicleId) {
    maintenanceSummaryFutures[vehicleId] = widget.api.getVehicleMaintenanceSummary(vehicleId);
  }

  Future<void> showVehicleQr(Map<String, dynamic> vehicle) async {
    await showVehiclePassportQr(context, vehicle);
  }

  Future<void> issueTransferCode(int vehicleId) async {
    try {
      final transfer = await widget.api.createVehicleTransferCode(vehicleId);
      if (!mounted) return;
      final code = transfer['code'].toString();
      final expires = transfer['expires_at'].toString().replaceFirst('T', ' ').split('.').first;
      await showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
        title: const Text('차량 인계 코드'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(transfer['model_name']?.toString() ?? '등록 차량', style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
          SelectableText(code, style: const TextStyle(fontSize: 30, letterSpacing: 4, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          Text('만료: $expires'),
          const SizedBox(height: 12),
          Text('구매자가 코드를 확인하고 승인하면 차계부 ${transfer['ledger_count']}건(업체 인증 ${transfer['verified_record_count']}건 · 정정 ${transfer['correction_count']}건)과 정비 알림 ${transfer['reminder_count']}건이 함께 전달됩니다. 완료 후 판매자 계정에서는 차량이 사라집니다.', style: const TextStyle(height: 1.45)),
          const SizedBox(height: 8),
          const Text('코드는 구매자에게만 전달해 주세요.', style: TextStyle(fontWeight: FontWeight.w800)),
        ]),
        actions: [
          TextButton.icon(
            onPressed: () async {
              try {
                await widget.api.cancelVehicleTransfer(vehicleId);
                if (dialogContext.mounted) Navigator.pop(dialogContext);
                if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('인계 코드를 취소했습니다.')));
              } catch (_) {
                if (dialogContext.mounted) ScaffoldMessenger.of(dialogContext).showSnackBar(const SnackBar(content: Text('코드를 취소하지 못했습니다. 차량 상태를 새로고침해 주세요.')));
              }
            },
            icon: const Icon(Icons.cancel_outlined), label: const Text('코드 취소'),
          ),
          TextButton.icon(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: code));
              if (dialogContext.mounted) ScaffoldMessenger.of(dialogContext).showSnackBar(const SnackBar(content: Text('인계 코드를 복사했습니다.')));
            },
            icon: const Icon(Icons.copy), label: const Text('코드 복사'),
          ),
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('닫기')),
        ],
      ));
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('인계 코드를 만들지 못했습니다. $error')));
    }
  }

  Future<void> acceptVehicleTransfer() async {
    final codeController = TextEditingController();
    String? inputError;
    final result = await showDialog<Map<String, dynamic>>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setDialogState) => AlertDialog(
      title: const Text('구매한 차량 인계받기'),
      content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('판매자가 전달한 10자리 코드를 입력하세요.'),
        const SizedBox(height: 12),
        TextField(controller: codeController, textCapitalization: TextCapitalization.characters, maxLength: 10, decoration: const InputDecoration(labelText: '인계 코드', counterText: '')),
        if (inputError != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(inputError!, style: const TextStyle(color: Colors.red))),
      ]),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('취소')),
        FilledButton(onPressed: () async {
          if (codeController.text.trim().length != 10) {
            setDialogState(() => inputError = '10자리 인계 코드를 입력해 주세요.');
            return;
          }
          try {
            final preview = await widget.api.previewVehicleTransfer(codeController.text);
            if (dialogContext.mounted) Navigator.pop(dialogContext, {'code': codeController.text.trim().toUpperCase(), 'preview': preview});
          } catch (_) {
            if (dialogContext.mounted) setDialogState(() => inputError = '코드를 확인하지 못했습니다. 만료 여부를 확인해 주세요.');
          }
        }, child: const Text('차량 정보 확인')),
      ],
    )));
    codeController.dispose();
    if (result == null || !mounted) return;
    final preview = result['preview'] as Map<String, dynamic>;
    final year = preview['model_year'] == null ? '' : ' · ${preview['model_year']}년식';
    final generation = (preview['generation'] ?? '').toString().trim();
    final odometer = preview['current_odometer_km'] == null ? '미등록' : '${preview['current_odometer_km']} km';
    final accepted = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('차량과 기록을 인계받을까요?'),
      content: Text(
        '${preview['model_name'] ?? 'MINI'}$year${generation.isEmpty ? '' : ' · $generation'}\n'
        '현재 주행거리: $odometer\n'
        '차계부 ${preview['ledger_count']}건 · 업체 인증 ${preview['verified_record_count']}건 · 정정 이력 ${preview['correction_count']}건\n'
        '정비 알림 ${preview['reminder_count']}건\n\n'
        '승인하면 금액을 포함한 차계부 내역과 정비 알림이 내 계정으로 이동합니다. 이전 소유자는 이 차량을 더 이상 볼 수 없습니다. 앱은 실제 차량 소유권을 확인하지 않으니 판매자와 차량 정보를 확인한 뒤 승인하세요.',
        style: const TextStyle(height: 1.5),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('취소')),
        FilledButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('인계 승인')),
      ],
    ));
    if (accepted != true) return;
    try {
      final transferred = await widget.api.acceptVehicleTransfer(result['code'].toString());
      final vehicle = transferred['vehicle'] as Map<String, dynamic>;
      if (!mounted) return;
      setState(() {
        selectedVehicleId = vehicle['id'] as int;
        vehiclesFuture = widget.api.list('vehicles');
      });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('차량과 차계부 기록을 인계받았습니다.')));
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('차량 인계를 완료하지 못했습니다. $error')));
    }
  }

  Future<void> addVehicle() async {
    final formKey = GlobalKey<FormState>();
    final model = TextEditingController();
    final nickname = TextEditingController();
    final generation = TextEditingController();
    final year = TextEditingController();
    final odometer = TextEditingController();
    String? error;
    final created = await showDialog<bool>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setDialogState) => AlertDialog(
      title: const Text('내 차량 등록'),
      content: SizedBox(width: 420, child: SingleChildScrollView(child: Form(key: formKey, child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextFormField(controller: model, decoration: const InputDecoration(labelText: '차종 *', hintText: '예: MINI Cooper S, Mercedes-Maybach S 580'), validator: (v) => (v == null || v.trim().isEmpty) ? '차종을 입력해 주세요.' : null),
        TextFormField(controller: nickname, decoration: const InputDecoration(labelText: '별명 (선택)'),),
        TextFormField(controller: generation, decoration: const InputDecoration(labelText: '세대 (선택)'),),
        TextFormField(controller: year, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '연식 (선택)'), validator: (v) => (v != null && v.isNotEmpty && int.tryParse(v) == null) ? '연식은 숫자로 입력해 주세요.' : null),
        TextFormField(controller: odometer, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '현재 주행거리 km (선택)'), validator: (v) => (v != null && v.isNotEmpty && int.tryParse(v) == null) ? '주행거리는 숫자로 입력해 주세요.' : null),
        if (error != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(error!, style: const TextStyle(color: Colors.red))),
      ])))),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('취소')), FilledButton(onPressed: () async {
        if (!formKey.currentState!.validate()) return;
        try {
          await widget.api.create('vehicles', {
            'model_name': model.text.trim(), 'nickname': nickname.text.trim(), 'generation': generation.text.trim(),
            'model_year': year.text.isEmpty ? null : int.parse(year.text),
            'current_odometer_km': odometer.text.isEmpty ? null : int.parse(odometer.text),
          });
          if (dialogContext.mounted) Navigator.pop(dialogContext, true);
        } catch (e) { setDialogState(() => error = e.toString()); }
      }, child: const Text('등록'))],
    )));
    model.dispose(); nickname.dispose(); generation.dispose(); year.dispose(); odometer.dispose();
    if (created == true && mounted) reloadVehicles();
  }

  Future<void> addLedgerEntry(int vehicleId) async {
    final formKey = GlobalKey<FormState>();
    final description = TextEditingController();
    final amount = TextEditingController();
    final odometer = TextEditingController();
    String kind = 'fuel';
    String? error;
    final created = await showDialog<bool>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setDialogState) => AlertDialog(
      title: const Text('차계부 기록 추가'),
      content: SizedBox(width: 420, child: SingleChildScrollView(child: Form(key: formKey, child: Column(mainAxisSize: MainAxisSize.min, children: [
        DropdownButtonFormField<String>(value: kind, decoration: const InputDecoration(labelText: '기록 종류'), items: const [
          DropdownMenuItem(value: 'fuel', child: Text('주유')), DropdownMenuItem(value: 'service', child: Text('정비')),
          DropdownMenuItem(value: 'part', child: Text('소모품')), DropdownMenuItem(value: 'wash', child: Text('세차')),
          DropdownMenuItem(value: 'other', child: Text('기타')),
        ], onChanged: (v) => setDialogState(() => kind = v ?? 'fuel')),
        TextFormField(controller: description, decoration: const InputDecoration(labelText: '내용', hintText: '예: 엔진오일 교환'), validator: (v) => (v == null || v.trim().isEmpty) ? '기록 내용을 입력해 주세요.' : null),
        TextFormField(controller: amount, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '금액 원'), validator: (v) => (v == null || int.tryParse(v) == null || int.parse(v) < 0) ? '금액을 숫자로 입력해 주세요.' : null),
        TextFormField(controller: odometer, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '주행거리 km (선택)'), validator: (v) => (v != null && v.isNotEmpty && int.tryParse(v) == null) ? '주행거리는 숫자로 입력해 주세요.' : null),
        if (error != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(error!, style: const TextStyle(color: Colors.red))),
      ])))),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('취소')), FilledButton(onPressed: () async {
        if (!formKey.currentState!.validate()) return;
        try {
          await widget.api.create('ledger', {
            'vehicle': vehicleId, 'kind': kind, 'entry_date': DateTime.now().toIso8601String().substring(0, 10),
            'description': description.text.trim(), 'amount_krw': int.parse(amount.text),
            'odometer_km': odometer.text.isEmpty ? null : int.parse(odometer.text),
          });
          if (dialogContext.mounted) Navigator.pop(dialogContext, true);
        } catch (e) { setDialogState(() => error = e.toString()); }
      }, child: const Text('저장'))],
    )));
    description.dispose(); amount.dispose(); odometer.dispose();
    if (created == true && mounted) setState(() {
      ledgerRevision++;
      refreshMaintenanceSummary(vehicleId);
    });
  }

  Future<void> addReminder(int vehicleId) async {
    final formKey = GlobalKey<FormState>();
    final title = TextEditingController();
    final odometer = TextEditingController();
    DateTime? dueDate;
    String? error;
    final created = await showDialog<bool>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setDialogState) => AlertDialog(
      title: const Text('정비 알림 추가'),
      content: SizedBox(width: 420, child: SingleChildScrollView(child: Form(key: formKey, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        TextFormField(controller: title, decoration: const InputDecoration(labelText: '알림 내용', hintText: '예: 엔진오일 교환'), validator: (v) => (v == null || v.trim().isEmpty) ? '알림 내용을 입력해 주세요.' : null),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () async {
            final picked = await showDatePicker(context: dialogContext, initialDate: dueDate ?? DateTime.now().add(const Duration(days: 30)), firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 3650)));
            if (picked != null) setDialogState(() => dueDate = picked);
          },
          icon: const Icon(Icons.calendar_month_outlined),
          label: Text(dueDate == null ? '날짜 알림 설정 (선택)' : '날짜: ${dueDate!.toIso8601String().substring(0, 10)}'),
        ),
        TextFormField(controller: odometer, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '주행거리 알림 km (선택)', hintText: '예: 85000'), validator: (v) => (v != null && v.isNotEmpty && (int.tryParse(v) == null || int.parse(v) < 0)) ? '주행거리를 숫자로 입력해 주세요.' : null),
        if (error != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(error!, style: const TextStyle(color: Colors.red))),
      ])))),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('취소')), FilledButton(onPressed: () async {
        if (!formKey.currentState!.validate()) return;
        if (dueDate == null && odometer.text.trim().isEmpty) {
          setDialogState(() => error = '날짜 또는 주행거리 중 하나는 설정해 주세요.');
          return;
        }
        try {
          await widget.api.create('reminders', {
            'vehicle': vehicleId,
            'title': title.text.trim(),
            'due_date': dueDate?.toIso8601String().substring(0, 10),
            'due_odometer_km': odometer.text.trim().isEmpty ? null : int.parse(odometer.text.trim()),
          });
          if (dialogContext.mounted) Navigator.pop(dialogContext, true);
        } catch (e) { setDialogState(() => error = e.toString()); }
      }, child: const Text('알림 저장'))],
    )));
    title.dispose();
    odometer.dispose();
    if (created == true && mounted) setState(() {
      reminderRevision++;
      refreshMaintenanceSummary(vehicleId);
    });
  }

  Future<void> completeReminder(int reminderId, int vehicleId) async {
    try {
      await widget.api.completeReminder(reminderId);
      if (mounted) setState(() {
        reminderRevision++;
        refreshMaintenanceSummary(vehicleId);
      });
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('알림을 완료 처리하지 못했습니다. 다시 시도해 주세요.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.signedIn) return ListView(padding: const EdgeInsets.all(20), children: [
      const Text('내 차량', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
      const SizedBox(height: 16), const InfoCard(text: '로그인 후 내 차량과 차계부를 사용할 수 있어요.'),
      const SizedBox(height: 12), FilledButton(onPressed: widget.onLogin, child: const Text('네이버로 로그인')),
    ]);
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: vehiclesFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return ListView(padding: const EdgeInsets.all(20), children: [
          const Text('내 차량', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 16), const InfoCard(text: '차량을 불러오지 못했습니다.'),
          FilledButton(onPressed: reloadVehicles, child: const Text('다시 불러오기')),
        ]);
        final vehicles = snapshot.data ?? [];
        if (vehicles.isEmpty) return ListView(padding: const EdgeInsets.all(20), children: [
          const Text('내 차량', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 16), const InfoCard(text: '내 차를 등록하고 주유·정비 기록을 모아보세요.'),
          const SizedBox(height: 12), FilledButton.icon(onPressed: addVehicle, icon: const Icon(Icons.add), label: const Text('차량 등록')),
          if (!ApiClient.demoMode) ...[
            const SizedBox(height: 8),
            OutlinedButton.icon(onPressed: acceptVehicleTransfer, icon: const Icon(Icons.swap_horiz), label: const Text('구매한 차량 인계 코드 입력')),
          ],
        ]);
        final matchingVehicles = vehicles.where((v) => v['id'] == selectedVehicleId).toList();
        final vehicle = matchingVehicles.isNotEmpty ? matchingVehicles.first : vehicles.first;
        final vehicleId = vehicle['id'] as int;
        return ListView(padding: const EdgeInsets.all(20), children: [
          Row(children: [
            const Expanded(child: Text('내 차량', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900))),
            IconButton(onPressed: reloadVehicles, tooltip: '차량 새로고침', icon: const Icon(Icons.refresh)),
            IconButton(onPressed: addVehicle, tooltip: '차량 추가', icon: const Icon(Icons.add_circle_outline)),
          ]),
          if (vehicles.length > 1) ...[
            const SizedBox(height: 8),
            GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
              childAspectRatio: 2.65,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: vehicles.asMap().entries.map((entry) {
                final item = entry.value;
                final id = item['id'] as int;
                final name = (item['nickname']?.toString().trim().isNotEmpty ?? false) ? item['nickname'].toString() : item['model_name'].toString();
                final selected = id == vehicleId;
                final colors = Theme.of(context).colorScheme;
                return Material(
                  color: selected ? colors.primary : colors.surface,
                  borderRadius: BorderRadius.circular(13),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(13),
                    onTap: () => setState(() { selectedVehicleId = id; ledgerFilter = '전체'; }),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
                      decoration: BoxDecoration(borderRadius: BorderRadius.circular(13), border: Border.all(color: selected ? colors.primary : colors.outlineVariant)),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
                        Text('차량 ${entry.key + 1}', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: selected ? colors.onPrimary.withOpacity(.8) : colors.onSurfaceVariant)),
                        const SizedBox(height: 3),
                        Text(name, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 12, height: 1.2, fontWeight: FontWeight.w800, color: selected ? colors.onPrimary : colors.onSurface)),
                      ]),
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 10),
          Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(vehicle['nickname']?.toString().trim().isNotEmpty == true ? vehicle['nickname'].toString() : vehicle['model_name'].toString(), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900))),
              IconButton(onPressed: () => showVehicleQr(vehicle), tooltip: '차량 QR', icon: const Icon(Icons.qr_code_2)),
            ]),
            if (hasFavouredF66Photo(vehicle) || hasMaybachPhoto(vehicle)) VehiclePhoto(vehicle: vehicle, height: 132),
            Text([
              if (vehicle['generation'] != null) vehicle['generation'],
              if (vehicle['model_year'] != null) '${vehicle['model_year']}년형',
              '현재 ${vehicle['current_odometer_km'] == null ? '주행거리 미등록' : '${formatKilometers(vehicle['current_odometer_km'])} km'}',
            ].join(' · '), style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
            if (vehicle['sample_data'] == true) const Padding(padding: EdgeInsets.only(top: 5), child: Text('주행거리는 시제품 예시입니다.', style: TextStyle(fontSize: 11))),
          ]))),
          const SizedBox(height: 12),
          FutureBuilder<Map<String, dynamic>>(
            key: ValueKey('maintenance-summary-$vehicleId'),
            future: maintenanceSummary(vehicleId),
            builder: (context, summary) {
              if (summary.connectionState == ConnectionState.waiting) return const SizedBox(height: 4);
              if (summary.hasError || summary.data == null) return const InfoCard(text: '정비 요약을 불러오지 못했습니다. 새로고침을 눌러 다시 확인해 주세요.');
              final data = summary.data!;
              final last = data['last_maintenance'] as Map<String, dynamic>?;
              final dueDate = data['next_due_date']?.toString();
              final dueKm = data['next_due_odometer_km']?.toString();
              final overdue = (data['overdue_reminder_count'] as num?)?.toInt() ?? 0;
              final nextManagementItems = [
                if (dueDate != null) dueDate,
                if (dueKm != null) '$dueKm km',
              ];
              return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  const Expanded(child: Text('정비 이력 요약', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900))),
                  if (overdue > 0) Chip(avatar: const Icon(Icons.warning_amber_rounded, size: 16), label: Text('기한 경과 $overdue건')),
                ]),
                Wrap(spacing: 8, runSpacing: 4, children: [
                  Chip(label: Text('업체 인증 ${data['verified_record_count']}건')),
                  Chip(label: Text('정정 이력 ${data['correction_count']}건')),
                  Chip(label: Text('예정 알림 ${data['pending_reminder_count']}건')),
                ]),
                const Divider(),
                Text(last == null
                    ? '등록된 정비·소모품 기록이 없습니다.'
                    : '최근 정비  ${last['entry_date']} · ${last['description']?.toString().isNotEmpty == true ? last['description'] : last['kind']} · ${last['odometer_km'] ?? '주행거리 미입력'} km',
                    style: const TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                Text('다음 관리  ${nextManagementItems.isEmpty ? '일정 미등록' : nextManagementItems.join(' · ')}', style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
              ])));
            },
          ),
          if (!ApiClient.demoMode) ...[
            const SizedBox(height: 8),
            Wrap(spacing: 8, runSpacing: 8, children: [
              OutlinedButton.icon(onPressed: () => issueTransferCode(vehicleId), icon: const Icon(Icons.share_outlined), label: const Text('판매 차량 인계')),
              OutlinedButton.icon(onPressed: acceptVehicleTransfer, icon: const Icon(Icons.swap_horiz), label: const Text('구매 차량 인계')),
            ]),
          ],
          const SizedBox(height: 20),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('차계부', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)), TextButton.icon(onPressed: () => addLedgerEntry(vehicleId), icon: const Icon(Icons.add), label: const Text('기록 추가'))]),
          FutureBuilder<List<Map<String, dynamic>>>(key: ValueKey('ledger-$vehicleId-$ledgerRevision'), future: widget.api.list('ledger?vehicle=$vehicleId'), builder: (context, records) {
            if (records.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
            if (records.hasError) return const InfoCard(text: '차계부를 불러오지 못했습니다.');
            final allRecords = records.data ?? [];
            final now = DateTime.now();
            final monthRecords = allRecords.where((entry) {
              final date = DateTime.tryParse((entry['entry_date'] ?? '').toString());
              return date != null && date.year == now.year && date.month == now.month;
            }).toList();
            int amountFor(Set<String> kinds) => monthRecords.where((entry) => kinds.contains('${entry['kind']}'))
                .fold<int>(0, (total, entry) => total + ((entry['amount_krw'] as num?)?.toInt() ?? 0));
            final monthlyTotal = amountFor({'fuel', 'service', 'part', 'wash', 'other'});
            final visibleRecords = ledgerFilter == '전체' ? allRecords : allRecords.where((entry) {
              final kind = switch ('${entry['kind']}') {
                'fuel' => '주유', 'service' => '정비', 'part' => '소모품', 'wash' => '세차', _ => '기타',
              };
              return kind == ledgerFilter;
            }).toList();
            return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${now.month}월 차량 지출', style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
                const SizedBox(height: 3),
                Text('₩${monthlyTotal.toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',')}', style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900)),
                const SizedBox(height: 12),
                Wrap(spacing: 7, runSpacing: 7, children: [
                  Chip(label: Text('주유 ₩${amountFor({'fuel'}).toString()}')),
                  Chip(label: Text('정비 ₩${amountFor({'service'}).toString()}')),
                  Chip(label: Text('소모품 ₩${amountFor({'part'}).toString()}')),
                  Chip(label: Text('${monthRecords.length}건 기록')),
                ]),
              ]))),
              const SizedBox(height: 12),
              SingleChildScrollView(scrollDirection: Axis.horizontal, child: Row(children: ['전체', '주유', '정비', '소모품', '세차', '기타'].map((label) => Padding(
                padding: const EdgeInsets.only(right: 7), child: ChoiceChip(label: Text(label), selected: ledgerFilter == label,
                  onSelected: (_) => setState(() => ledgerFilter = label)),
              )).toList())),
              if (visibleRecords.isEmpty) InfoCard(text: allRecords.isEmpty ? '아직 기록이 없습니다. 주유나 정비 기록을 추가해 보세요.' : '이 종류로 기록한 내역이 없습니다.')
              else ...visibleRecords.map((entry) {
              final verified = entry['source'] == 'partner';
              final integrityValid = entry['integrity_valid'] != false;
              final partnerName = (entry['partner_name'] ?? '').toString();
              final partNumber = (entry['part_number'] ?? '').toString();
              final detail = [
                '기록 #${entry['id']}',
                '${entry['entry_date']} · ${entry['odometer_km'] ?? '주행거리 미입력'} km',
                if (verified && partnerName.isNotEmpty) partnerName,
                if (entry['corrects'] != null) '정정 기록 #${entry['corrects']} · ${entry['correction_reason'] ?? ''}',
                if (entry['is_corrected'] == true) '정정된 기록 · 아래 정정 이력 확인',
                if (partNumber.isNotEmpty) '부품번호 $partNumber',
                if ((entry['evidence_url'] ?? '').toString().isNotEmpty) '증빙 등록',
              ].join('\n');
              return Card(child: ListTile(
                leading: verified ? Icon(integrityValid ? Icons.verified : Icons.gpp_bad_outlined, color: integrityValid ? Colors.green : Colors.red) : const Icon(Icons.edit_note),
                title: Row(children: [
                  Expanded(child: Text(entry['description']?.toString().isNotEmpty == true ? entry['description'] : entry['kind'])),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(color: verified && integrityValid ? const Color.fromARGB(45, 76, 175, 80) : Theme.of(context).colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(12)),
                    child: Text(integrityValid ? (entry['trust_label'] ?? '차주 입력').toString() : '검증 이상', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800)),
                  ),
                ]),
                subtitle: Text(detail),
                trailing: Text(entry['details_redacted'] == true ? '이전 이력' : '₩${entry['amount_krw']}'),
              ));
              }),
            ]);
          }),
          const SizedBox(height: 20),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('정비 알림', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)), TextButton.icon(onPressed: () => addReminder(vehicleId), icon: const Icon(Icons.add), label: const Text('알림 추가'))]),
          FutureBuilder<List<Map<String, dynamic>>>(key: ValueKey('reminders-$vehicleId-$reminderRevision'), future: widget.api.list('reminders?vehicle=$vehicleId'), builder: (context, reminders) {
            if (reminders.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
            if (reminders.hasError) return const InfoCard(text: '정비 알림을 불러오지 못했습니다.');
            final rows = reminders.data ?? [];
            if (rows.isEmpty) return const InfoCard(text: '엔진오일, 검사 일정 등을 알림으로 등록해 보세요.');
            return Column(children: rows.map((reminder) {
              final complete = reminder['is_complete'] == true;
              final date = reminder['due_date']?.toString();
              final km = reminder['due_odometer_km'];
              final due = date != null ? DateTime.tryParse(date) : null;
              final today = DateTime.now();
              final overdue = !complete && due != null && DateTime(due.year, due.month, due.day).isBefore(DateTime(today.year, today.month, today.day));
              final details = [if (date != null) date, if (km != null) '$km km'].join(' · ');
              return Card(child: ListTile(
                leading: Icon(complete ? Icons.check_circle : (overdue ? Icons.warning_amber_rounded : Icons.notifications_active_outlined), color: complete ? Colors.green : (overdue ? Colors.deepOrange : null)),
                title: Text(reminder['title']?.toString() ?? '정비 알림', style: TextStyle(fontWeight: FontWeight.w800, decoration: complete ? TextDecoration.lineThrough : null)),
                subtitle: Text('${details.isEmpty ? '일정 미설정' : details}${overdue ? ' · 예정일 지남' : ''}'),
                trailing: complete ? const Text('완료') : IconButton(tooltip: '완료 처리', onPressed: () => completeReminder(reminder['id'] as int, vehicleId), icon: const Icon(Icons.check_circle_outline)),
              ));
            }).toList());
          }),
          const SizedBox(height: 20),
          FilledButton.icon(onPressed: () => addLedgerEntry(vehicleId), icon: const Icon(Icons.add), label: const Text('차계부 기록 추가')),
          const SizedBox(height: 8),
          OutlinedButton.icon(onPressed: () => addReminder(vehicleId), icon: const Icon(Icons.notifications_active_outlined), label: const Text('정비 알림 추가')),
        ]);
      },
    );
  }
}

class AccountPage extends StatelessWidget {
  const AccountPage({required this.api, required this.signedIn, required this.pushEnabled, required this.onPushChanged, required this.onLogin, required this.onLogout, required this.onManageVehicles, super.key});
  final ApiClient api;
  final bool signedIn;
  final bool pushEnabled;
  final ValueChanged<bool> onPushChanged;
  final VoidCallback onLogin;
  final VoidCallback onLogout;
  final VoidCallback onManageVehicles;
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(20), children: [
    const Text('나의 차고', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
    const SizedBox(height: 16),
    InfoCard(text: ApiClient.demoMode
        ? '데모 계정으로 체험 중입니다. 차계부와 알림 변경 사항은 앱을 종료하면 초기화됩니다.'
        : signedIn ? '로그인되어 있습니다. 정비 예정일과 목표 주행거리 알림을 관리할 수 있어요.' : '로그인해 차량을 등록하고 기록을 관리하세요.'),
    const SizedBox(height: 20),
    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      const Text('내 차량', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
      TextButton.icon(onPressed: onManageVehicles, icon: const Icon(Icons.add), label: const Text('차량 추가')),
    ]),
    if (!signedIn && !ApiClient.demoMode)
      const InfoCard(text: '로그인 후 MINI와 다른 차종을 함께 등록할 수 있어요.')
    else
      FutureBuilder<List<Map<String, dynamic>>>(future: api.list('vehicles'), builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const LinearProgressIndicator();
        if (snapshot.hasError) return const InfoCard(text: '차량 목록을 불러오지 못했습니다.');
        final vehicles = snapshot.data ?? [];
        if (vehicles.isEmpty) return const InfoCard(text: '등록된 차량이 없습니다. 차량을 추가해 주세요.');
        return Column(children: vehicles.map((vehicle) {
          final name = (vehicle['nickname']?.toString().trim().isNotEmpty ?? false)
              ? vehicle['nickname'].toString() : (vehicle['model_name'] ?? '등록 차량').toString();
          final details = [
            if (vehicle['generation'] != null && vehicle['generation'].toString().isNotEmpty) vehicle['generation'],
            if (vehicle['model_year'] != null) '${vehicle['model_year']}년형',
            if (vehicle['current_odometer_km'] != null) '${formatKilometers(vehicle['current_odometer_km'])} km',
          ].join(' · ');
          return Card(child: InkWell(borderRadius: BorderRadius.circular(14), onTap: onManageVehicles, child: Padding(
            padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [Expanded(child: Text(name, style: const TextStyle(fontWeight: FontWeight.w800))), const Icon(Icons.chevron_right)]),
              if (hasFavouredF66Photo(vehicle) || hasMaybachPhoto(vehicle)) VehiclePhoto(vehicle: vehicle, height: 104),
              if (details.isNotEmpty) Text(details, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
              if (vehicle['sample_data'] == true) const Padding(padding: EdgeInsets.only(top: 5), child: Text('시제품 예시 차량', style: TextStyle(fontSize: 11))),
            ]),
          )));
        }).toList());
      }),
    const SizedBox(height: 12),
    OutlinedButton.icon(onPressed: onManageVehicles, icon: const Icon(Icons.directions_car_outlined), label: const Text('차량 관리 및 차계부 열기')),
    const SizedBox(height: 8),
    OutlinedButton.icon(onPressed: () => _openCafeNotice(context, iloveMiniWebsiteUrl), icon: const Icon(Icons.open_in_new), label: const Text('네이버 카페 바로가기')),
    const SizedBox(height: 8),
    OutlinedButton.icon(
      onPressed: () => _openCafeNotice(context, partnerInquiryUrl),
      icon: const Icon(Icons.storefront_outlined),
      label: const Text('협력업체 입점 문의'),
    ),
    const SizedBox(height: 8),
    OutlinedButton.icon(onPressed: () => showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('이용약관 · 개인정보 안내'),
      content: const SingleChildScrollView(child: Text('이용약관 (안)\n아이러브미니는 차량 관리, 차계부, 정비 알림, 협력업체 정보 및 커뮤니티 연결 기능을 제공합니다. 이용자는 본인의 차량 및 정비 정보를 정확하게 입력하고 계정 보안을 관리해야 합니다. 업체 정보·가격·혜택은 변경될 수 있으므로 이용 전 업체에 확인해 주세요. 정비 계약 및 작업 결과는 이용자와 해당 업체 사이의 책임입니다.\n\n개인정보 처리 안내 (안)\n서비스 제공 과정에서 계정 식별·로그인 정보, 이용자가 입력한 차량·주행거리·정비 기록·사진·문의 내용, 알림 설정 및 이용 기록을 처리할 수 있습니다. 이용 목적은 회원 확인, 차량 이력 관리, 문의 응대, 선택한 알림 제공, 보안과 서비스 개선입니다. 목적 달성 후 관련 법령상 보존 의무가 있는 경우를 제외하고 파기합니다. 이용자는 본인 정보의 열람·정정·삭제·처리정지를 요청할 수 있습니다.\n\n시제품용 초안입니다. 운영 주체, 실제 데이터 흐름·보관 기간·수탁업체 및 연락처를 정식 출시 전에 확정해 고지해야 합니다.'),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('닫기'))],
    )), icon: const Icon(Icons.description_outlined), label: const Text('이용약관 · 개인정보 안내')),
    if (signedIn && !ApiClient.demoMode) SwitchListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 14),
      value: pushEnabled,
      onChanged: onPushChanged,
      title: const Text('정비 푸시 알림'),
      subtitle: const Text('설정한 날짜 또는 주행거리에 도달하면 알림을 받아요.'),
      secondary: const Icon(Icons.notifications_active_outlined),
    ),
    if (signedIn && !ApiClient.demoMode) ...[
      const SizedBox(height: 8),
      OutlinedButton.icon(
        onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => PartnerRecordPage(api: api))),
        icon: const Icon(Icons.verified_outlined),
        label: const Text('협력업체 정비 인증기록 등록'),
      ),
    ],
    const SizedBox(height: 12),
    if (!ApiClient.demoMode)
      FilledButton(onPressed: signedIn ? onLogout : onLogin, child: Text(signedIn ? '로그아웃' : '로그인 / 가입')),
  ]);
}

class PartnerRecordPage extends StatefulWidget {
  const PartnerRecordPage({required this.api, super.key});
  final ApiClient api;
  @override
  State<PartnerRecordPage> createState() => _PartnerRecordPageState();
}

class _PartnerRecordPageState extends State<PartnerRecordPage> {
  final formKey = GlobalKey<FormState>();
  final vehiclePublicId = TextEditingController();
  final description = TextEditingController();
  final odometer = TextEditingController();
  final amount = TextEditingController(text: '0');
  final partNumber = TextEditingController();
  final evidenceUrl = TextEditingController();
  final corrects = TextEditingController();
  final correctionReason = TextEditingController();
  late Future<List<Map<String, dynamic>>> workplaces;
  int? partnerId;
  String kind = 'service';
  bool busy = false;
  String? error;

  Future<void> scanVehicle() async {
    final scanned = await Navigator.of(context).push<String>(MaterialPageRoute(builder: (_) => const ScanVehicleQrPage()));
    if (scanned != null && mounted) setState(() => vehiclePublicId.text = scanned);
  }

  @override
  void initState() {
    super.initState();
    workplaces = widget.api.list('partners/my-workplaces');
  }

  Future<void> submit() async {
    if (!formKey.currentState!.validate() || partnerId == null) {
      setState(() => error = partnerId == null ? '인증 권한이 있는 협력업체를 선택해 주세요.' : null);
      return;
    }
    setState(() { busy = true; error = null; });
    try {
      await widget.api.createPartnerVerifiedRecord({
        'vehicle_public_id': vehiclePublicId.text.trim(),
        'partner': partnerId,
        'kind': kind,
        'entry_date': DateTime.now().toIso8601String().substring(0, 10),
        'odometer_km': int.parse(odometer.text),
        'amount_krw': int.parse(amount.text),
        'description': description.text.trim(),
        'part_number': partNumber.text.trim(),
        'evidence_url': evidenceUrl.text.trim(),
        if (corrects.text.trim().isNotEmpty) 'corrects': int.parse(corrects.text.trim()),
        if (corrects.text.trim().isNotEmpty) 'correction_reason': correctionReason.text.trim(),
      });
      if (!mounted) return;
      await showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
        title: const Text('업체 인증기록 등록 완료'),
        content: const Text('차량 차계부에 협력업체 인증 배지와 함께 기록되었습니다. 등록된 원본은 수정하거나 삭제할 수 없습니다.'),
        actions: [FilledButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('확인'))],
      ));
      if (mounted) Navigator.pop(context, true);
    } catch (_) {
      if (mounted) setState(() => error = '등록하지 못했습니다. 차량 QR과 협력업체 권한, 입력 내용을 확인해 주세요.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('협력업체 정비 등록')),
    body: FutureBuilder<List<Map<String, dynamic>>>(
      future: workplaces,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('협력업체 권한을 확인하지 못했습니다.')));
        final partners = snapshot.data ?? [];
        if (partners.isEmpty) return const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('운영자에게 협력업체 담당자 권한을 승인받은 계정만 인증기록을 등록할 수 있습니다.', textAlign: TextAlign.center)));
        partnerId ??= partners.first['id'] as int;
        return Form(key: formKey, child: ListView(padding: const EdgeInsets.all(20), children: [
          const InfoCard(text: '아이러브미니가 승인한 협력업체 담당자는 차주 승인코드 없이 정비이력을 직접 등록할 수 있습니다. 등록 원본은 수정·삭제되지 않으며, 오류는 원 기록에 연결된 정정이력으로 남깁니다.'),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            value: partnerId,
            decoration: const InputDecoration(labelText: '협력업체'),
            items: partners.map((row) => DropdownMenuItem<int>(value: row['id'] as int, child: Text(row['name'].toString()))).toList(),
            onChanged: (value) => setState(() => partnerId = value),
          ),
          TextFormField(controller: vehiclePublicId, decoration: InputDecoration(labelText: '차량 Passport ID *', suffixIcon: IconButton(tooltip: '차량 QR 스캔', onPressed: scanVehicle, icon: const Icon(Icons.qr_code_scanner))), validator: (value) => value?.trim().isNotEmpty == true ? null : '차량 QR을 스캔해 주세요.'),
          DropdownButtonFormField<String>(value: kind, decoration: const InputDecoration(labelText: '작업 종류'), items: const [
            DropdownMenuItem(value: 'service', child: Text('정비')), DropdownMenuItem(value: 'part', child: Text('소모품')),
            DropdownMenuItem(value: 'wash', child: Text('세차')), DropdownMenuItem(value: 'other', child: Text('기타')),
          ], onChanged: (value) => setState(() => kind = value ?? 'service')),
          TextFormField(controller: description, decoration: const InputDecoration(labelText: '작업내용 *', hintText: '예: 엔진마운트 교환'), validator: (value) => value == null || value.trim().isEmpty ? '작업내용을 입력해 주세요.' : null),
          TextFormField(controller: odometer, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '작업 당시 주행거리 km *'), validator: (value) => int.tryParse(value ?? '') == null ? '주행거리를 숫자로 입력해 주세요.' : null),
          TextFormField(controller: amount, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '결제금액 원 *'), validator: (value) => int.tryParse(value ?? '') == null ? '금액을 숫자로 입력해 주세요.' : null),
          TextFormField(controller: partNumber, decoration: const InputDecoration(labelText: '부품번호 (선택)')),
          TextFormField(controller: corrects, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '정정 대상 기록 번호 (정정 시 입력)'), validator: (value) => value == null || value.trim().isEmpty || int.tryParse(value.trim()) != null ? null : '기록 번호를 숫자로 입력해 주세요.'),
          TextFormField(controller: correctionReason, decoration: const InputDecoration(labelText: '정정 사유 (정정 시 필수)'), validator: (value) => corrects.text.trim().isEmpty || (value?.trim().isNotEmpty ?? false) ? null : '정정 사유를 입력해 주세요.'),
          TextFormField(controller: evidenceUrl, keyboardType: TextInputType.url, decoration: const InputDecoration(labelText: '영수증·작업사진 링크 (선택)'), validator: (value) {
            if (value == null || value.trim().isEmpty) return null;
            final uri = Uri.tryParse(value.trim());
            return uri != null && uri.scheme == 'https' ? null : 'HTTPS 링크를 입력해 주세요.';
          }),
          if (error != null) Padding(padding: const EdgeInsets.only(top: 10), child: Text(error!, style: const TextStyle(color: Colors.red))),
          const SizedBox(height: 18),
          FilledButton.icon(onPressed: busy ? null : submit, icon: const Icon(Icons.verified), label: Text(busy ? '등록 중…' : '업체 인증기록 등록')),
        ]));
      },
    ),
  );

  @override
  void dispose() {
    vehiclePublicId.dispose(); description.dispose(); odometer.dispose(); amount.dispose(); partNumber.dispose(); evidenceUrl.dispose(); corrects.dispose(); correctionReason.dispose();
    super.dispose();
  }
}

class ScanVehicleQrPage extends StatefulWidget {
  const ScanVehicleQrPage({super.key});
  @override
  State<ScanVehicleQrPage> createState() => _ScanVehicleQrPageState();
}

class _ScanVehicleQrPageState extends State<ScanVehicleQrPage> {
  bool handled = false;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('차량 QR 스캔')),
    body: Stack(children: [
      MobileScanner(onDetect: (capture) {
        if (handled) return;
        for (final barcode in capture.barcodes) {
          final raw = barcode.rawValue;
          final uri = raw == null ? null : Uri.tryParse(raw);
          if (uri != null && uri.scheme == 'ilovemini' && uri.host == 'vehicle' && uri.pathSegments.length == 1) {
            handled = true;
            Navigator.of(context).pop(uri.pathSegments.single);
            return;
          }
        }
      }),
      const Positioned(left: 24, right: 24, bottom: 32, child: Card(child: Padding(padding: EdgeInsets.all(14), child: Text('아이러브미니 Vehicle Passport QR을 화면 안에 맞춰 주세요.', textAlign: TextAlign.center)))),
    ]),
  );
}

class LoginPage extends StatefulWidget {
  const LoginPage({required this.api, super.key});
  final ApiClient api;
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final appLinks = AppLinks();
  StreamSubscription<Uri>? subscription;
  bool busy = false;
  bool termsAccepted = false, privacyAccepted = false;
  String? error;
  @override
  void initState() {
    super.initState();
    subscription = appLinks.uriLinkStream.listen(_handleLink);
    appLinks.getInitialLink().then((uri) { if (uri != null) _handleLink(uri); });
  }
  Future<void> _handleLink(Uri uri) async {
    final ticket = uri.queryParameters['ticket'];
    if (uri.scheme != 'ilovemini' || uri.host != 'auth' || ticket == null || !mounted) return;
    setState(() { busy = true; error = null; });
    try {
      await widget.api.completeNaverLogin(ticket, termsAccepted: termsAccepted, privacyAccepted: privacyAccepted);
      if (mounted) Navigator.pop(context, true);
    } catch (e) { if (mounted) setState(() => error = '로그인 확인에 실패했습니다. 다시 시도해 주세요.'); }
    if (mounted) setState(() => busy = false);
  }
  Future<void> _startLogin() async {
    setState(() { busy = true; error = null; });
    try {
      final uri = await widget.api.startNaverLogin();
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) throw Exception('로그인 화면을 열지 못했습니다.');
    } catch (e) { if (mounted) setState(() => error = e.toString()); }
    if (mounted) setState(() => busy = false);
  }
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('아이러브미니 시작하기')),
    body: ListView(padding: const EdgeInsets.all(24), children: [
      const SizedBox(height: 18),
      const Center(child: BrandLogo(height: 205)),
      const SizedBox(height: 24),
      const Text('네이버 아이디로\n간편하게 시작하세요', style: TextStyle(fontSize: 27, fontWeight: FontWeight.w900, height: 1.25)),
      const SizedBox(height: 12),
      Text('첫 로그인 시 아이러브미니 회원 계정이 자동으로 만들어집니다. 네이버 비밀번호는 아이러브미니에 전달되지 않습니다.', style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant, height: 1.5)),
      const SizedBox(height: 28),
      CheckboxListTile(contentPadding: EdgeInsets.zero, value: termsAccepted, onChanged: (value) => setState(() => termsAccepted = value ?? false), title: const Text('(필수) 이용약관 동의')),
      CheckboxListTile(contentPadding: EdgeInsets.zero, value: privacyAccepted, onChanged: (value) => setState(() => privacyAccepted = value ?? false), title: const Text('(필수) 개인정보 처리 안내 동의')),
      SizedBox(height: 54, child: FilledButton.icon(
        style: FilledButton.styleFrom(backgroundColor: const Color(0xFF03A94D), foregroundColor: Colors.white),
        onPressed: (busy || !termsAccepted || !privacyAccepted) ? null : _startLogin,
        icon: const Text('N', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
        label: Text(busy ? '네이버 로그인 진행 중…' : '네이버 아이디로 시작하기', style: const TextStyle(fontWeight: FontWeight.w800)),
      )),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 14), child: Text(error!, style: const TextStyle(color: Colors.red))),
      const SizedBox(height: 16),
      Text('동의 기록은 회원가입 처리에 사용됩니다. 실제 출시 전 약관과 개인정보 처리 안내 문서 및 연결 링크를 확정해야 합니다.', style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
    ]),
  );
  @override
  void dispose() { subscription?.cancel(); super.dispose(); }
}


class BrandLogo extends StatelessWidget {
  const BrandLogo({required this.height, super.key});
  final double height;
  @override
  Widget build(BuildContext context) {
    final width = height * (1346 / 1603);
    return Image.asset('assets/images/ilovemini_logo.png', width: width, height: height, fit: BoxFit.contain);
  }
}

class SectionHeading extends StatelessWidget {
  const SectionHeading({required this.title, required this.subtitle, super.key});
  final String title, subtitle;
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 10), child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
        Text(subtitle, style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
      ]));
}

class InfoCard extends StatelessWidget {
  const InfoCard({required this.text, super.key});
  final String text;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(18), child: Row(children: [
        Icon(Icons.info_outline, color: Theme.of(context).colorScheme.onSurfaceVariant), const SizedBox(width: 12), Expanded(child: Text(text, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant))),
      ])));
}
