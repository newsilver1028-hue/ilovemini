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
            IconButton(visualDensity: VisualDensity.compact, tooltip: paused ? '자동 넘김 재생' : '자동 넘김 일시정지', onPressed: