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
import 'package:local_auth/local_auth.dart';
import 'api_client.dart';
import 'firebase_options.dart';
import 'partner_map.dart';
import 'partner_directory.dart';

final scaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();
bool firebaseReady = false;
final appThemeMode = ValueNotifier<ThemeMode>(ThemeMode.system);

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

bool _isValidKoreanPlate(String? value) {
  final normalized = (value ?? '').replaceAll(RegExp(r'[\s-]+'), '').toUpperCase();
  return RegExp(r'^(?:[가-힣]{1,2})?\d{2,3}[가-힣]\d{4}$').hasMatch(normalized);
}

String _vehicleRelationshipLabel(dynamic value) => switch (value?.toString()) {
  'owned' => '자가 차량', 'lease' => '리스 차량', 'rental' => '렌트 차량',
  'family' => '가족 차량', 'other' => '기타 이용 차량', _ => '미선택',
};

const favouredF66PhotoAsset = 'assets/images/mini_f66_favoured_red.png';
const maybachS580FrontAsset = 'assets/images/maybach-s580-front.webp';
const naverCafeMobileUrl = 'https://m.cafe.naver.com/minilover/';
const partnerInquiryUrl = 'https://naver.me/xTb4h7ZR';
const recommendedCafeItems = <Map<String, String>>[
  {'title': '차량용 거치대', 'detail': '차량용 스마트폰 거치 아이템 · 호환 정보 확인 중', 'image': 'assets/images/mini-recommended-items/item-01-phone-holder.png'},
  {'title': '실내 고정 브래킷', 'detail': '실내 고정용 부품 · 적용 차종 확인 중', 'image': 'assets/images/mini-recommended-items/item-02-interior-brackets.png'},
  {'title': '프런트 그릴 파츠', 'detail': '외장 그릴 부품 · 적용 차종 확인 중', 'image': 'assets/images/mini-recommended-items/item-03-grille-parts.png'},
  {'title': '기어 노브·부츠', 'detail': '수동 기어 노브와 부츠 · 적용 차종 확인 중', 'image': 'assets/images/mini-recommended-items/item-04-shift-knob.png'},
];

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
        !await launchUrl(uri, mode: LaunchMode.externalApplication, webOnlyWindowName: '_top')) throw Exception();
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
  {'asset': 'assets/images/partner-square-kumho.png', 'alt': '금호타이어와 타이어프로의 아이러브미니 제휴 회원 이벤트', 'url': 'https://m.site.naver.com/2hkXc'},
  {'asset': 'assets/images/partner-square-deutsch.png', 'alt': '도이치모터스 MINI 전시장 전차종 시승 안내'},
  {'asset': 'assets/images/partner-square-printtrap.png', 'alt': '프린트랩 수입차 부품과 자가 정비 지원 안내'},
];

class AffiliateBannerCarousel extends StatefulWidget {
  const AffiliateBannerCarousel({super.key});
  @override
  State<AffiliateBannerCarousel> createState() => _AffiliateBannerCarouselState();
}

class _AffiliateBannerCarouselState extends State<AffiliateBannerCarousel> {
  static const _bannerCount = 3;
  final PageController _controller = PageController(initialPage: 1);
  Timer? _timer;
  int currentPage = 1;
  bool paused = false;

  int get logicalPage => currentPage <= 0 ? _bannerCount : currentPage > _bannerCount ? 1 : currentPage;

  @override
  void initState() { super.initState(); _startTimer(); }

  void _startTimer() {
    _timer?.cancel();
    if (paused) return;
    _timer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (mounted && _controller.hasClients) _controller.nextPage(duration: const Duration(milliseconds: 360), curve: Curves.easeOutCubic);
    });
  }

  void _onPageChanged(int index) {
    if (!mounted) return;
    setState(() => currentPage = index);
    if (index == 0 || index == _bannerCount + 1) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted || !_controller.hasClients) return;
        final target = index == 0 ? _bannerCount : 1;
        _controller.jumpToPage(target);
        setState(() => currentPage = target);
      });
    }
  }

  Future<void> _openBanner(Map<String, String> banner) async {
    final url = banner['url'];
    if (url != null) await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
  }

  @override
  void dispose() { _timer?.cancel(); _controller.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width - 40;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SectionHeading(title: '제휴 배너', subtitle: '카페 제휴 소식'),
      const SizedBox(height: 9),
      ClipRRect(borderRadius: BorderRadius.circular(14), child: SizedBox(height: width, child: Stack(children: [
        PageView.builder(
          controller: _controller,
          itemCount: _bannerCount + 2,
          onPageChanged: _onPageChanged,
          itemBuilder: (context, page) {
            final index = page == 0 ? _bannerCount - 1 : page == _bannerCount + 1 ? 0 : page - 1;
            final banner = partnerBanners[index];
            final image = Image.asset(banner['asset']!, width: width, height: width, fit: BoxFit.cover, semanticLabel: banner['alt']);
            final url = banner['url'];
            return url == null ? image : Semantics(button: true, label: '${banner['alt']} 자세히 보기', child: InkWell(onTap: () => _openBanner(banner), child: image));
          },
        ),
        Positioned(right: 9, bottom: 9, child: DecoratedBox(
          decoration: BoxDecoration(color: const Color(0xC7191A1E), borderRadius: BorderRadius.circular(24)),
          child: Padding(padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3), child: Row(mainAxisSize: MainAxisSize.min, children: [
            IconButton(visualDensity: VisualDensity.compact, tooltip: '이전 배너', onPressed: () => _controller.previousPage(duration: const Duration(milliseconds: 280), curve: Curves.easeOut), icon: const Icon(Icons.chevron_left, color: Colors.white, size: 20)),
            Text('$logicalPage / $_bannerCount', style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w800)),
            IconButton(visualDensity: VisualDensity.compact, tooltip: '다음 배너', onPressed: () => _controller.nextPage(duration: const Duration(milliseconds: 280), curve: Curves.easeOut), icon: const Icon(Icons.chevron_right, color: Colors.white, size: 20)),
            IconButton(visualDensity: VisualDensity.compact, tooltip: paused ? '자동 넘김 재생' : '자동 넘김 일시정지', onPressed: () { setState(() => paused = !paused); if (paused) { _timer?.cancel(); } else { _startTimer(); } }, icon: Icon(paused ? Icons.play_arrow : Icons.pause, color: Colors.white, size: 18)),
          ])),
        )),
      ]))),
    ]);
  }
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
  Widget build(BuildContext context) => ValueListenableBuilder<ThemeMode>(
      valueListenable: appThemeMode,
      builder: (context, mode, _) => MaterialApp(
        title: 'ILOVEMINI',
        debugShowCheckedModeBanner: false,
        scaffoldMessengerKey: scaffoldMessengerKey,
        theme: _appTheme(Brightness.light),
        darkTheme: _appTheme(Brightness.dark),
        themeMode: mode,
        home: const MainShell(),
      ),
    );
}

ThemeData _appTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;
  final background = isDark ? const Color(0xFF191A1E) : paper;
  final surface = isDark ? const Color(0xFF25262C) : Colors.white;
  final text = isDark ? const Color(0xFFF3F3F5) : ink;
  final muted = isDark ? const Color(0xFFB2B3BC) : const Color(0xFF686B73);
  final accent = brandRed;
  final border = isDark ? const Color(0xFF3B3D44) : const Color(0xFFDFE0E4);
  final scheme = ColorScheme.fromSeed(seedColor: brandRed, brightness: brightness).copyWith(
    primary: accent, onPrimary: Colors.white,
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
    navigationBarTheme: NavigationBarThemeData(backgroundColor: background, surfaceTintColor: Colors.transparent, indicatorColor: Colors.transparent, iconTheme: WidgetStateProperty.resolveWith((states) => IconThemeData(color: states.contains(WidgetState.selected) ? brandRed : muted)), labelTextStyle: WidgetStateProperty.resolveWith((states) => TextStyle(color: states.contains(WidgetState.selected) ? brandRed : muted, fontSize: 12)), height: 76),
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
  final localAuth = LocalAuthentication();
  try {
    if (!await localAuth.isDeviceSupported()) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('이 기기에서 화면 잠금 인증을 사용할 수 없어 QR을 열지 않았어요.')),
      );
      return;
    }
    final authenticated = await localAuth.authenticate(
      localizedReason: '차량 QR을 표시하려면 Face ID, 지문 또는 기기 잠금으로 인증해 주세요.',
      biometricOnly: false,
    );
    if (!authenticated) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('인증이 완료되지 않아 QR을 열지 않았어요.')),
      );
      return;
    }
  } catch (_) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('기기 인증을 사용할 수 없습니다. Face ID·지문 또는 화면 잠금을 설정해 주세요.')),
    );
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
          : '승인된 협력업체 담당자에게 이 QR을 보여주세요. 차량 QR 자체에는 차주 개인정보가 들어 있지 않습니다.', textAlign: TextAlign.center),
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
    setState(() { signedIn = false; tab = 4; });
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
      appBar: AppBar(centerTitle: false, title: Semantics(button: true, label: 'ILOVEMINI 홈으로 이동', child: InkWell(
        mouseCursor: SystemMouseCursors.click,
        borderRadius: BorderRadius.circular(8),
        onTap: () => setState(() => tab = 0),
        child: const Row(mainAxisSize: MainAxisSize.min, children: [BrandLogo(height: 52), SizedBox(width: 12), Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('ILOVEMINI', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, letterSpacing: 2)), Text('OWNERS COMMUNITY', style: TextStyle(fontSize: 8, letterSpacing: 2))])]),
      )) , actions: [IconButton(tooltip: '화면 테마 변경', icon: Icon(Theme.of(context).brightness == Brightness.dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined), onPressed: () { appThemeMode.value = Theme.of(context).brightness == Brightness.dark ? ThemeMode.light : ThemeMode.dark; })]),
      body: switch (tab) {
        0 => HomePage(api: api, signedIn: signedIn, onOpenGarage: () => setState(() => tab = 1), onLogin: _login),
        1 => GaragePage(key: ValueKey('garage-$signedIn'), api: api, signedIn: signedIn, onLogin: _login),
        2 => CafePage(api: api),
        3 => CatalogPage(api: api, path: 'partners', title: 'ILOVEMINI 협력업체'),
        _ => AccountPage(api: api, signedIn: signedIn, pushEnabled: pushEnabled, onPushChanged: _setPushEnabled, onLogin: _login, onLogout: () async { await _removePushInstallation(); await api.logout(); if (mounted) setState(() { signedIn = false; pushEnabled = false; }); }, onManageVehicles: () => setState(() => tab = 1)),
      },
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: (value) => setState(() => tab = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: '홈'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), selectedIcon: Icon(Icons.receipt_long_outlined), label: '차계부'),
          NavigationDestination(icon: Icon(Icons.forum_outlined), selectedIcon: Icon(Icons.forum), label: '카페'),
          NavigationDestination(icon: Icon(Icons.build_outlined), selectedIcon: Icon(Icons.build_outlined), label: '업체'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'MY'),
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
    const SizedBox(height: 10),
    Row(children: [
      Expanded(child: OutlinedButton.icon(onPressed: onOpenGarage, icon: const Icon(Icons.add), label: const Text('기록 추가'))),
      const SizedBox(width: 12),
      Expanded(child: OutlinedButton.icon(onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => CatalogPage(api: api, path: 'partners', title: '업체 찾기 · 예약'))), icon: const Icon(Icons.storefront_outlined), label: const Text('업체 찾기'))),
    ]),
    const SizedBox(height: 16),
    const SectionHeading(title: '제휴 배너', subtitle: '카페 제휴 소식'),
    const SizedBox(height: 10),
    const AffiliateBannerCarousel(),
  ]);
}

class CafePage extends StatelessWidget {
  const CafePage({required this.api, super.key});
  final ApiClient api;
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.fromLTRB(20, 14, 20, 28), children: [
    const Text('ILOVEMINI CAFE', style: TextStyle(color: brandRed, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 2.4)),
    const SizedBox(height: 5),
    const Text('카페 소식', style: TextStyle(fontSize: 27, fontWeight: FontWeight.w900, letterSpacing: -0.7)),
    const SizedBox(height: 3),
    Text('공지사항, 회원 MINI 앨범, 정비 Q&A를 한곳에서 확인해요.', style: TextStyle(fontSize: 13, color: Theme.of(context).colorScheme.onSurfaceVariant)),
    const SizedBox(height: 18),
    CafeKnowledgeSearch(api: api),
    const SizedBox(height: 16),
    const SectionHeading(title: '카페 공지사항', subtitle: '필독 2건'),
    const CafeNoticeFeed(previewCount: 2),
    const SizedBox(height: 12),
    const CafeMiniAlbumPreview(),
    const SizedBox(height: 12),
    const RecommendedCafeItemsCarousel(),
  ]);
}

class RecommendedCafeItemsCarousel extends StatefulWidget {
  const RecommendedCafeItemsCarousel({super.key});
  @override
  State<RecommendedCafeItemsCarousel> createState() => _RecommendedCafeItemsCarouselState();
}

class _RecommendedCafeItemsCarouselState extends State<RecommendedCafeItemsCarousel> {
  static const _interval = Duration(seconds: 5);
  late final PageController _controller;
  Timer? _timer;
  int _page = 1;
  bool _paused = false;

  int get _logicalPage {
    if (_page <= 0) return recommendedCafeItems.length;
    if (_page > recommendedCafeItems.length) return 1;
    return _page;
  }

  @override
  void initState() {
    super.initState();
    _controller = PageController(initialPage: _page);
    _startTimer();
  }

  void _startTimer() {
    _timer?.cancel();
    if (_paused) return;
    _timer = Timer.periodic(_interval, (_) {
      if (!mounted || !_controller.hasClients) return;
      _controller.nextPage(duration: const Duration(milliseconds: 360), curve: Curves.easeOutCubic);
    });
  }

  void _onPageChanged(int page) {
    if (!mounted) return;
    setState(() => _page = page);
    if (page == 0 || page == recommendedCafeItems.length + 1) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted || !_controller.hasClients) return;
        final target = page == 0 ? recommendedCafeItems.length : 1;
        _controller.jumpToPage(target);
        setState(() => _page = target);
      });
    }
  }

  void _togglePause() {
    setState(() => _paused = !_paused);
    if (_paused) {
      _timer?.cancel();
    } else {
      _startTimer();
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width - 40;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SectionHeading(title: 'MINI 추천 아이템', subtitle: '회원 추천 아이템'),
      const SizedBox(height: 2),
      Text('제품 정보와 MINI 호환 여부를 확인하고 있어요.', style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
      const SizedBox(height: 9),
      Card(clipBehavior: Clip.antiAlias, child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        SizedBox(
          height: width,
          child: Stack(children: [
            PageView.builder(
              controller: _controller,
              itemCount: recommendedCafeItems.length + 2,
              onPageChanged: _onPageChanged,
              itemBuilder: (context, page) {
                final itemIndex = page == 0 ? recommendedCafeItems.length - 1 : page == recommendedCafeItems.length + 1 ? 0 : page - 1;
                final item = recommendedCafeItems[itemIndex];
                return ColoredBox(
                  color: Colors.white,
                  child: Image.asset(item['image']!, fit: BoxFit.contain, semanticLabel: item['title'],
                    errorBuilder: (context, error, stackTrace) => const Center(child: Icon(Icons.image_not_supported_outlined, size: 42))),
                );
              },
            ),
            Positioned(right: 9, bottom: 9, child: DecoratedBox(
              decoration: BoxDecoration(color: const Color(0xC7191A1E), borderRadius: BorderRadius.circular(24)),
              child: Padding(padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3), child: Row(mainAxisSize: MainAxisSize.min, children: [
                IconButton(visualDensity: VisualDensity.compact, tooltip: '이전 아이템', onPressed: () => _controller.previousPage(duration: const Duration(milliseconds: 280), curve: Curves.easeOut), icon: const Icon(Icons.chevron_left, color: Colors.white, size: 20)),
                Text('$_logicalPage / ${recommendedCafeItems.length}', style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w800)),
                IconButton(visualDensity: VisualDensity.compact, tooltip: '다음 아이템', onPressed: () => _controller.nextPage(duration: const Duration(milliseconds: 280), curve: Curves.easeOut), icon: const Icon(Icons.chevron_right, color: Colors.white, size: 20)),
                IconButton(visualDensity: VisualDensity.compact, tooltip: _paused ? '자동 넘김 재생' : '자동 넘김 일시정지', onPressed: _togglePause, icon: Icon(_paused ? Icons.play_arrow : Icons.pause, color: Colors.white, size: 18)),
              ])),
            )),
          ]),
        ),
        Padding(padding: const EdgeInsets.fromLTRB(14, 11, 14, 13), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(recommendedCafeItems[_logicalPage - 1]['title']!, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
          const SizedBox(height: 3),
          Text(recommendedCafeItems[_logicalPage - 1]['detail']!, style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
          const SizedBox(height: 8),
          const Align(alignment: Alignment.centerLeft, child: Chip(visualDensity: VisualDensity.compact, label: Text('구매 링크 준비 중'))),
        ])),
      ])),
      const SizedBox(height: 6),
      Text('실제 등록 전 상품명과 적용 차종을 확인할 예정입니다.', style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurfaceVariant)),
    ]);
  }
}

class CafeKnowledgeSearch extends StatefulWidget {
  const CafeKnowledgeSearch({required this.api, super.key});
  final ApiClient api;
  @override
  State<CafeKnowledgeSearch> createState() => _CafeKnowledgeSearchState();
}

class _CafeKnowledgeSearchState extends State<CafeKnowledgeSearch> {
  final queryController = TextEditingController();
  String? searchError;

  Future<void> search([String? value]) => _openSearch(value: value);

  Future<void> searchNaver() => _openSearch(cafe: true);

  Future<void> _openSearch({String? value, bool cafe = false}) async {
    final query = (value ?? queryController.text).trim();
    if (query.length < 2 || query.length > 120) {
      setState(() => searchError = '질문을 2~120자로 입력해 주세요.');
      return;
    }
    queryController.text = query;
    setState(() => searchError = null);
    final uri = cafe
        ? Uri.https('m.cafe.naver.com', '/ca-fe/web/cafes/13071593/search', {
            'q': query, 'mi': '0', 'ta': 'SUBJECT', 'pc': 'ALL', 'od': 'NEW',
          })
        : Uri.https('search.naver.com', '/search.naver', {
            'query': query, 'qvt': '0', 'ssc': 'tab.ait.all',
          });
    try {
      // Native iOS/Android delegates HTTPS to the system, outside the app WebView.
      // The web build navigates the top-level window instead of creating a popup.
      final opened = await launchUrl(uri,
        mode: LaunchMode.externalApplication,
        webOnlyWindowName: '_top',
      );
      if (!opened) throw Exception('외부 검색 화면을 열지 못했습니다.');
    } catch (_) {
      if (mounted) setState(() => searchError = '네이버 검색을 열지 못했습니다. 다시 시도해 주세요.');
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
        Text('MINI 박사 Q&A', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
        Text('네이버 AI탭에서 질문하고, 카페 글도 찾아보세요.', style: TextStyle(fontSize: 12)),
      ])),
    ]),
    const SizedBox(height: 12),
    Row(children: [
      Expanded(child: TextField(controller: queryController,
        style: const TextStyle(fontSize: 16),
        maxLength: 120,
        textInputAction: TextInputAction.search,
        onSubmitted: search,
        decoration: const InputDecoration(hintText: '정비 질문 또는 검색어 입력', counterText: ''),
      )),
      const SizedBox(width: 8),
      FilledButton(onPressed: () => search(), child: const Text('AI 검색')),
    ]),
    if (searchError != null) ...[
      const SizedBox(height: 8),
      Text(searchError!, style: const TextStyle(fontSize: 13, color: brandRed)),
    ],
    Align(alignment: Alignment.centerRight, child: TextButton.icon(
      onPressed: searchNaver,
      icon: const Icon(Icons.open_in_new, size: 16),
      label: const Text('아이러브미니 카페에서 검색'),
    )),
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
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.event_available, color: brandRed),
            const SizedBox(width: 8),
            const Expanded(child: Text('오늘의 출석체크', style: TextStyle(fontWeight: FontWeight.w800))),
            Text('$points P', style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900, color: brandRed)),
          ]),
          const SizedBox(height: 6),
          Text('매일 출석 1,000P · 7일 연속 보너스 3,000P · 현재 $streak일 연속', style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
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

class CafeMiniAlbumPreview extends StatefulWidget {
  const CafeMiniAlbumPreview({super.key});
  @override
  State<CafeMiniAlbumPreview> createState() => _CafeMiniAlbumPreviewState();
}

class _CafeMiniAlbumPreviewState extends State<CafeMiniAlbumPreview> {
  static const _posts = [
    {'image': 'album-01.jpg', 'title': '연휴 끝', 'author': '꼬마악동', 'meta': '01:05 · 조회 137'},
    {'image': 'album-02.jpg', 'title': '명절이라 디테일링 …', 'author': '구름아', 'meta': '26.09.25 · 조회 220'},
    {'image': 'album-03.jpg', 'title': '몇년만에 손세차.. F60', 'author': '케인지F60촌놈', 'meta': '26.09.25 · 조회 147'},
    {'image': 'album-04.jpg', 'title': '블랙의 세차', 'author': '집가이', 'meta': '26.09.25 · 조회 187'},
    {'image': 'album-05.jpg', 'title': '3개월만에 차 받았어…', 'author': '빵빵도우', 'meta': '26.09.23 · 조회 250'},
    {'image': 'album-06.jpg', 'title': '하루를 마감하는 미니', 'author': '집가이', 'meta': '26.09.23 · 조회 159'},
  ];
  final ScrollController _scrollController = ScrollController();
  int _index = 0;

  void _updateIndex(double cardStep) {
    if (!_scrollController.hasClients) return;
    final next = (_scrollController.offset / cardStep).round().clamp(0, _posts.length - 1);
    if (next != _index && mounted) setState(() => _index = next);
  }

  void _move(double cardStep, int direction) {
    if (!_scrollController.hasClients) return;
    final destination = (_scrollController.offset + cardStep * direction)
        .clamp(0.0, _scrollController.position.maxScrollExtent).toDouble();
    _scrollController.animateTo(destination, duration: const Duration(milliseconds: 280), curve: Curves.easeOut);
  }

  @override
  void dispose() { _scrollController.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cardWidth = (MediaQuery.sizeOf(context).width - 40) * .7;
    final cardStep = cardWidth + 12;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const Expanded(child: SectionHeading(title: '미니앨범', subtitle: '카페 회원들의 MINI 이야기')),
        IconButton(tooltip: '이전 사진', onPressed: _index == 0 ? null : () => _move(cardStep, -1), icon: const Icon(Icons.chevron_left)),
        Text('${_index + 1} / ${_posts.length}', style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurfaceVariant)),
        IconButton(tooltip: '다음 사진', onPressed: _index == _posts.length - 1 ? null : () => _move(cardStep, 1), icon: const Icon(Icons.chevron_right)),
      ]),
      SizedBox(height: cardWidth + 82, child: NotificationListener<ScrollNotification>(
        onNotification: (notification) { _updateIndex(cardStep); return false; },
        child: ListView.separated(
          controller: _scrollController,
          scrollDirection: Axis.horizontal,
          physics: const BouncingScrollPhysics(),
          itemCount: _posts.length,
          separatorBuilder: (_, __) => const SizedBox(width: 12),
          itemBuilder: (context, index) {
            final post = _posts[index];
            return SizedBox(width: cardWidth, child: Semantics(
              button: true,
              label: '${post['title']}, ${post['author']}. 아이러브미니 카페 미니앨범 열기',
              child: InkWell(
                borderRadius: BorderRadius.circular(10),
                onTap: () => _openCafeNotice(context, naverCafeMobileUrl),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: AspectRatio(
                      aspectRatio: 1,
                      child: Image.asset('assets/images/mini-album/${post['image']}', fit: BoxFit.cover),
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(post['title']!, maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 3),
                  Text(post['author']!, maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface)),
                  const SizedBox(height: 2),
                  Text(post['meta']!, maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurfaceVariant)),
                ]),
              ),
            ));
          },
        ),
      )),
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
          if (vehicle != null) IconButton(tooltip: '차량 QR', onPressed: () => showVehiclePassportQr(context, vehicle), icon: const Icon(Icons.qr_code_2)),
          TextButton(onPressed: widget.onGarage, child: const Text('차량 관리')),
        ]),
        if (vehicle != null && (hasFavouredF66Photo(vehicle) || hasMaybachPhoto(vehicle)))
          VehiclePhoto(vehicle: vehicle, height: 220),
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

Map<String, String>? partnerExternalActions(String name) {
  if (name.contains('얼마면탈까')) return {'label': '상담', 'contact': 'https://pf.kakao.com/_xerCTG/chat', 'site': 'https://openestimate.co.kr/'};
  if (name.contains('프린트랩')) return {'label': '상담', 'contact': 'https://pf.kakao.com/_mxlrHj/chat', 'site': 'https://smartstore.naver.com/print_lab/'};
  if (name.contains('금호타이어')) return {'label': '채널', 'contact': 'https://pf.kakao.com/_XNxdxkxl', 'site': 'https://www.kumhotire.com/ko/index.do'};
  return null;
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
  late Future<List<Map<String, dynamic>>> itemsFuture;
  String query = '', filter = '전체', regionFilter = '전체 지역';
  String mapQuery = '대한민국';
  final mapPanelKey = GlobalKey();
  void showPartnerMap(Map<String, dynamic> item) {
    final actions = partnerExternalActions('${item['name']}');
    if (actions != null) { _openCafeNotice(context, actions['contact']!); return; }
    setState(() => mapQuery = '${item['name']} ${item['address'] ?? item['region'] ?? ''}'.trim());
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final panel = mapPanelKey.currentContext;
      if (panel != null) Scrollable.ensureVisible(panel, alignment: .1, duration: const Duration(milliseconds: 300));
    });
  }
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
    final categoryMatch = switch (filter) {
      '정비' => categories.contains('정비') || categories.contains('수입차'),
      '사고수리' => categories.contains('사고') || categories.contains('판금'),
      '차량유리' => categories.contains('유리'),
      '오디오·전장' => categories.contains('오디오') || categories.contains('전장'),
      '휠·타이어' => categories.contains('휠') || categories.contains('타이어'),
      '부품·튜닝' => categories.contains('부품') || categories.contains('튜닝'),
      '신차패키지' => _partnerSpecialty(item) == '신차패키지',
      '수도권' => _partnerRegionGroup(item) == '서울/경기 협력업체' && _partnerSpecialty(item) != '신차패키지',
      '지방' => _partnerRegionGroup(item) == '전라/경상/충청 협력업체',
      _ => true,
    };
    return categoryMatch && (regionFilter == '전체 지역' || _partnerRegionGroup(item) == regionFilter) && text.contains(query.trim().toLowerCase());
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
    if (RegExp(r'휠|타이어').hasMatch(text)) return '휠·타이어 전문';
    return '정비 전문';
  }
  bool _partnerHasSpecialty(Map<String, dynamic> item, String specialty) {
    final text = '${item['category'] ?? ''} ${(item['service_categories'] as List? ?? []).join(' ')}';
    return switch (specialty) {
      '사고수리 전문' => text.contains('사고') || text.contains('판금'),
      '차량유리 전문' => text.contains('유리'),
      '전장류 전문' => RegExp(r'전장|오디오').hasMatch(text),
      '휠·타이어 전문' => RegExp(r'휠|타이어').hasMatch(text),
      '사고수리·정비 전문' => (text.contains('사고') || text.contains('판금')) && RegExp(r'정비|수리|서비스|디젤').hasMatch(text),
      '부품·튜닝 전문' => text.contains('부품') || (text.contains('튜닝') && !RegExp(r'전장|오디오').hasMatch(text)),
      '정비 전문' => RegExp(r'정비|서비스|디젤').hasMatch(text) || (text.contains('수리') && !RegExp(r'사고|판금|도색|휠').hasMatch(text)),
      _ => _partnerSpecialty(item) == specialty,
    };
  }
  List<Widget> _partnerGroupTiles(List<Map<String, dynamic>> items) {
    const groups = ['사고수리 전문', '차량유리 전문', '전장류 전문', '휠·타이어 전문', '부품·튜닝 전문', '정비 전문', '신차패키지'];
    return ['서울/경기 협력업체', '전라/경상/충청 협력업체', '신차패키지'].expand((region) {
      final shops = items.where((item) => region == '신차패키지' ? _partnerSpecialty(item) == '신차패키지' : _partnerSpecialty(item) != '신차패키지' && _partnerRegionGroup(item) == region).toList();
      if (shops.isEmpty) return <Widget>[];
      final headings = region == '전라/경상/충청 협력업체' ? ['사고수리·정비 전문'] : region == '신차패키지' ? ['신차패키지'] : groups;
      return <Widget>[
        Padding(padding: const EdgeInsets.symmetric(vertical: 16), child: Row(children: [Expanded(child: Text(region == '서울/경기 협력업체' ? '수도권 협력업체' : region == '신차패키지' ? '신차패키지 업체' : '지방 협력업체', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18))), Text('${shops.length}곳')])),
        ...headings.map((group) {
          final list = shops.where((item) => group == '사고수리·정비 전문' || _partnerHasSpecialty(item, group)).toList();
          if (list.isEmpty) return const SizedBox.shrink();
          return Card(clipBehavior: Clip.antiAlias, child: ExpansionTile(
            key: PageStorageKey('partner-$region-$group-$filter-$query'),
            initiallyExpanded: filter != '전체' || query.isNotEmpty,
            title: Text(group, style: const TextStyle(fontWeight: FontWeight.w700)),
            trailing: Row(mainAxisSize: MainAxisSize.min, children: [Text('${list.length}곳'), const SizedBox(width: 12), const Icon(Icons.add, color: brandRed)]),
            children: list.map((item) {
              final external = partnerExternalActions('${item['name']}');
              return Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                InkWell(onTap: () => openItem(item), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text([item['name'], if ((item['branch_label'] ?? '').toString().isNotEmpty) item['branch_label']].join(' · '), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                  const SizedBox(height: 6), Text('${(item['address'] ?? '').toString().isNotEmpty ? item['address'] : item['region']} · ${item['category'] ?? group}', style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
                ])),
                const SizedBox(height: 10),
                Row(children: [Expanded(child: OutlinedButton(onPressed: () => showPartnerMap(item), child: Text(external?['label'] ?? '지도보기'))), const SizedBox(width: 8), Expanded(child: FilledButton(onPressed: () => external == null ? openItem(item) : _openCafeNotice(context, external['site']!), child: Text(external == null ? '예약 요청' : '사이트 이동')))]),
              ]));
            }).toList(),
          ));
        }),
      ];
    }).toList();
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
          InfoCard(text: snapshot.error is TimeoutException ? '서버가 시작하는 데 시간이 걸리고 있습니다. 잠시 후 다시 시도해 주세요.' : '목록 요청 실패: ${snapshot.error.toString().replaceFirst("Exception: ", "")}'),
          TextButton(onPressed: reload, child: const Text('다시 시도')),
        ]);
        final apiItems = snapshot.data ?? [];
        final isPartners = widget.path == 'partners';
        final all = isPartners ? alignPartnerDirectory(apiItems) : apiItems;
        final items = isPartners ? all.where(matches).toList() : all;
        return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          if (isPartners) ...[
            if (!widget.compact) ...[
              const Text('ILOVEMINI PARTNERS', style: TextStyle(color: brandRed, letterSpacing: 3, fontWeight: FontWeight.w800)),
              const SizedBox(height: 10),
              Text('협력업체 찾기', style: const TextStyle(fontSize: 25, height: 1.12, fontWeight: FontWeight.w900, letterSpacing: -0.7)),
              const SizedBox(height: 8),
              Text('분야와 지역으로 찾고, 지도 확인과 예약 요청을 한곳에서 진행하세요.', style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
              const SizedBox(height: 18),
              Row(children: [Expanded(flex: 3, child: TextField(decoration: const InputDecoration(hintText: '업체명 정비 항목 검색'), onChanged: (value) => setState(() => query = value))), const SizedBox(width: 10), Expanded(flex: 2, child: DropdownButtonFormField<String>(initialValue: regionFilter, items: ['전체 지역', '서울/경기 협력업체', '전라/경상/충청 협력업체', '신차패키지'].map((value) => DropdownMenuItem(value: value, child: Text(value == '서울/경기 협력업체' ? '수도권' : value == '전라/경상/충청 협력업체' ? '지방' : value, overflow: TextOverflow.ellipsis))).toList(), onChanged: (value) => setState(() => regionFilter = value!)))]),
              const SizedBox(height: 12),
              Wrap(spacing: 8, runSpacing: 8, children: ['전체', '정비', '사고수리', '오디오·전장', '차량유리', '휠·타이어', '부품·튜닝', '신차패키지', '수도권', '지방'].map((name) => ChoiceChip(
                label: Text(name), selected: filter == name, showCheckmark: false, selectedColor: brandRed, labelStyle: TextStyle(color: filter == name ? Colors.white : Theme.of(context).colorScheme.onSurface), shape: const StadiumBorder(),
                onSelected: (_) => setState(() => filter = name))).toList()),
            ],
            const SizedBox(height: 24),
            const Text('Google 업체 지도', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            const Text('업체별 지도·상담 버튼으로 위치를 확인하거나 문의할 수 있어요.'),
            const SizedBox(height: 12),
          ],
          if (items.isEmpty) InfoCard(text: all.isEmpty ? widget.title : '검색 조건에 맞는 업체가 없습니다.'),
          if (isPartners) ...[
            Padding(key: mapPanelKey, padding: const EdgeInsets.only(bottom: 16), child: PartnerMap(query: mapQuery)),
            Row(children: [const Expanded(child: Text('검색 결과')), Text('${items.length}곳', style: const TextStyle(fontWeight: FontWeight.w800))]),
            ..._partnerGroupTiles(items),
          ]
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
    final branchLabel = (partner['branch_label'] ?? '').toString();
    final phone = (partner['phone'] ?? '').toString();
    final address = (partner['address'] ?? '').toString();
    final mapLink = (partner['map_url'] ?? '').toString();
    final cafeLink = (partner['cafe_url'] ?? '').toString();
    final infoPending = (partner['region'] ?? '').toString().contains('확인 필요') && cafeLink.isEmpty;
    final externalActions = partnerExternalActions(name);
    final categories = (partner['service_categories'] as List? ?? const []).map((item) => item.toString()).toList();
    final details = <Widget>[
      if (address.isNotEmpty) ListTile(leading: const Icon(Icons.location_on_outlined), title: const Text('주소'), subtitle: Text(address)),
      if (phone.isNotEmpty) ListTile(leading: const Icon(Icons.call_outlined), title: const Text('전화번호'), subtitle: Text(phone)),
      if ((partner['hours'] ?? '').toString().isNotEmpty) ListTile(leading: const Icon(Icons.schedule_outlined), title: const Text('영업시간'), subtitle: Text(partner['hours'].toString())),
    ];
    final usableMapUri = Uri.https('www.google.com', '/maps/search/', {'api': '1', 'query': '$name $branchLabel $address'.trim()});
    return Scaffold(
      appBar: AppBar(title: const Text('업체 정보')),
      body: ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 28), children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(color: ink, borderRadius: BorderRadius.circular(22)),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (partner['is_sponsored'] == true) const _SponsoredBadge(),
            const SizedBox(height: 12),
            Text([name, if (branchLabel.isNotEmpty) branchLabel].join(' · '), style: const TextStyle(color: Colors.white, fontSize: 25, fontWeight: FontWeight.w900)),
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
        const SizedBox(height: 16),
        if (externalActions == null) PartnerMap(query: '$name $branchLabel ${address.isEmpty ? partner['region'] ?? '' : address}'),
        if (externalActions != null) Row(children: [
          Expanded(child: OutlinedButton(onPressed: () => _launch(context, Uri.parse(externalActions['contact']!)), child: Text(externalActions['label']!))),
          const SizedBox(width: 12),
          Expanded(child: FilledButton(onPressed: () => _launch(context, Uri.parse(externalActions['site']!)), child: const Text('사이트이동'))),
        ]),
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
            if (mapLink.isNotEmpty || address.isNotEmpty) Expanded(child: OutlinedButton.icon(onPressed: () => _launch(context, usableMapUri), icon: const Icon(Icons.map_outlined), label: const Text('지도보기'))),
          ]),
        if (infoPending)
          const InfoCard(text: '이 업체는 협력업체 목록에서 확인했지만 지역·연락처·카페 게시글은 아직 확인되지 않았습니다. 확인 전 정보는 표시하지 않습니다.')
        else if (phone.isEmpty && mapLink.isEmpty && address.isEmpty)
          const InfoCard(text: '업체 연락처와 위치는 실제 정보를 등록한 뒤 표시됩니다.'),
        if (cafeLink.isNotEmpty) ...[
          const SizedBox(height: 8),
          OutlinedButton.icon(onPressed: () => _launch(context, Uri.tryParse(cafeLink) ?? Uri()), icon: const Icon(Icons.open_in_new), label: const Text('카페에서 더 알아보기')),
        ],
        const SizedBox(height: 12),
        if (partner['catalog_only'] == true) const InfoCard(text: '이 지점은 위치 확인만 가능합니다. 서버에 지점 등록 후 예약을 연결합니다.'),
        if (externalActions == null && partner['catalog_only'] != true) FilledButton.icon(
          onPressed: () async {
            final result = await Navigator.of(context).push<bool>(MaterialPageRoute(
              builder: (_) => PartnerBookingPage(api: api, partner: partner),
            ));
            if (result == true && context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('업체에 예약 요청을 보냈습니다. MY에서 상태를 확인할 수 있어요.')));
            }
          },
          icon: const Icon(Icons.calendar_month_outlined), label: const Text('예약 요청'),
        ),
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

class _LedgerEntryDialog extends StatefulWidget {
  const _LedgerEntryDialog({required this.api, required this.vehicleId});
  final ApiClient api;
  final int vehicleId;

  @override
  State<_LedgerEntryDialog> createState() => _LedgerEntryDialogState();
}

class _LedgerEntryDialogState extends State<_LedgerEntryDialog> {
  final formKey = GlobalKey<FormState>();
  final description = TextEditingController();
  final amount = TextEditingController();
  final odometer = TextEditingController();
  String kind = 'fuel';
  String? error;
  bool busy = false;

  Future<void> save() async {
    if (busy || !formKey.currentState!.validate()) return;
    setState(() { busy = true; error = null; });
    try {
      await widget.api.create('ledger', {
        'vehicle': widget.vehicleId,
        'kind': kind,
        'entry_date': DateTime.now().toIso8601String().substring(0, 10),
        'description': description.text.trim(),
        'amount_krw': int.parse(amount.text.trim()),
        'odometer_km': odometer.text.trim().isEmpty ? null : int.parse(odometer.text.trim()),
      });
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('차계부 기록 추가'),
    content: SizedBox(width: 420, child: SingleChildScrollView(child: Form(key: formKey, child: Column(mainAxisSize: MainAxisSize.min, children: [
      DropdownButtonFormField<String>(initialValue: kind, decoration: const InputDecoration(labelText: '기록 종류'), items: const [
        DropdownMenuItem(value: 'fuel', child: Text('주유')), DropdownMenuItem(value: 'service', child: Text('정비')),
        DropdownMenuItem(value: 'part', child: Text('소모품')), DropdownMenuItem(value: 'wash', child: Text('세차')),
        DropdownMenuItem(value: 'other', child: Text('기타')),
      ], onChanged: busy ? null : (value) => setState(() => kind = value ?? 'fuel')),
      TextFormField(controller: description, decoration: const InputDecoration(labelText: '내용', hintText: '예: 셀프 주유'), validator: (value) => value?.trim().isNotEmpty == true ? null : '기록 내용을 입력해 주세요.'),
      TextFormField(controller: amount, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '금액 원'), validator: (value) => int.tryParse(value ?? '') != null && int.parse(value!) >= 0 ? null : '금액을 숫자로 입력해 주세요.'),
      TextFormField(controller: odometer, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '주행거리 km (선택)'), validator: (value) => value == null || value.trim().isEmpty || (int.tryParse(value.trim()) != null && int.parse(value.trim()) >= 0) ? null : '주행거리를 0 이상의 숫자로 입력해 주세요.'),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(error!, style: const TextStyle(color: Colors.red))),
    ])))),
    actions: [
      TextButton(onPressed: busy ? null : () => Navigator.pop(context, false), child: const Text('취소')),
      FilledButton(onPressed: busy ? null : save, child: Text(busy ? '저장 중…' : '저장')),
    ],
  );

  @override
  void dispose() {
    description.dispose(); amount.dispose(); odometer.dispose();
    super.dispose();
  }
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
    vehiclesFuture = widget.signedIn || ApiClient.demoMode ? widget.api.list('vehicles') : Future.value([]);
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
          if ((transfer['plate_number'] ?? '').toString().isNotEmpty)
            Text('차량 번호: ${transfer['plate_number']}', style: const TextStyle(fontWeight: FontWeight.w700)),
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
    final plateNumber = (preview['plate_number'] ?? '').toString().trim();
    final odometer = preview['current_odometer_km'] == null ? '미등록' : '${preview['current_odometer_km']} km';
    String incomingRelationship = 'owned';
    final acceptedRelationship = await showDialog<String?>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setDialogState) => AlertDialog(
      title: const Text('차량과 기록을 인계받을까요?'),
      content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(
          '${preview['model_name'] ?? 'MINI'}$year${generation.isEmpty ? '' : ' · $generation'}\n'
          '차량 번호: ${plateNumber.isEmpty ? '미등록' : plateNumber}\n'
          '현재 주행거리: $odometer\n'
          '차계부 ${preview['ledger_count']}건 · 업체 실차 확인 기록 ${preview['verified_record_count']}건 · 정정 이력 ${preview['correction_count']}건\n'
          '정비 알림 ${preview['reminder_count']}건\n\n'
          '이 차량을 이용하는 형태를 선택해 주세요. 등록 정보는 법적 소유권을 확인하지 않습니다. 차량과 판매자를 확인한 뒤 승인하세요.',
          style: const TextStyle(height: 1.5),
        ),
        DropdownButtonFormField<String>(initialValue: incomingRelationship, decoration: const InputDecoration(labelText: '내 차량 이용 형태'), items: const [
          DropdownMenuItem(value: 'owned', child: Text('자가 차량')), DropdownMenuItem(value: 'lease', child: Text('리스 차량')),
          DropdownMenuItem(value: 'rental', child: Text('렌트 차량')), DropdownMenuItem(value: 'family', child: Text('가족 차량')),
          DropdownMenuItem(value: 'other', child: Text('기타 이용 차량')),
        ], onChanged: (value) => setDialogState(() => incomingRelationship = value ?? 'owned')),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('취소')),
        FilledButton(onPressed: () => Navigator.pop(dialogContext, incomingRelationship), child: const Text('인계 승인')),
      ],
    )));
    if (acceptedRelationship == null) return;
    try {
      final transferred = await widget.api.acceptVehicleTransfer(result['code'].toString(), acceptedRelationship);
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
    final plate = TextEditingController();
    final odometer = TextEditingController();
    String? error;
    String useRelationship = 'owned';
    final created = await showDialog<bool>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setDialogState) => AlertDialog(
      title: const Text('내 차량 등록'),
      content: SizedBox(width: 420, child: SingleChildScrollView(child: Form(key: formKey, child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextFormField(controller: model, decoration: const InputDecoration(labelText: '차종 *', hintText: '예: MINI Cooper S, Mercedes-Maybach S 580'), validator: (v) => (v == null || v.trim().isEmpty) ? '차종을 입력해 주세요.' : null),
        TextFormField(controller: nickname, decoration: const InputDecoration(labelText: '별명 (선택)'),),
        TextFormField(controller: generation, decoration: const InputDecoration(labelText: '세대 (선택)'),),
        TextFormField(controller: year, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '연식 (선택)'), validator: (v) => (v != null && v.isNotEmpty && int.tryParse(v) == null) ? '연식은 숫자로 입력해 주세요.' : null),
        TextFormField(controller: plate, textCapitalization: TextCapitalization.characters, decoration: const InputDecoration(labelText: '차량 번호판 *', hintText: '예: 12가3456'), validator: (v) => _isValidKoreanPlate(v) ? null : '차량 번호를 확인해 주세요. 예: 12가3456'),
        DropdownButtonFormField<String>(initialValue: useRelationship, decoration: const InputDecoration(labelText: '차량 이용 형태 *'), items: const [
          DropdownMenuItem(value: 'owned', child: Text('자가 차량')), DropdownMenuItem(value: 'lease', child: Text('리스 차량')),
          DropdownMenuItem(value: 'rental', child: Text('렌트 차량')), DropdownMenuItem(value: 'family', child: Text('가족 차량')),
          DropdownMenuItem(value: 'other', child: Text('기타 이용 차량')),
        ], onChanged: (value) => setDialogState(() => useRelationship = value ?? 'owned')),
        const Padding(padding: EdgeInsets.only(top: 6), child: Text('이 선택은 차량 이용 형태를 기록합니다. 법적 소유권을 증명하지 않습니다.', style: TextStyle(fontSize: 12))),
        TextFormField(controller: odometer, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: '현재 주행거리 km (선택)'), validator: (v) => (v != null && v.isNotEmpty && int.tryParse(v) == null) ? '주행거리는 숫자로 입력해 주세요.' : null),
        if (error != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(error!, style: const TextStyle(color: Colors.red))),
      ])))),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('취소')), FilledButton(onPressed: () async {
        if (!formKey.currentState!.validate()) return;
        try {
          await widget.api.create('vehicles', {
            'model_name': model.text.trim(), 'nickname': nickname.text.trim(), 'generation': generation.text.trim(),
            'plate_number': plate.text.trim(),
            'use_relationship': useRelationship,
            'model_year': year.text.isEmpty ? null : int.parse(year.text),
            'current_odometer_km': odometer.text.isEmpty ? null : int.parse(odometer.text),
          });
          if (dialogContext.mounted) Navigator.pop(dialogContext, true);
        } catch (e) { setDialogState(() => error = e.toString()); }
      }, child: const Text('등록'))],
    )));
    model.dispose(); nickname.dispose(); generation.dispose(); year.dispose(); plate.dispose(); odometer.dispose();
    if (created == true && mounted) reloadVehicles();
  }

  Future<void> editVehiclePlate(Map<String, dynamic> vehicle) async {
    final id = vehicle['id'] as int;
    final plate = TextEditingController(text: (vehicle['plate_number'] ?? '').toString());
    String? error;
    String useRelationship = (vehicle['ownership_relationship'] ?? 'other').toString();
    final saved = await showDialog<bool>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setDialogState) => AlertDialog(
      title: const Text('차량 번호판 등록·변경'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        TextFormField(controller: plate, autofocus: true, textCapitalization: TextCapitalization.characters, decoration: const InputDecoration(labelText: '차량 번호판', hintText: '예: 12가3456')),
        DropdownButtonFormField<String>(initialValue: const ['owned', 'lease', 'rental', 'family', 'other'].contains(useRelationship) ? useRelationship : 'other', decoration: const InputDecoration(labelText: '차량 이용 형태'), items: const [
          DropdownMenuItem(value: 'owned', child: Text('자가 차량')), DropdownMenuItem(value: 'lease', child: Text('리스 차량')),
          DropdownMenuItem(value: 'rental', child: Text('렌트 차량')), DropdownMenuItem(value: 'family', child: Text('가족 차량')),
          DropdownMenuItem(value: 'other', child: Text('기타 이용 차량')),
        ], onChanged: (value) => setDialogState(() => useRelationship = value ?? 'other')),
        const SizedBox(height: 8),
        const Text('번호판 변경 이력은 보관됩니다. 이용 형태 선택은 소유권 증명이 아닙니다.', style: TextStyle(fontSize: 12)),
        if (error != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(error!, style: const TextStyle(color: Colors.red))),
      ]),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('취소')),
        FilledButton(onPressed: () async {
          if (!_isValidKoreanPlate(plate.text)) { setDialogState(() => error = '차량 번호 형식을 확인해 주세요.'); return; }
          try {
            await widget.api.updateVehiclePlate(id, plate.text.trim(), useRelationship);
            if (dialogContext.mounted) Navigator.pop(dialogContext, true);
          } catch (e) { setDialogState(() => error = e.toString().replaceFirst('Exception: ', '')); }
        }, child: const Text('저장')),
      ],
    )));
    plate.dispose();
    if (saved == true && mounted) reloadVehicles();
  }

  Future<void> addLedgerEntry(int vehicleId) async {
    final created = await showDialog<bool>(
      context: context,
      builder: (_) => _LedgerEntryDialog(api: widget.api, vehicleId: vehicleId),
    );
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
                        Text('차량 ${entry.key + 1}', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: selected ? colors.onPrimary.withValues(alpha: .8) : colors.onSurfaceVariant)),
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
              IconButton(onPressed: () => editVehiclePlate(vehicle), tooltip: '차량 번호판 등록·변경', icon: const Icon(Icons.edit_road_outlined)),
              IconButton(onPressed: () => showVehicleQr(vehicle), tooltip: '차량 QR', icon: const Icon(Icons.qr_code_2)),
            ]),
            if (hasFavouredF66Photo(vehicle) || hasMaybachPhoto(vehicle)) VehiclePhoto(vehicle: vehicle, height: 132),
            Text('차량 번호  ${(vehicle['plate_number'] ?? '').toString().isEmpty ? '미등록' : vehicle['plate_number']}', style: const TextStyle(fontWeight: FontWeight.w700)),
            Text('이용 형태  ${_vehicleRelationshipLabel(vehicle['ownership_relationship'])} · 소유권 미확인', style: const TextStyle(fontSize: 12)),
            Text([
              if (vehicle['generation'] != null) vehicle['generation'],
              if (vehicle['model_year'] != null) '${vehicle['model_year']}년형',
              '현재 ${vehicle['current_odometer_km'] == null ? '주행거리 미등록' : '${formatKilometers(vehicle['current_odometer_km'])} km'}',
            ].join(' · '), style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
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
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('차량 이력', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)), TextButton.icon(onPressed: () => addLedgerEntry(vehicleId), icon: const Icon(Icons.add), label: const Text('기록 추가'))]),
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
    const Text('MY', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
    const SizedBox(height: 16),
    InfoCard(text: ApiClient.demoMode
        ? '데모 계정으로 체험 중입니다. 차계부와 알림 변경 사항은 앱을 종료하면 초기화됩니다.'
        : signedIn ? '로그인되어 있습니다. 정비 예정일과 목표 주행거리 알림을 관리할 수 있어요.' : '로그인해 차량을 등록하고 기록을 관리하세요.'),
    const SizedBox(height: 10),
    MembershipSummaryCard(api: api, signedIn: signedIn),
    AttendanceCheckinCard(api: api, signedIn: signedIn, onLogin: onLogin),
    if (signedIn && !ApiClient.demoMode) ...[
      const SizedBox(height: 12),
      BookingListSection(api: api),
    ],
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
            ]),
          )));
        }).toList());
      }),
    const SizedBox(height: 12),
    OutlinedButton.icon(onPressed: onManageVehicles, icon: const Icon(Icons.directions_car_outlined), label: const Text('차량 관리 및 차계부 열기')),
    const SizedBox(height: 8),
    OutlinedButton.icon(onPressed: () => _openCafeNotice(context, naverCafeMobileUrl), icon: const Icon(Icons.open_in_new), label: const Text('네이버 카페 바로가기')),
    const SizedBox(height: 8),
    OutlinedButton.icon(
      onPressed: () => _openCafeNotice(context, partnerInquiryUrl),
      icon: const Icon(Icons.storefront_outlined),
      label: const Text('협력업체 입점 문의'),
    ),
    const SizedBox(height: 8),
    OutlinedButton.icon(onPressed: () => showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('이용약관 · 개인정보 안내'),
      content: const SingleChildScrollView(child: Text('이용약관 (안)\n아이러브미니는 차량 관리, 차계부, 정비 알림, 협력업체 정보 및 커뮤니티 연결 기능을 제공합니다. 이용자는 본인의 차량 및 정비 정보를 정확하게 입력하고 계정 보안을 관리해야 합니다. 업체 정보·가격·혜택은 변경될 수 있으므로 이용 전 업체에 확인해 주세요. 정비 계약 및 작업 결과는 이용자와 해당 업체 사이의 책임입니다.\n\n개인정보 처리 안내 (안)\n서비스 제공 과정에서 계정 식별·로그인 정보, 이용자가 입력한 차량·주행거리·정비 기록·사진·문의 내용, 알림 설정 및 이용 기록을 처리할 수 있습니다. 이용 목적은 회원 확인, 차량 이력 관리, 문의 응대, 선택한 알림 제공, 보안과 서비스 개선입니다. 목적 달성 후 관련 법령상 보존 의무가 있는 경우를 제외하고 파기합니다. 이용자는 본인 정보의 열람·정정·삭제·처리정지를 요청할 수 있습니다.\n\n시제품용 초안입니다. 운영 주체, 실제 데이터 흐름·보관 기간·수탁업체 및 연락처를 정식 출시 전에 확정해 고지해야 합니다.')),
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

class MembershipSummaryCard extends StatefulWidget {
  const MembershipSummaryCard({required this.api, required this.signedIn, super.key});
  final ApiClient api;
  final bool signedIn;
  @override
  State<MembershipSummaryCard> createState() => _MembershipSummaryCardState();
}

class _MembershipSummaryCardState extends State<MembershipSummaryCard> {
  late Future<Map<String, dynamic>> _grade;
  late Future<Map<String, dynamic>> _points;

  @override
  void initState() { super.initState(); _load(); }

  @override
  void didUpdateWidget(covariant MembershipSummaryCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.signedIn != widget.signedIn) _load();
  }

  void _load() {
    _grade = widget.signedIn || ApiClient.demoMode
        ? widget.api.memberGrade()
        : Future.value({'grade_label': '로그인 후 확인'});
    _points = widget.signedIn || ApiClient.demoMode
        ? widget.api.attendanceSummary()
        : Future.value({'balance_points': 0});
  }

  void _showGradeGuide() {
    showDialog<void>(context: context, builder: (context) => AlertDialog(
      title: const Text('회원 등급 안내'),
      content: const Text('''일반회원
기본 가입 회원

미니회원
아이러브미니 운영진이 승인한 MINI 회원

협력업체
등록된 협력업체 담당자'''),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('닫기'))],
    ));
  }

  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Row(children: [
      const Expanded(child: Text('아이러브미니 멤버십', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900))),
      TextButton(onPressed: _showGradeGuide, child: const Text('등급 안내')),
    ]),
    const SizedBox(height: 5),
    FutureBuilder<Map<String, dynamic>>(future: _grade, builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) return const LinearProgressIndicator();
      return Row(children: [
        const Icon(Icons.verified_user_outlined, color: brandRed),
        const SizedBox(width: 8),
        const Text('회원 등급', style: TextStyle(fontWeight: FontWeight.w700)),
        const Spacer(),
        Text((snapshot.data?['grade_label'] ?? '등급 확인 불가').toString(), style: const TextStyle(color: brandRed, fontWeight: FontWeight.w900)),
      ]);
    }),
    const Divider(height: 22),
    Row(children: [
      Expanded(child: FutureBuilder<Map<String, dynamic>>(future: _points, builder: (context, snapshot) {
        final points = (snapshot.data?['balance_points'] as num?)?.toInt() ?? 0;
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('보유 포인트', style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
          const SizedBox(height: 3),
          Text('${formatKilometers(points)} P', style: const TextStyle(fontSize: 19, color: brandRed, fontWeight: FontWeight.w900)),
        ]);
      })),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('쿠폰', style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurfaceVariant)),
        const SizedBox(height: 3),
        const Text('준비 중', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
      ])),
    ]),
  ])));
}

class PartnerBookingPage extends StatefulWidget {
  const PartnerBookingPage({required this.api, required this.partner, super.key});
  final ApiClient api;
  final Map<String, dynamic> partner;
  @override
  State<PartnerBookingPage> createState() => _PartnerBookingPageState();
}

class _PartnerBookingPageState extends State<PartnerBookingPage> {
  final formKey = GlobalKey<FormState>();
  final service = TextEditingController();
  final phone = TextEditingController();
  final note = TextEditingController();
  late DateTime selected;
  List<Map<String, dynamic>> vehicles = [];
  int? selectedVehicleId;
  bool loadingVehicles = true;
  bool busy = false;
  String? error;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    selected = DateTime(now.year, now.month, now.day + 1, 10);
    final cats = (widget.partner['service_categories'] as List? ?? const []).map((e) => e.toString()).toList();
    service.text = cats.isEmpty ? '정비·점검' : cats.first;
    loadVehicles();
  }

  Future<void> loadVehicles() async {
    try {
      final rows = await widget.api.list('vehicles');
      if (!mounted) return;
      setState(() {
        vehicles = rows;
        if (rows.length == 1) selectedVehicleId = rows.first['id'] as int;
        loadingVehicles = false;
      });
    } catch (e) {
      if (mounted) setState(() { loadingVehicles = false; error = e.toString().replaceFirst('Exception: ', ''); });
    }
  }

  Future<void> chooseTime() async {
    final date = await showDatePicker(context: context, initialDate: selected, firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 180)));
    if (date == null || !mounted) return;
    final time = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(selected));
    if (time == null || !mounted) return;
    setState(() => selected = DateTime(date.year, date.month, date.day, time.hour, time.minute));
  }

  Future<void> submit() async {
    if (!formKey.currentState!.validate()) return;
    Map<String, dynamic>? selectedVehicle;
    for (final vehicle in vehicles) {
      if (vehicle['id'] == selectedVehicleId) { selectedVehicle = vehicle; break; }
    }
    if (selectedVehicle == null) { setState(() => error = '예약할 차량을 선택해 주세요.'); return; }
    if ((selectedVehicle['plate_number'] ?? '').toString().trim().isEmpty) { setState(() => error = '선택한 차량의 번호판을 먼저 등록해 주세요.'); return; }
    setState(() { busy = true; error = null; });
    try {
      final payload = <String, dynamic>{
        'partner': widget.partner['id'], 'scheduled_at': selected.toUtc().toIso8601String(),
        'service_type': service.text.trim(), 'contact_phone': phone.text.trim(),
        'customer_note': note.text.trim(),
      };
      payload['vehicle'] = selectedVehicleId;
      await widget.api.createPartnerBooking(payload);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('업체 예약 요청')),
    body: Form(key: formKey, child: ListView(padding: const EdgeInsets.all(20), children: [
      Text([
        widget.partner['name'] ?? '협력업체',
        if ((widget.partner['branch_label'] ?? '').toString().isNotEmpty) widget.partner['branch_label'],
      ].join(' · '), style: Theme.of(context).textTheme.headlineSmall),
      const SizedBox(height: 8),
      const InfoCard(text: '예약 요청을 보내면 업체 담당자가 확인 후 확정하거나 안내를 남깁니다. 예약 확정 전에는 업체와 통화해 주세요.'),
      const SizedBox(height: 16),
      if (loadingVehicles) const LinearProgressIndicator(),
      if (!loadingVehicles && vehicles.isEmpty) const InfoCard(text: '예약 전 MY > 내 차량에서 차량과 번호판을 등록해 주세요.'),
      if (vehicles.isNotEmpty) DropdownButtonFormField<int>(
        initialValue: selectedVehicleId,
        decoration: const InputDecoration(labelText: '예약할 차량 *'),
        items: vehicles.map((row) => DropdownMenuItem<int>(value: row['id'] as int,
          child: Text('${row['model_name'] ?? '내 차량'} · ${row['plate_number'] ?? '번호판 미등록'}'))).toList(),
        onChanged: (value) => setState(() => selectedVehicleId = value),
        validator: (value) => value == null ? '예약할 차량을 선택해 주세요.' : null,
      ),
      const SizedBox(height: 12),
      TextFormField(controller: service, decoration: const InputDecoration(labelText: '방문 목적'), validator: (v) => v?.trim().isNotEmpty == true ? null : '방문 목적을 입력해 주세요.'),
      const SizedBox(height: 12),
      OutlinedButton.icon(onPressed: chooseTime, icon: const Icon(Icons.schedule), label: Text('희망 일시  ${selected.year}-${selected.month.toString().padLeft(2, '0')}-${selected.day.toString().padLeft(2, '0')}  ${selected.hour.toString().padLeft(2, '0')}:${selected.minute.toString().padLeft(2, '0')}')),
      const SizedBox(height: 12),
      TextFormField(controller: phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: '연락처 (선택)', hintText: '업체가 연락할 번호')),
      const SizedBox(height: 12),
      TextFormField(controller: note, maxLines: 3, decoration: const InputDecoration(labelText: '요청사항 (선택)')),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: const TextStyle(color: Colors.red))),
      const SizedBox(height: 18),
      FilledButton(onPressed: busy || loadingVehicles || vehicles.isEmpty ? null : submit, child: Text(busy ? '요청 중…' : '예약 요청 보내기')),
    ])),
  );

  @override
  void dispose() { service.dispose(); phone.dispose(); note.dispose(); super.dispose(); }
}

class BookingListSection extends StatefulWidget {
  const BookingListSection({required this.api, super.key});
  final ApiClient api;
  @override
  State<BookingListSection> createState() => _BookingListSectionState();
}

class _BookingListSectionState extends State<BookingListSection> {
  late Future<List<Map<String, dynamic>>> future;
  void reload() => future = widget.api.list('bookings');
  @override
  void initState() { super.initState(); reload(); }

  Future<void> act(Future<void> Function() action) async {
    try { await action(); if (mounted) setState(reload); }
    catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', '')))); }
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Map<String, dynamic>>>(
    future: future,
    builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) return const LinearProgressIndicator();
      if (snapshot.hasError) return const InfoCard(text: '예약 목록을 불러오지 못했습니다.');
      final rows = (snapshot.data ?? []).where((row) => row['status'] != 'cancelled').toList();
      return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('업체 예약', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
        if (rows.isEmpty) const Padding(padding: EdgeInsets.only(top: 10), child: Text('예약 요청이 없습니다.')),
        ...rows.map((row) {
          final manager = row['can_manage'] == true;
          final owner = row['is_customer'] == true;
          final status = row['status']?.toString() ?? '';
          final date = DateTime.tryParse(row['scheduled_at']?.toString() ?? '')?.toLocal();
          final when = date == null ? '' : '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
          return Column(children: [
            ListTile(contentPadding: EdgeInsets.zero, title: Text([
              (row['partner_name'] ?? '').toString(),
              if ((row['partner_branch_label'] ?? '').toString().isNotEmpty) (row['partner_branch_label'] ?? '').toString(),
              if ((row['partner_region'] ?? '').toString().isNotEmpty) (row['partner_region'] ?? '').toString(),
            ].join(' · '), style: const TextStyle(fontWeight: FontWeight.w800)),
              subtitle: Text('$when · ${row['service_type']} · ${row['status_label']}\n${(row['partner_note'] ?? row['customer_note'] ?? '').toString()}'),
              trailing: owner && (status == 'requested' || status == 'confirmed')
                ? TextButton(onPressed: () => act(() => widget.api.cancelPartnerBooking(row['id'] as int)), child: const Text('취소')) : null),
            if (manager && status == 'requested') Row(mainAxisAlignment: MainAxisAlignment.end, children: [
              TextButton(onPressed: () => act(() => widget.api.respondToPartnerBooking(row['id'] as int, status: 'rejected')), child: const Text('거절')),
              const SizedBox(width: 6),
              FilledButton(onPressed: () => act(() => widget.api.respondToPartnerBooking(row['id'] as int, status: 'confirmed')), child: const Text('예약 확정')),
            ]),
            if (manager && status == 'confirmed') Align(alignment: Alignment.centerRight, child: TextButton.icon(
              onPressed: () => act(() => widget.api.respondToPartnerBooking(row['id'] as int, status: 'completed')),
              icon: const Icon(Icons.check_circle_outline), label: const Text('작업 완료 처리'))),
            if (manager && row['can_verify_records'] == true && status == 'confirmed' &&
                (row['vehicle_plate_number'] ?? '').toString().isNotEmpty)
              Align(alignment: Alignment.centerRight, child: FilledButton.tonalIcon(
                onPressed: () async {
                  final saved = await Navigator.of(context).push<bool>(MaterialPageRoute(builder: (_) => PartnerRecordPage(
                    api: widget.api,
                    initialPlateNumber: row['vehicle_plate_number'].toString(),
                    initialPartnerId: row['partner'] as int?,
                  )));
                  if (saved == true && mounted) setState(reload);
                },
                icon: const Icon(Icons.qr_code_scanner), label: const Text('번호판 확인 후 QR 정비 등록')),
              ),
            const Divider(),
          ]);
        }),
      ])));
    },
  );
}

class PartnerRecordPage extends StatefulWidget {
  const PartnerRecordPage({required this.api, this.initialPlateNumber, this.initialPartnerId, super.key});
  final ApiClient api;
  final String? initialPlateNumber;
  final int? initialPartnerId;
  @override
  State<PartnerRecordPage> createState() => _PartnerRecordPageState();
}

class _PartnerRecordPageState extends State<PartnerRecordPage> {
  final formKey = GlobalKey<FormState>();
  final vehiclePublicId = TextEditingController();
  final plateNumber = TextEditingController();
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
  Map<String, dynamic>? scannedPassport;
  Map<String, dynamic>? matchedVehicle;
  bool plateConfirmed = false;

  Future<void> lookupPlate() async {
    if (!_isValidKoreanPlate(plateNumber.text)) {
      setState(() => error = '차량 번호 형식을 확인해 주세요. 예: 12가3456');
      return;
    }
    setState(() { busy = true; error = null; matchedVehicle = null; plateConfirmed = false; scannedPassport = null; vehiclePublicId.clear(); });
    try {
      final result = await widget.api.lookupVehicleByPlate(plateNumber.text.trim());
      if (!mounted) return;
      setState(() {
        matchedVehicle = Map<String, dynamic>.from(result['vehicle'] as Map);
        plateNumber.text = matchedVehicle!['plate_number'].toString();
      });
    } catch (e) {
      if (mounted) setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> scanVehicle() async {
    final vehicle = matchedVehicle;
    if (vehicle == null) return;
    final confirmed = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('실차 번호판 확인'),
      content: Text('실제 차량 번호판이 ${vehicle['plate_number']}와 같은지 확인해 주세요. 확인 후 해당 차량의 QR을 스캔합니다.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('다시 확인')),
        FilledButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('번호판 확인 · QR 스캔')),
      ],
    ));
    if (confirmed != true || !mounted) return;
    setState(() { plateConfirmed = true; error = null; scannedPassport = null; vehiclePublicId.clear(); });
    final scanned = await Navigator.of(context).push<String>(MaterialPageRoute(builder: (_) => const ScanVehicleQrPage()));
    if (scanned != null && mounted) {
      setState(() { vehiclePublicId.text = scanned; scannedPassport = null; error = null; });
      try {
        final passport = await widget.api.scanVehiclePassport(scanned, plateNumber.text.trim());
        if (!mounted) return;
        final scannedVehicle = Map<String, dynamic>.from(passport['vehicle'] as Map);
        if (scannedVehicle['public_id'] != vehicle['public_id'] || scannedVehicle['plate_number'] != vehicle['plate_number']) {
          setState(() { plateConfirmed = false; vehiclePublicId.clear(); error = '번호판 조회 결과와 QR 차량이 일치하지 않습니다.'; });
          return;
        }
        setState(() => scannedPassport = passport);
      } catch (e) {
        if (mounted) setState(() { plateConfirmed = false; vehiclePublicId.clear(); error = e.toString().replaceFirst('Exception: ', ''); });
      }
    }
  }

  @override
  void initState() {
    super.initState();
    workplaces = widget.api.list('partners/my-workplaces');
    partnerId = widget.initialPartnerId;
    if (widget.initialPlateNumber != null) {
      plateNumber.text = widget.initialPlateNumber!;
      WidgetsBinding.instance.addPostFrameCallback((_) { if (mounted) lookupPlate(); });
    }
  }

  Future<void> submit() async {
    if (!formKey.currentState!.validate() || partnerId == null || !plateConfirmed || scannedPassport == null) {
      setState(() => error = partnerId == null ? '인증 권한이 있는 협력업체를 선택해 주세요.' : '차량 번호 확인 후 일치하는 QR을 스캔해 주세요.');
      return;
    }
    setState(() { busy = true; error = null; });
    try {
      await widget.api.createPartnerVerifiedRecord({
        'vehicle_public_id': vehiclePublicId.text.trim(),
        'plate_number': plateNumber.text.trim(),
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
        partnerId ??= widget.initialPartnerId ?? partners.first['id'] as int;
      return Form(key: formKey, child: ListView(padding: const EdgeInsets.all(20), children: [
          const InfoCard(text: '① 차량 번호를 조회해 실차 번호판을 확인합니다. ② 확인 버튼을 누르고 같은 차량에 부착된 QR을 스캔합니다. 두 차량 정보가 일치해야 인증기록을 등록할 수 있습니다.'),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            initialValue: partnerId,
            decoration: const InputDecoration(labelText: '협력업체'),
            items: partners.map((row) => DropdownMenuItem<int>(value: row['id'] as int, child: Text(row['name'].toString()))).toList(),
            onChanged: (value) => setState(() => partnerId = value),
          ),
          TextFormField(controller: plateNumber, textCapitalization: TextCapitalization.characters, decoration: const InputDecoration(labelText: '차량 번호판 *', hintText: '예: 12가3456'), onChanged: (_) => setState(() { matchedVehicle = null; plateConfirmed = false; scannedPassport = null; vehiclePublicId.clear(); error = null; }), validator: (value) => _isValidKoreanPlate(value) ? null : '차량 번호를 확인해 주세요.'),
          const SizedBox(height: 8),
          OutlinedButton.icon(onPressed: busy ? null : lookupPlate, icon: const Icon(Icons.search), label: Text(busy ? '차량 확인 중…' : '차량 번호 조회')),
          if (matchedVehicle != null) ...[
            const SizedBox(height: 8),
            Card(child: ListTile(
              leading: const Icon(Icons.directions_car_filled_outlined),
              title: Text(matchedVehicle!['plate_number'].toString(), style: const TextStyle(fontWeight: FontWeight.w900)),
              subtitle: Text('${matchedVehicle!['model_name'] ?? '차종 미등록'} · ${(matchedVehicle!['generation'] ?? '').toString()}'),
            )),
            FilledButton.icon(onPressed: scanVehicle, icon: const Icon(Icons.qr_code_scanner), label: const Text('실차 번호판 확인 · QR 스캔')),
          ],
          TextFormField(controller: vehiclePublicId, readOnly: true, decoration: const InputDecoration(labelText: '차량 QR 확인 결과 *'), validator: (value) => value?.trim().isNotEmpty == true ? null : '번호판 확인 후 QR을 스캔해 주세요.'),
          if (scannedPassport != null) ...[
            const SizedBox(height: 8),
            InfoCard(text: '${(scannedPassport!['vehicle'] as Map)['plate_number']} · ${(scannedPassport!['vehicle'] as Map)['model_name']} · 기존 차량 이력 ${(scannedPassport!['history'] as List).length}건을 확인했습니다.'),
          ],
          DropdownButtonFormField<String>(initialValue: kind, decoration: const InputDecoration(labelText: '작업 종류'), items: const [
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
    vehiclePublicId.dispose(); plateNumber.dispose(); description.dispose(); odometer.dispose(); amount.dispose(); partNumber.dispose(); evidenceUrl.dispose(); corrects.dispose(); correctionReason.dispose();
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
