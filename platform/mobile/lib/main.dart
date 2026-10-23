import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:app_links/app_links.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:local_auth/local_auth.dart';
import 'package:image_picker/image_picker.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'api_client.dart';
import 'admin_managed_widgets.dart';
import 'app_refresh.dart';
import 'maintenance_requests.dart';
import 'vehicle_catalog_picker.dart';
import 'vehicle_photo_support.dart';
import 'brand_loading.dart';
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
    await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform);
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
  final normalized =
      (value ?? '').replaceAll(RegExp(r'[\s-]+'), '').toUpperCase();
  return RegExp(r'^(?:[가-힣]{1,2})?\d{2,3}[가-힣]\d{4}$').hasMatch(normalized);
}

String _vehicleRelationshipLabel(dynamic value) => switch (value?.toString()) {
      'owned' => '자가 차량',
      'lease' => '리스 차량',
      'rental' => '렌트 차량',
      'family' => '가족 차량',
      'other' => '기타 이용 차량',
      _ => '미선택',
    };

const favouredF66PhotoAsset = 'assets/images/mini_f66_favoured_red.png';
const maybachS580FrontAsset = 'assets/images/maybach-s580-front.webp';
const naverCafeMobileUrl = 'https://m.cafe.naver.com/minilover/';
const partnerInquiryUrl = 'https://naver.me/xTb4h7ZR';
const recommendedCafeItems = <Map<String, String>>[
  {
    'title': '차량용 거치대',
    'detail': '차량용 스마트폰 거치 아이템 · 호환 정보 확인 중',
    'image': 'assets/images/mini-recommended-items/item-01-phone-holder.png'
  },
  {
    'title': '실내 고정 브래킷',
    'detail': '실내 고정용 부품 · 적용 차종 확인 중',
    'image':
        'assets/images/mini-recommended-items/item-02-interior-brackets.png'
  },
  {
    'title': '프런트 그릴 파츠',
    'detail': '외장 그릴 부품 · 적용 차종 확인 중',
    'image': 'assets/images/mini-recommended-items/item-03-grille-parts.png'
  },
  {
    'title': '기어 노브·부츠',
    'detail': '수동 기어 노브와 부츠 · 적용 차종 확인 중',
    'image': 'assets/images/mini-recommended-items/item-04-shift-knob.png'
  },
];

const shoppingBenefitFallback = <Map<String, String>>[
  {
    'title': '도이치모터스 MINI 시승 안내',
    'detail': '전시장별 시승 차량은 전시장에 문의 후 방문해 주세요.',
    'asset_key': 'partner-deutsch',
  },
  {
    'title': '프린트랩 수입차 부품 안내',
    'detail': '수입차 부품 조회와 자가 정비 상담 안내',
    'asset_key': 'partner-printtrap',
  },
];

const malautoRecommendedProducts = <Map<String, dynamic>>[
  {
    'title': '핸드폰 거치대 집게 미니쿠퍼 악세사리',
    'description':
        '말자동차 미니쿠퍼 거치대의 집게 부분만 별도로 교체할 수 있는 상품입니다. 최대 거치 사이즈 약 8.5cm.',
    'image_url':
        'https://ecimg.cafe24img.com/pg2312b83362846015/horsecar/web/product/big/shop1_9b6837d54af746332403145b475b4b7d.jpg',
    'action_url':
        'https://horsecar.co.kr/product/%ED%95%B8%EB%93%9C%ED%8F%B0-%EA%B1%B0%EC%B9%98%EB%8C%80-%EC%A7%91%EA%B2%8C-%EB%AF%B8%EB%8B%88%EC%BF%A0%ED%8D%BC-%EC%95%85%EC%84%B8%EC%82%AC%EB%A6%AC/1092/',
  },
  {
    'title': 'MAL 가죽 키커버 키케이스 키링 미니쿠퍼 악세사리 용품 8종',
    'description': '8가지 디자인 중 선택하는 MINI 키커버와 키링 액세서리입니다.',
    'image_url':
        'https://ecimg.cafe24img.com/pg2312b83362846015/horsecar/web/product/big/shop1_045ec67df92378c27448432f77e786a4.jpg',
    'action_url':
        'https://horsecar.co.kr/product/detail.html?cate_no=117&display_group=1&product_no=2948',
  },
  {
    'title': '미니카 실리콘 모형 스위치 버튼링 미니쿠퍼 악세사리 용품',
    'description': '미니카 모양의 실리콘 스위치 버튼링으로 MINI 실내에 포인트를 더해 줍니다.',
    'image_url':
        'https://ecimg.cafe24img.com/pg2312b83362846015/horsecar/web/product/big/shop1_e9d3d3e6d20e6ef4b6b729890bda0fb5.jpg',
    'action_url':
        'https://horsecar.co.kr/product/%EB%AF%B8%EB%8B%88%EC%B9%B4-%EC%8B%A4%EB%A6%AC%EC%BD%98-%EB%AA%A8%ED%98%95-%EC%8A%A4%EC%9C%84%EC%B9%98-%EB%B2%84%ED%8A%BC%EB%A7%81-%EB%AF%B8%EB%8B%88%EC%BF%A0%ED%8D%BC-%EC%95%85%EC%84%B8%EC%82%AC%EB%A6%AC-%EC%9A%A9%ED%92%88/1879/',
  },
  {
    'title': '자동차 먼지떨이 차량용 먼지털이개 미니쿠퍼 악세사리 용품',
    'description': '차량 실내 먼지를 가볍게 털어내는 미니쿠퍼 액세서리용 먼지털이개입니다.',
    'image_url':
        'https://ecimg.cafe24img.com/pg2312b83362846015/horsecar/web/product/big/shop1_516d2cca7351f8976f08fc7fde7b1c4b.jpg',
    'action_url':
        'https://horsecar.co.kr/product/%EC%9E%90%EB%8F%99%EC%B0%A8-%EB%A8%BC%EC%A7%80%EB%96%A8%EC%9D%B4-%EC%B0%A8%EB%9F%89%EC%9A%A9-%EB%A8%BC%EC%A7%80%ED%84%B8%EC%9D%B4%EA%B0%9C-%EB%AF%B8%EB%8B%88%EC%BF%A0%ED%8D%BC-%EC%95%85%EC%84%B8%EC%82%AC%EB%A6%AC-%EC%9A%A9%ED%92%88/1119',
  },
];

const malautoGroupbuyProducts = <Map<String, dynamic>>[
  {
    'title': '[세일] 패턴 가죽 컵홀더 컵받침 패드 F55 F56 F57 미니쿠퍼 악세사리',
    'description':
        'F55·F56·F57용 패턴 가죽 컵받침 패드입니다. 말자동차 상품 페이지에서 디자인 옵션을 확인할 수 있습니다.',
    'image_url':
        'https://ecimg.cafe24img.com/pg2312b83362846015/horsecar/web/product/big/shop1_55e582e3eeb83c01de7418688fc39313.jpg',
    'action_url':
        'https://horsecar.co.kr/product/%EC%84%B8%EC%9D%BC-%ED%8C%A8%ED%84%B4-%EA%B0%80%EC%A3%BD-%EC%BB%B5%ED%99%80%EB%8D%94-%EC%BB%B5%EB%B0%9B%EC%B9%A8-%ED%8C%A8%EB%93%9C-f55-f56-f57-%EB%AF%B8%EB%8B%88%EC%BF%A0%ED%8D%BC-%EC%95%85%EC%84%B8%EC%82%AC%EB%A6%AC/2084/',
  },
  {
    'title': '[세일] 미니 윙 컬러블럭 아이스티 머그 60주년 미니쿠퍼 순정품 악세사리',
    'description':
        'MINI 60주년 기념 미니 윙 컬러블럭 아이스티 머그입니다. 색상과 판매 상태는 상품 페이지에서 확인해 주세요.',
    'image_url':
        'https://ecimg.cafe24img.com/pg2312b83362846015/horsecar/web/product/big/20260923/96f968d6409ee4524f7b2fb7c4aa0ecf.jpg',
    'action_url':
        'https://horsecar.co.kr/product/detail.html?cate_no=1&display_group=15&product_no=1404',
  },
];

const iloveMiniCafeNotices = <Map<String, String>>[
  {
    'title': '[추석 이벤트] 우리 가족 자동차 자랑대회 🧧',
    'category': '추석 이벤트',
    'url': 'https://m.site.naver.com/2hkWt'
  },
  {
    'title': '6WB 디지털계기판 리콜가능성이 보일수도...',
    'category': 'MINI 차량 정보',
    'url': 'https://m.site.naver.com/2hkX3'
  },
  {
    'title': '9월에 어디 가지? 전국 가을 축제 드라이브 지도!',
    'category': '드라이브 정보',
    'url': 'https://m.site.naver.com/2hkX5'
  },
  {
    'title': '드라이아이스 에바클리닝+에어컨 필터 교체 이벤트!',
    'category': '협력업체 이벤트',
    'url': 'https://m.site.naver.com/2hkX7'
  },
  {
    'title': '[이벤트] 여름의 끝자락, 시원한 혜택은 계속! KUMHO:T SUMMER PROMOTION',
    'category': '타이어 프로모션',
    'url': 'https://m.site.naver.com/2hkXc'
  },
  {
    'title': '협력업체 군팩토리 카오디오 이벤트 START!',
    'category': '협력업체 이벤트',
    'url': 'https://m.site.naver.com/2hkXh'
  },
  {
    'title': '락업클러치 이상으로 인한 미션교체 대상(보증기간은 지난상황)',
    'category': '정비 정보',
    'url': 'https://naver.me/FlBvjooR'
  },
  {
    'title': '🏆 아이러브미니 공식랭킹 - 실시간 업데이트 (2026. 08. 31) 🏆',
    'category': '공식 랭킹',
    'url': 'https://m.site.naver.com/2hkXs'
  },
  {
    'title': '코스텔 충전기 사용하시는분들 참고하세요~',
    'category': '전기차 정보',
    'url': 'https://naver.me/G6RXgbZY'
  },
  {
    'title': '셀프 세차 중 잠금 이슈(+미니코리아 답변)',
    'category': '사용자 정보',
    'url': 'https://m.site.naver.com/2hkXw'
  },
  {
    'title': '신입등급일 때 등업이나 스티커 신청 시 유의할 점(신입이 적은 글)',
    'category': '카페 이용 안내',
    'url': 'https://naver.me/GGGDgrEP'
  },
];

Future<void> _openCafeNotice(BuildContext context, String url) async {
  final uri = Uri.tryParse(url);
  try {
    if (uri == null ||
        uri.scheme != 'https' ||
        uri.host.isEmpty ||
        !await launchUrl(uri,
            mode: LaunchMode.externalApplication,
            webOnlyWindowName: '_top')) throw Exception();
  } catch (_) {
    if (context.mounted)
      ScaffoldMessenger.of(context).showSnackBar(
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
      if (rest.isNotEmpty)
        Card(
            clipBehavior: Clip.antiAlias,
            child: ExpansionTile(
              leading: const Icon(Icons.expand_more),
              title: const Text('나머지 공지 보기',
                  style: TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text('${rest.length}건'),
              children:
                  rest.map((notice) => CafeNoticeTile(notice: notice)).toList(),
            )),
    ]);
  }
}

const partnerBanners = <Map<String, String>>[
  {
    'asset': 'assets/images/partner-square-kumho.png',
    'alt': '금호타이어와 타이어프로의 아이러브미니 제휴 회원 이벤트',
    'url': 'https://m.site.naver.com/2hkXc'
  },
  {
    'asset': 'assets/images/partner-square-deutsch.png',
    'alt': '도이치모터스 MINI 전시장 전차종 시승 안내'
  },
  {
    'asset': 'assets/images/partner-square-printtrap.png',
    'alt': '프린트랩 수입차 부품과 자가 정비 지원 안내'
  },
];

class AffiliateBannerCarousel extends StatefulWidget {
  const AffiliateBannerCarousel({super.key});
  @override
  State<AffiliateBannerCarousel> createState() =>
      _AffiliateBannerCarouselState();
}

class _AffiliateBannerCarouselState extends State<AffiliateBannerCarousel> {
  static const _bannerCount = 3;
  final PageController _controller = PageController(initialPage: 1);
  Timer? _timer;
  int currentPage = 1;
  bool paused = false;

  int get logicalPage => currentPage <= 0
      ? _bannerCount
      : currentPage > _bannerCount
          ? 1
          : currentPage;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _timer?.cancel();
    if (paused) return;
    _timer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (mounted && _controller.hasClients)
        _controller.nextPage(
            duration: const Duration(milliseconds: 360),
            curve: Curves.easeOutCubic);
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
    if (url != null)
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
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
      const SectionHeading(title: '제휴 배너', subtitle: '카페 제휴 소식'),
      const SizedBox(height: 9),
      ClipRRect(
          borderRadius: BorderRadius.circular(14),
          child: SizedBox(
              height: width,
              child: Stack(children: [
                PageView.builder(
                  controller: _controller,
                  itemCount: _bannerCount + 2,
                  onPageChanged: _onPageChanged,
                  itemBuilder: (context, page) {
                    final index = page == 0
                        ? _bannerCount - 1
                        : page == _bannerCount + 1
                            ? 0
                            : page - 1;
                    final banner = partnerBanners[index];
                    final image = Image.asset(banner['asset']!,
                        width: width,
                        height: width,
                        fit: BoxFit.cover,
                        semanticLabel: banner['alt']);
                    final url = banner['url'];
                    return url == null
                        ? image
                        : Semantics(
                            button: true,
                            label: '${banner['alt']} 자세히 보기',
                            child: InkWell(
                                onTap: () => _openBanner(banner),
                                child: image));
                  },
                ),
                Positioned(
                    right: 9,
                    bottom: 9,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                          color: const Color(0xC7191A1E),
                          borderRadius: BorderRadius.circular(24)),
                      child: Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 5, vertical: 3),
                          child: Row(mainAxisSize: MainAxisSize.min, children: [
                            IconButton(
                                visualDensity: VisualDensity.compact,
                                tooltip: '이전 배너',
                                onPressed: () => _controller.previousPage(
                                    duration: const Duration(milliseconds: 280),
                                    curve: Curves.easeOut),
                                icon: const Icon(Icons.chevron_left,
                                    color: Colors.white, size: 20)),
                            Text('$logicalPage / $_bannerCount',
                                style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w800)),
                            IconButton(
                                visualDensity: VisualDensity.compact,
                                tooltip: '다음 배너',
                                onPressed: () => _controller.nextPage(
                                    duration: const Duration(milliseconds: 280),
                                    curve: Curves.easeOut),
                                icon: const Icon(Icons.chevron_right,
                                    color: Colors.white, size: 20)),
                            IconButton(
                                visualDensity: VisualDensity.compact,
                                tooltip: paused ? '자동 넘김 재생' : '자동 넘김 일시정지',
                                onPressed: () {
                                  setState(() => paused = !paused);
                                  if (paused) {
                                    _timer?.cancel();
                                  } else {
                                    _startTimer();
                                  }
                                },
                                icon: Icon(
                                    paused ? Icons.play_arrow : Icons.pause,
                                    color: Colors.white,
                                    size: 18)),
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
          const Padding(
              padding: EdgeInsets.fromLTRB(4, 0, 4, 12),
              child: Text('제목을 누르면 아이러브미니 카페 원문이 열립니다.')),
          ...iloveMiniCafeNotices
              .map((notice) => CafeNoticeTile(notice: notice)),
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
          leading: CircleAvatar(
              backgroundColor: pinned
                  ? const Color(0xFFFBECEF)
                  : Theme.of(context).colorScheme.primaryContainer,
              child: Icon(
                  pinned ? Icons.push_pin_outlined : Icons.campaign_outlined,
                  color: pinned ? brandRed : null)),
          title: Text(notice['title'] ?? '',
              style: const TextStyle(fontWeight: FontWeight.w700)),
          subtitle: Text('${notice['category'] ?? '카페 공지'} · 원문 열기'),
          trailing: pinned
              ? const Chip(label: Text('필독'))
              : const Icon(Icons.open_in_new),
          onTap: () => _openCafeNotice(context, notice['url'] ?? ''),
        ),
      );
}

bool hasFavouredF66Photo(Map<String, dynamic> vehicle) {
  final generation = '${vehicle['generation'] ?? ''}'.toLowerCase();
  final identity =
      '${vehicle['model_name'] ?? ''} ${vehicle['trim'] ?? ''}'.toLowerCase();
  final isF66 = generation.contains('f66') || generation.contains('4세대');
  final isFavoured = identity.contains('favoured') || identity.contains('페이버드');
  return isF66 && isFavoured;
}

const miniVehiclePhotoAssets = <String, String>{
  'R50': 'assets/images/mini-vehicles/mini_cooper_3door_r50.webp',
  'R53': 'assets/images/mini-vehicles/mini_cooper_3door_r53.webp',
  'R56': 'assets/images/mini-vehicles/mini_cooper_3door_r56.webp',
  'F56': 'assets/images/mini-vehicles/mini_cooper_3door_f56.webp',
  'F66': 'assets/images/mini-vehicles/mini_cooper_3door_f66.webp',
  'F55': 'assets/images/mini-vehicles/mini_cooper_5door_f55.webp',
  'F65': 'assets/images/mini-vehicles/mini_cooper_5door_f65.webp',
  'F56 SE': 'assets/images/mini-vehicles/mini_cooper_electric_f56se.webp',
  'J01': 'assets/images/mini-vehicles/mini_cooper_electric_j01.webp',
  'R52': 'assets/images/mini-vehicles/mini_convertible_r52.webp',
  'R57': 'assets/images/mini-vehicles/mini_convertible_r57.webp',
  'F57': 'assets/images/mini-vehicles/mini_convertible_f57.webp',
  'F67': 'assets/images/mini-vehicles/mini_convertible_f67.webp',
  'R55': 'assets/images/mini-vehicles/mini_clubman_r55.webp',
  'F54': 'assets/images/mini-vehicles/mini_clubman_f54.webp',
  'R60': 'assets/images/mini-vehicles/mini_countryman_r60.webp',
  'F60': 'assets/images/mini-vehicles/mini_countryman_f60.webp',
  'U25': 'assets/images/mini-vehicles/mini_countryman_u25.webp',
  'J05': 'assets/images/mini-vehicles/mini_aceman_j05.webp',
  'R61': 'assets/images/mini-vehicles/mini_paceman_r61.webp',
  'R58': 'assets/images/mini-vehicles/mini_coupe_r58.webp',
  'R59': 'assets/images/mini-vehicles/mini_roadster_r59.webp',
  'CLASSIC': 'assets/images/mini-vehicles/mini_classic.webp',
};

String? miniVehiclePhotoAsset(Map<String, dynamic> vehicle) {
  final generation = '${vehicle['generation'] ?? ''}'.toUpperCase().trim();
  for (final code in miniVehiclePhotoAssets.keys.toList()
    ..sort((a, b) => b.length.compareTo(a.length))) {
    if (generation.contains(code)) return miniVehiclePhotoAssets[code];
  }
  final name =
      '${vehicle['model_name'] ?? ''} ${vehicle['trim'] ?? ''}'.toLowerCase();
  if (!(name.contains('mini') || name.contains('미니')) && generation.isEmpty)
    return null;
  if (name.contains('클래식') || name.contains('classic'))
    return miniVehiclePhotoAssets['CLASSIC'];
  if (name.contains('에이스맨') || name.contains('aceman'))
    return miniVehiclePhotoAssets['J05'];
  if (name.contains('페이스맨') || name.contains('paceman'))
    return miniVehiclePhotoAssets['R61'];
  if (name.contains('로드스터') || name.contains('roadster'))
    return miniVehiclePhotoAssets['R59'];
  if (name.contains('쿠페') || name.contains('coupe'))
    return miniVehiclePhotoAssets['R58'];
  if (name.contains('컨버터블') || name.contains('convertible'))
    return miniVehiclePhotoAssets['F67'];
  if (name.contains('클럽맨') || name.contains('clubman'))
    return miniVehiclePhotoAssets['F54'];
  if (name.contains('컨트리맨') || name.contains('countryman'))
    return miniVehiclePhotoAssets['U25'];
  if (name.contains('전기') || name.contains('electric') || name.contains(' se'))
    return miniVehiclePhotoAssets['J01'];
  if (name.contains('5도어') || name.contains('5-door'))
    return miniVehiclePhotoAssets['F65'];
  if (name.contains('3도어') || name.contains('cooper') || name.contains('쿠퍼'))
    return miniVehiclePhotoAssets['F66'];
  return null;
}

bool hasMiniVehiclePhoto(Map<String, dynamic> vehicle) =>
    miniVehiclePhotoAsset(vehicle) != null;

String? bmwVehiclePhotoAsset(Map<String, dynamic> vehicle) {
  final name =
      '${vehicle['model_name'] ?? ''} ${vehicle['trim'] ?? ''}'.toLowerCase();
  if (!name.contains('bmw')) return null;
  if (RegExp(r'\bix\d*').hasMatch(name)) {
    return 'assets/images/bmw-vehicles/bmw-electric-suv-ix3.jpg';
  }
  final isSuv = RegExp(r'\b(?:x\s?\d|xm|ix\d*)\b').hasMatch(name);
  return isSuv
      ? 'assets/images/bmw-vehicles/bmw-suv-x5-2024.jpg'
      : 'assets/images/bmw-vehicles/bmw-sedan-5-series-2024.jpg';
}

bool hasBmwVehiclePhoto(Map<String, dynamic> vehicle) =>
    bmwVehiclePhotoAsset(vehicle) != null;

bool hasMaybachPhoto(Map<String, dynamic> vehicle) =>
    '${vehicle['model_name'] ?? ''} ${vehicle['trim'] ?? ''}'
        .toLowerCase()
        .contains('maybach');

class VehiclePhoto extends StatefulWidget {
  const VehiclePhoto({required this.vehicle, this.height = 118, super.key});
  final Map<String, dynamic> vehicle;
  final double height;

  @override
  State<VehiclePhoto> createState() => _VehiclePhotoState();
}

class _VehiclePhotoState extends State<VehiclePhoto> {
  late Future<File?> _customPhoto;

  String? get _plate => widget.vehicle['plate_number']?.toString();

  @override
  void initState() {
    super.initState();
    _customPhoto = VehiclePhotoStorage.forPlate(_plate);
  }

  @override
  void didUpdateWidget(covariant VehiclePhoto oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.vehicle['plate_number'] != widget.vehicle['plate_number']) {
      _customPhoto = VehiclePhotoStorage.forPlate(_plate);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<File?>(
        future: _customPhoto,
        builder: (context, snapshot) {
          final file = snapshot.data;
          if (file != null) {
            return SizedBox(
                height: widget.height,
                width: double.infinity,
                child: Image.file(file,
                    fit: BoxFit.contain,
                    alignment: Alignment.center,
                    errorBuilder: (_, __, ___) => _fallback(context)));
          }
          return _builtInPhoto(context);
        });
  }

  Widget _builtInPhoto(BuildContext context) {
    if (hasMaybachPhoto(widget.vehicle)) {
      return SizedBox(
          height: widget.height,
          width: double.infinity,
          child: Image.asset(
            maybachS580FrontAsset,
            fit: BoxFit.contain,
            alignment: Alignment.center,
            semanticLabel: 'Mercedes-Maybach S 580 차량 전면',
            errorBuilder: (_, __, ___) => _fallback(context),
          ));
    }
    final asset = hasFavouredF66Photo(widget.vehicle)
        ? favouredF66PhotoAsset
        : miniVehiclePhotoAsset(widget.vehicle) ??
            bmwVehiclePhotoAsset(widget.vehicle);
    if (asset == null) return _fallback(context);
    return SizedBox(
        height: widget.height,
        width: double.infinity,
        child: Image.asset(
          asset,
          fit: BoxFit.contain,
          alignment: Alignment.center,
          semanticLabel:
              asset.contains('/bmw-vehicles/') ? 'BMW 차량 사진' : 'MINI 차량 사진',
          errorBuilder: (_, __, ___) => _fallback(context),
        ));
  }

  Widget _fallback(BuildContext context) => SizedBox(
      height: widget.height,
      width: double.infinity,
      child: Center(
          child: Icon(Icons.directions_car_filled,
              size: widget.height * .55,
              color: Theme.of(context).colorScheme.onSurfaceVariant)));
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
          locale: const Locale('ko', 'KR'),
          supportedLocales: const [Locale('ko', 'KR')],
          localizationsDelegates: GlobalMaterialLocalizations.delegates,
          debugShowCheckedModeBanner: false,
          scaffoldMessengerKey: scaffoldMessengerKey,
          theme: _appTheme(Brightness.light),
          darkTheme: _appTheme(Brightness.dark),
          themeMode: mode,
          builder: (context, child) {
            final media = MediaQuery.of(context);
            return MediaQuery(
              data: media.copyWith(
                textScaler: responsiveTextScalerForWidth(
                  media.textScaler,
                  media.size.width,
                ),
              ),
              child: child ?? const SizedBox.shrink(),
            );
          },
          home: const SeasonLaunch(home: MainShell()),
        ),
      );
}

/// Modestly adapts default typography to narrow phones and wider screens.
/// The operating system's accessibility text scale always takes precedence.
double responsiveTextScaleForWidth(double logicalWidth) {
  if (!logicalWidth.isFinite || logicalWidth <= 0) return 1;
  return (logicalWidth / 390).clamp(0.94, 1.06).toDouble();
}

TextScaler responsiveTextScalerForWidth(
  TextScaler systemScaler,
  double logicalWidth,
) {
  final hasAccessibilityScale = (systemScaler.scale(12) - 12).abs() > 0.1 ||
      (systemScaler.scale(16) - 16).abs() > 0.1 ||
      (systemScaler.scale(24) - 24).abs() > 0.1;
  if (hasAccessibilityScale) return systemScaler;
  final widthScale = responsiveTextScaleForWidth(logicalWidth);
  return widthScale == 1
      ? systemScaler
      : _WidthAdjustedTextScaler(systemScaler, widthScale);
}

class _WidthAdjustedTextScaler extends TextScaler {
  const _WidthAdjustedTextScaler(this.systemScaler, this.widthScale);

  final TextScaler systemScaler;
  final double widthScale;

  @override
  double scale(double fontSize) => systemScaler.scale(fontSize) * widthScale;

  @override
  double get textScaleFactor => scale(14) / 14;

  @override
  bool operator ==(Object other) =>
      other is _WidthAdjustedTextScaler &&
      other.systemScaler == systemScaler &&
      other.widthScale == widthScale;

  @override
  int get hashCode => Object.hash(systemScaler, widthScale);
}

ThemeData _appTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;
  final background = isDark ? const Color(0xFF191A1E) : paper;
  final surface = isDark ? const Color(0xFF25262C) : Colors.white;
  final text = isDark ? const Color(0xFFF3F3F5) : ink;
  final muted = isDark ? const Color(0xFFB2B3BC) : const Color(0xFF686B73);
  final accent = brandRed;
  final border = isDark ? const Color(0xFF3B3D44) : const Color(0xFFDFE0E4);
  final scheme =
      ColorScheme.fromSeed(seedColor: brandRed, brightness: brightness)
          .copyWith(
    primary: accent,
    onPrimary: Colors.white,
    primaryContainer:
        isDark ? const Color(0xFF3D282E) : const Color(0xFFFBECEF),
    onPrimaryContainer: accent,
    surface: surface,
    onSurface: text,
    onSurfaceVariant: muted,
    outline: border,
    outlineVariant: border,
    secondaryContainer:
        isDark ? const Color(0xFF303137) : const Color(0xFFECECEF),
    onSecondaryContainer: text,
  );
  final shape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(14), side: BorderSide(color: border));
  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    scaffoldBackgroundColor: background,
    colorScheme: scheme,
    dividerColor: border,
    appBarTheme: AppBarTheme(
        backgroundColor: background,
        foregroundColor: text,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        toolbarHeight: 74),
    cardTheme: CardThemeData(
        color: surface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        margin: const EdgeInsets.symmetric(vertical: 5),
        shape: shape),
    navigationBarTheme: NavigationBarThemeData(
        backgroundColor: background,
        surfaceTintColor: Colors.transparent,
        indicatorColor: Colors.transparent,
        iconTheme: WidgetStateProperty.resolveWith((states) => IconThemeData(
            color: states.contains(WidgetState.selected) ? brandRed : muted)),
        labelTextStyle: WidgetStateProperty.resolveWith((states) => TextStyle(
            color: states.contains(WidgetState.selected) ? brandRed : muted,
            fontSize: 12)),
        height: 76),
    inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: border)),
        enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: border)),
        focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: accent, width: 2))),
    filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
            minimumSize: const Size(44, 46),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10)))),
    outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
            minimumSize: const Size(44, 46),
            foregroundColor: text,
            side: BorderSide(color: border),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10)))),
    dialogTheme: DialogThemeData(
        backgroundColor: background,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22))),
    bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: background, surfaceTintColor: Colors.transparent),
  );
}

Future<void> showVehiclePassportQr(
    BuildContext context, Map<String, dynamic> vehicle) async {
  final publicId = vehicle['public_id']?.toString() ??
      (ApiClient.demoMode ? 'demo-${vehicle['id']}' : null);
  if (publicId == null || publicId.isEmpty) {
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('차량 QR 정보를 불러오지 못했습니다.')));
    return;
  }
  final localAuth = LocalAuthentication();
  try {
    if (!await localAuth.isDeviceSupported()) {
      if (context.mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('이 기기에서 화면 잠금 인증을 사용할 수 없어 QR을 열지 않았어요.')),
        );
      return;
    }
    final authenticated = await localAuth.authenticate(
      localizedReason: '차량 QR을 표시하려면 Face ID, 지문 또는 기기 잠금으로 인증해 주세요.',
      options: const AuthenticationOptions(biometricOnly: false),
    );
    if (!authenticated) {
      if (context.mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('인증이 완료되지 않아 QR을 열지 않았어요.')),
        );
      return;
    }
  } catch (_) {
    if (context.mounted)
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('기기 인증을 사용할 수 없습니다. Face ID·지문 또는 화면 잠금을 설정해 주세요.')),
      );
    return;
  }
  final data = 'ilovemini://vehicle/$publicId';
  await showModalBottomSheet<void>(
    context: context,
    showDragHandle: true,
    isScrollControlled: false,
    builder: (sheetContext) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('ILOVEMINI MEMBERSHIP',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          const SizedBox(height: 20),
          QrImageView(data: data, size: 220, backgroundColor: Colors.white),
          const SizedBox(height: 16),
          const Text('승인된 협력업체 담당자에게 이 QR을 보여주세요.',
              textAlign: TextAlign.center),
          const SizedBox(height: 8),
          TextButton(
              onPressed: () => Navigator.pop(sheetContext),
              child: const Text('닫기')),
        ]),
      ),
    ),
  );
}

class MainShell extends StatefulWidget {
  const MainShell({this.api, super.key});
  final ApiClient? api;
  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> with WidgetsBindingObserver {
  int tab = 0;
  bool signedIn = false;
  bool pushEnabled = false;
  bool _membershipQrBusy = false;
  bool _membershipCardExpanded = false;
  List<Map<String, dynamic>> _membershipVehicles = [];
  Map<String, dynamic>? _membershipVehicle;

  String _membershipVehicleLabel(Map<String, dynamic> vehicle) {
    final nickname = vehicle['nickname']?.toString().trim() ?? '';
    return nickname.isNotEmpty
        ? nickname
        : (vehicle['model_name'] ?? '등록 차량').toString();
  }

  late final api = widget.api ?? ApiClient();
  late final AppRefreshController _appRefresh;
  int _contentRevision = 0;
  bool _pendingRefresh = false;
  void _requestDataRefresh() {
    _pendingRefresh = true;
    _applyDataRefresh();
  }

  void _applyDataRefresh() {
    if (!mounted ||
        !_pendingRefresh ||
        _membershipCardExpanded ||
        ModalRoute.of(context)?.isCurrent == false) return;
    final focus = FocusManager.instance.primaryFocus?.context;
    if (focus?.findAncestorWidgetOfExactType<EditableText>() != null) return;
    setState(() {
      _pendingRefresh = false;
      _contentRevision++;
    });
  }

  StreamSubscription<String>? tokenSubscription;
  StreamSubscription<RemoteMessage>? messageSubscription;
  StreamSubscription<RemoteMessage>? openedSubscription;
  bool pushConfigured = false;
  Timer? _pointRequestPoller;
  bool _pointApprovalDialogOpen = false;
  int? _dismissedPointRequestId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _appRefresh =
        AppRefreshController(api, _requestDataRefresh, _applyDataRefresh);
    _appRefresh.start();
    ApiClient.sessionExpired.addListener(_onSessionExpired);
    _loadSession();
    if (firebaseReady) {
      openedSubscription =
          FirebaseMessaging.onMessageOpenedApp.listen(_handlePushOpen);
      FirebaseMessaging.instance.getInitialMessage().then((message) {
        if (message != null) _handlePushOpen(message);
      }, onError: (Object _) {});
    }
  }

  void _onSessionExpired() {
    if (!mounted) return;
    setState(() {
      signedIn = false;
      tab = 6;
    });
    scaffoldMessengerKey.currentState?.showSnackBar(
        const SnackBar(content: Text('로그인이 만료되었습니다. 다시 로그인해 주세요.')));
  }

  Future<void> _loadSession() async {
    if (ApiClient.demoMode) {
      if (mounted)
        setState(() {
          signedIn = true;
          pushEnabled = false;
        });
      return;
    }
    final values =
        await Future.wait([api.isSignedIn, api.pushNotificationsEnabled]);
    if (!mounted) return;
    setState(() {
      signedIn = values[0];
      pushEnabled = values[1];
    });
    if (signedIn && pushEnabled) await _configurePush();
    if (signedIn) _startPointRequestPolling();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _appRefresh.start();
    } else {
      _appRefresh.stop();
    }
    if (state == AppLifecycleState.resumed && signedIn) {
      _checkPendingPointRedemption();
      _startPointRequestPolling();
    } else if (state != AppLifecycleState.resumed) {
      _pointRequestPoller?.cancel();
      _pointRequestPoller = null;
    }
  }

  void _startPointRequestPolling() {
    if (ApiClient.demoMode ||
        !signedIn ||
        WidgetsBinding.instance.lifecycleState != AppLifecycleState.resumed ||
        _pointRequestPoller != null) return;
    _checkPendingPointRedemption();
    _pointRequestPoller = Timer.periodic(const Duration(seconds: 3), (_) {
      _checkPendingPointRedemption();
    });
  }

  Future<void> _checkPendingPointRedemption() async {
    if (!signedIn || _pointApprovalDialogOpen || !mounted) return;
    try {
      final request = await api.pendingPointRedemption();
      if (!mounted || request == null) {
        _dismissedPointRequestId = null;
        return;
      }
      final requestId = (request['id'] as num?)?.toInt();
      if (requestId == null || requestId == _dismissedPointRequestId) return;
      _pointApprovalDialogOpen = true;
      final approve = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) => AlertDialog(
          title: const Text('포인트 사용 승인'),
          content: Text(
            '${request['partner'] ?? '협력업체'}에서 포인트 사용을 요청했어요.\n\n'
            '결제 총액  ${formatKilometers((request['payment_amount_krw'] as num?)?.toInt() ?? 0)}원\n'
            '사용 포인트  −${formatKilometers((request['points_requested'] as num?)?.toInt() ?? 0)}P\n'
            '실결제 금액  ${formatKilometers((request['actual_payment_krw'] as num?)?.toInt() ?? (((request['payment_amount_krw'] as num?)?.toInt() ?? 0) - ((request['points_requested'] as num?)?.toInt() ?? 0)))}원\n'
            '보유 포인트  ${formatKilometers((request['available_points'] as num?)?.toInt() ?? 0)}P',
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(dialogContext, false),
                child: const Text('거절')),
            FilledButton(
                onPressed: () => Navigator.pop(dialogContext, true),
                child: const Text('승인하고 결제')),
          ],
        ),
      );
      if (!mounted) return;
      if (approve == null) {
        _dismissedPointRequestId = requestId;
        return;
      }
      try {
        await api.respondPointRedemption(requestId, approve);
        scaffoldMessengerKey.currentState?.showSnackBar(SnackBar(
            content: Text(approve ? '포인트 사용을 승인했어요.' : '포인트 사용을 거절했어요.')));
      } catch (error) {
        scaffoldMessengerKey.currentState?.showSnackBar(SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', ''))));
      }
    } catch (_) {
      // The request is also checked again when the app resumes.
    } finally {
      _pointApprovalDialogOpen = false;
    }
  }

  Future<void> _configurePush() async {
    if (!signedIn || !pushEnabled || pushConfigured || !firebaseReady) return;
    pushConfigured = true;
    var failureHint = '알림 권한을 확인해 주세요.';
    try {
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission(
          alert: true, badge: true, sound: true);
      if (settings.authorizationStatus == AuthorizationStatus.denied ||
          settings.authorizationStatus == AuthorizationStatus.notDetermined) {
        pushConfigured = false;
        await api.setPushNotificationsEnabled(false);
        if (mounted) setState(() => pushEnabled = false);
        scaffoldMessengerKey.currentState?.showSnackBar(
            const SnackBar(content: Text('휴대폰 설정에서 알림 권한을 허용해 주세요.')));
        return;
      }
      if (defaultTargetPlatform == TargetPlatform.iOS) {
        failureHint = 'iPhone에서 Apple 푸시 토큰을 받지 못했습니다. 알림 권한과 푸시 서명을 확인해 주세요.';
        String? apnsToken;
        for (var attempt = 0; attempt < 20; attempt++) {
          apnsToken = await messaging.getAPNSToken();
          if (apnsToken != null && apnsToken.isNotEmpty) break;
          await Future<void>.delayed(const Duration(milliseconds: 500));
        }
        if (apnsToken == null || apnsToken.isEmpty) {
          throw StateError('APNs token was not received after 10 seconds.');
        }
      }
      failureHint =
          'Firebase에서 푸시 토큰을 발급하지 못했습니다. Cloud Messaging의 APNs 키 설정을 확인해 주세요.';
      final token = await messaging.getToken();
      if (token == null || token.isEmpty) {
        throw StateError('Firebase Messaging did not return a token.');
      }
      failureHint = '기기 토큰을 알림 서버에 등록하지 못했습니다. 네트워크와 로그인 상태를 확인해 주세요.';
      await api.registerPushInstallation(token,
          defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android');
      tokenSubscription = messaging.onTokenRefresh.listen((newToken) {
        api
            .registerPushInstallation(newToken,
                defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android')
            .then((_) {}, onError: (Object _) {});
      });
      messageSubscription = FirebaseMessaging.onMessage.listen((message) {
        final notice = message.notification;
        if (message.data['type'] == 'point_redemption') {
          _checkPendingPointRedemption();
        }
        if (notice == null) return;
        scaffoldMessengerKey.currentState?.showSnackBar(SnackBar(
            content:
                Text('${notice.title ?? '아이러브미니'} · ${notice.body ?? ''}')));
      });
    } catch (error, stackTrace) {
      // Missing Firebase platform configuration must not block sign-in or core app use.
      pushConfigured = false;
      debugPrint('Push setup failed: $error\n$stackTrace');
      scaffoldMessengerKey.currentState
          ?.showSnackBar(SnackBar(content: Text('푸시 알림 설정 실패: $failureHint')));
    }
  }

  Future<void> _setPushEnabled(bool enabled) async {
    if (enabled && !firebaseReady) {
      scaffoldMessengerKey.currentState?.showSnackBar(
          const SnackBar(content: Text('Firebase 앱 연결 설정을 먼저 완료해 주세요.')));
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
    if (message.data['type'] == 'point_redemption' && mounted) {
      _checkPendingPointRedemption();
    }
  }

  Future<void> _removePushInstallation() async {
    try {
      final token = await FirebaseMessaging.instance.getToken();
      if (token != null && token.isNotEmpty)
        await api.unregisterPushInstallation(token);
    } catch (_) {
      // The next server send removes expired tokens automatically.
    }
    pushConfigured = false;
    await tokenSubscription?.cancel();
    await messageSubscription?.cancel();
  }

  Future<void> _login() async {
    if (ApiClient.demoMode) {
      scaffoldMessengerKey.currentState?.showSnackBar(
          const SnackBar(content: Text('로그인과 차계부는 API 서버 연결 후 확인할 수 있습니다.')));
      return;
    }
    final ok = await Navigator.of(context)
        .push<bool>(MaterialPageRoute(builder: (_) => LoginPage(api: api)));
    if (ok == true && mounted) {
      setState(() => signedIn = true);
      _startPointRequestPolling();
      await _configurePush();
    }
  }

  Future<void> _openMembershipPopup() async {
    if (_membershipQrBusy) return;
    if (_membershipCardExpanded) {
      setState(() => _membershipCardExpanded = false);
      return;
    }
    if (!signedIn && !ApiClient.demoMode) {
      _login();
      return;
    }
    _membershipQrBusy = true;
    try {
      final vehicles = await api.list('vehicles');
      if (!mounted) return;
      if (vehicles.isEmpty) {
        setState(() => tab = 1);
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('차량 등록 후 QR을 이용할 수 있어요.')));
        return;
      }
      final localAuth = LocalAuthentication();
      if (!await localAuth.isDeviceSupported()) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
                content: Text('이 기기에서 화면 잠금 인증을 사용할 수 없어 QR을 열지 않았어요.')),
          );
        }
        return;
      }
      final authenticated = await localAuth.authenticate(
        localizedReason: '차량 QR을 표시하려면 Face ID, 지문 또는 기기 잠금으로 인증해 주세요.',
        options: const AuthenticationOptions(biometricOnly: false),
      );
      if (!authenticated) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('인증이 완료되지 않아 QR을 열지 않았어요.')),
          );
        }
        return;
      }
      if (mounted) {
        setState(() {
          _membershipVehicles = vehicles;
          _membershipVehicle = vehicles.first;
          _membershipCardExpanded = true;
        });
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content:
                  Text('기기 인증을 사용할 수 없습니다. Face ID·지문 또는 화면 잠금을 설정해 주세요.')),
        );
      }
    } finally {
      _membershipQrBusy = false;
    }
  }

  Widget _membershipPopupBar(BuildContext context) {
    final selected = _membershipVehicle;
    final publicId = selected?['public_id']?.toString() ??
        (ApiClient.demoMode ? 'demo-${selected?['id']}' : null);
    return Semantics(
      button: true,
      label: '아이러브미니 멤버십 열기',
      child: Material(
        color: Colors.transparent,
        child: ClipRRect(
          borderRadius: const BorderRadius.vertical(top: Radius.circular(22)),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 360),
            curve: Curves.easeInOutCubic,
            height: _membershipCardExpanded
                ? (MediaQuery.sizeOf(context).height * .47)
                    .clamp(340.0, 410.0)
                    .toDouble()
                : 72,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [Color(0xFFBD2434), Color(0xFF09090B)],
              ),
            ),
            child: Column(children: [
              SizedBox(
                height: 72,
                child: InkWell(
                  onTap: _openMembershipPopup,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 10),
                    child: Row(children: [
                      Container(
                        width: 46,
                        height: 46,
                        decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: .25),
                            borderRadius: BorderRadius.circular(14)),
                        child: const Icon(Icons.qr_code_2,
                            color: Color(0xFFFF8290), size: 26),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text('ILOVEMINI MEMBERSHIP',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 1.7)),
                      ),
                      Icon(
                          _membershipCardExpanded
                              ? Icons.keyboard_arrow_down
                              : Icons.keyboard_arrow_up,
                          color: Colors.white,
                          size: 28),
                    ]),
                  ),
                ),
              ),
              if (_membershipCardExpanded)
                Expanded(
                  child: SingleChildScrollView(
                    physics: const NeverScrollableScrollPhysics(),
                    child: SizedBox(
                      height: (MediaQuery.sizeOf(context).height * .47)
                              .clamp(340.0, 410.0)
                              .toDouble() -
                          72,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            if (_membershipVehicles.length > 1)
                              DropdownButtonHideUnderline(
                                child: DropdownButton<Map<String, dynamic>>(
                                  value: selected,
                                  isExpanded: true,
                                  alignment: Alignment.center,
                                  dropdownColor:
                                      Theme.of(context).colorScheme.surface,
                                  style:
                                      Theme.of(context).textTheme.titleMedium,
                                  selectedItemBuilder: (context) =>
                                      _membershipVehicles
                                          .map((vehicle) => Center(
                                                child: Text(
                                                  _membershipVehicleLabel(
                                                      vehicle),
                                                  maxLines: 1,
                                                  overflow:
                                                      TextOverflow.ellipsis,
                                                  textAlign: TextAlign.center,
                                                ),
                                              ))
                                          .toList(),
                                  items: _membershipVehicles
                                      .map((vehicle) => DropdownMenuItem<
                                              Map<String, dynamic>>(
                                            value: vehicle,
                                            child: Center(
                                              child: Text(
                                                _membershipVehicleLabel(
                                                    vehicle),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                textAlign: TextAlign.center,
                                              ),
                                            ),
                                          ))
                                      .toList(),
                                  onChanged: (vehicle) {
                                    if (vehicle != null) {
                                      setState(
                                          () => _membershipVehicle = vehicle);
                                    }
                                  },
                                ),
                              ),
                            if (publicId != null && publicId.isNotEmpty)
                              Flexible(
                                child: LayoutBuilder(
                                  builder: (context, constraints) {
                                    final qrSize = constraints.maxHeight
                                        .clamp(0.0, 196.0)
                                        .toDouble();
                                    return Center(
                                      child: QrImageView(
                                          data: 'ilovemini://vehicle/$publicId',
                                          size: qrSize,
                                          backgroundColor: Colors.white),
                                    );
                                  },
                                ),
                              )
                            else
                              const Flexible(
                                child: Center(
                                  child: Text('차량 QR 정보를 불러오지 못했습니다.',
                                      style: TextStyle(color: Colors.white)),
                                ),
                              ),
                            const SizedBox(height: 8),
                            const Text('승인된 협력업체 담당자에게 이 QR을 보여주세요.',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Colors.white)),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
            ]),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          centerTitle: false,
          title: Semantics(
              button: true,
              label: 'ILOVEMINI 홈으로 이동',
              child: InkWell(
                mouseCursor: SystemMouseCursors.click,
                borderRadius: BorderRadius.circular(8),
                onTap: () => setState(() => tab = 0),
                child: const Row(mainAxisSize: MainAxisSize.min, children: [
                  BrandLogo(height: 52),
                  SizedBox(width: 12),
                  Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('ILOVEMINI',
                            style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 2)),
                        Text('OWNERS COMMUNITY',
                            style: TextStyle(fontSize: 8, letterSpacing: 2))
                      ])
                ]),
              )),
          actions: [
            IconButton(
                tooltip: '화면 테마 변경',
                icon: Icon(Theme.of(context).brightness == Brightness.dark
                    ? Icons.light_mode_outlined
                    : Icons.dark_mode_outlined),
                onPressed: () {
                  appThemeMode.value =
                      Theme.of(context).brightness == Brightness.dark
                          ? ThemeMode.light
                          : ThemeMode.dark;
                })
          ]),
      body: KeyedSubtree(
          key: ValueKey('tab-$tab-revision-$_contentRevision'),
          child: switch (tab) {
            0 => HomePage(
                api: api,
                signedIn: signedIn,
                onOpenGarage: () => setState(() => tab = 1),
                onLogin: _login),
            1 => GaragePage(
                key: ValueKey('garage-$signedIn'),
                api: api,
                signedIn: signedIn,
                onLogin: _login),
            2 =>
              CatalogPage(api: api, path: 'partners', title: 'ILOVEMINI 협력업체'),
            3 => CafePage(api: api),
            _ => AccountPage(
                api: api,
                signedIn: signedIn,
                pushEnabled: pushEnabled,
                onPushChanged: _setPushEnabled,
                onLogin: _login,
                onLogout: () async {
                  await _removePushInstallation();
                  await api.logout();
                  if (mounted)
                    setState(() {
                      signedIn = false;
                      pushEnabled = false;
                    });
                },
                onManageVehicles: () => setState(() => tab = 1)),
          }),
      bottomNavigationBar: Column(mainAxisSize: MainAxisSize.min, children: [
        _membershipPopupBar(context),
        NavigationBar(
          selectedIndex: const [0, 1, 2, 3, 6].indexOf(tab).clamp(0, 4),
          onDestinationSelected: (value) =>
              setState(() => tab = const [0, 1, 2, 3, 6][value]),
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.home_outlined),
                selectedIcon: Icon(Icons.home),
                label: '홈'),
            NavigationDestination(
                icon: Icon(Icons.receipt_long_outlined),
                selectedIcon: Icon(Icons.receipt_long_outlined),
                label: '차계부'),
            NavigationDestination(
                icon: Icon(Icons.build_outlined),
                selectedIcon: Icon(Icons.build_outlined),
                label: '업체'),
            NavigationDestination(
                icon: Icon(Icons.forum_outlined),
                selectedIcon: Icon(Icons.forum),
                label: '카페'),
            NavigationDestination(
                icon: Icon(Icons.person_outline),
                selectedIcon: Icon(Icons.person),
                label: 'MY'),
          ],
        ),
      ]),
    );
  }

  @override
  void dispose() {
    _appRefresh.stop();
    WidgetsBinding.instance.removeObserver(this);
    _pointRequestPoller?.cancel();
    ApiClient.sessionExpired.removeListener(_onSessionExpired);
    tokenSubscription?.cancel();
    messageSubscription?.cancel();
    openedSubscription?.cancel();
    super.dispose();
  }
}

class SeasonLaunch extends StatelessWidget {
  const SeasonLaunch({required this.home, super.key});
  final Widget home;
  @override
  Widget build(BuildContext context) => ManagedSeasonLaunch(home: home);
}

class HomePage extends StatelessWidget {
  const HomePage(
      {required this.api,
      required this.signedIn,
      required this.onOpenGarage,
      required this.onLogin,
      super.key});
  final VoidCallback onOpenGarage;
  final VoidCallback onLogin;
  final ApiClient api;
  final bool signedIn;
  @override
  Widget build(BuildContext context) =>
      ListView(padding: const EdgeInsets.fromLTRB(20, 14, 20, 28), children: [
        VehicleOverview(
            key: ValueKey('overview-$signedIn'),
            api: api,
            signedIn: signedIn,
            onGarage: onOpenGarage),
        const SizedBox(height: 16),
        ManagedNotices(
            api: api,
            onOpen: (notice) => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => CatalogDetailPage(
                    api: api, path: 'notices', item: notice)))),
        ManagedBanners(api: api),
        ManagedUpdateNotice(api: api),
      ]);
}

class CafeCommunityCard extends StatelessWidget {
  const CafeCommunityCard({super.key});

  Future<void> _openCafe(BuildContext context) async {
    final opened = await launchUrl(Uri.parse(naverCafeMobileUrl),
        mode: LaunchMode.externalApplication);
    if (!opened && context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('네이버 카페를 열지 못했습니다.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final iconColor = isDark ? Colors.white : Colors.black87;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _openCafe(context),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          child: Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: isDark ? Colors.transparent : Colors.white,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(Icons.groups_outlined, color: iconColor),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('아이러브미니 네이버 카페',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontWeight: FontWeight.w800)),
                  SizedBox(height: 4),
                  Text('회원 게시글과 커뮤니티 소식',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
            const SizedBox(width: 6),
            Icon(Icons.open_in_new_rounded,
                size: 17,
                color: Theme.of(context).colorScheme.onSurfaceVariant),
          ]),
        ),
      ),
    );
  }
}

class CafePage extends StatefulWidget {
  const CafePage({required this.api, super.key});
  final ApiClient api;

  @override
  State<CafePage> createState() => _CafePageState();
}

class _CafePageState extends State<CafePage> {
  late Future<Map<String, dynamic>> content;

  @override
  void initState() {
    super.initState();
    content = widget.api.appContent();
  }

  Future<void> reload() async {
    final next = widget.api.appContent();
    setState(() => content = next);
    try {
      await next;
    } catch (_) {}
  }

  Widget _productCard(Map<String, dynamic> item, {bool compact = false}) =>
      Card(
          clipBehavior: Clip.antiAlias,
          child: Column(children: [
            Expanded(child: managedImage(item)),
            const Padding(padding: EdgeInsets.all(10), child: Text('업데이트예정')),
          ]));

  Widget _productList(
      List<Map<String, dynamic>> products, String category, bool showDemo) {
    final items = products
        .where((item) => '${item['category'] ?? 'recommended'}' == category)
        .toList();
    final fallbackItems = switch (category) {
      'recommended' => <Map<String, dynamic>>[
          {'asset_key': 'grille-parts'}
        ],
      'groupbuy' => <Map<String, dynamic>>[
          {'asset_key': 'shift-knob'}
        ],
      'benefits' => shoppingBenefitFallback
          .map((item) => <String, dynamic>{
                'title': item['title'],
                'description': item['detail'],
                'asset_key': item['asset_key'],
              })
          .toList(),
      _ => <Map<String, dynamic>>[],
    };
    final sourceItems = items.isNotEmpty
        ? items
        : showDemo
            ? fallbackItems
            : <Map<String, dynamic>>[];
    final visibleItems = category == 'recommended' || category == 'groupbuy'
        ? sourceItems.take(1).toList()
        : sourceItems;
    if (visibleItems.isEmpty) {
      return ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(24),
          children: const [
            SizedBox(height: 70),
            Icon(Icons.shopping_bag_outlined, size: 46, color: brandRed),
            SizedBox(height: 12),
            Center(
                child: Text('등록된 상품이 없습니다.',
                    style: TextStyle(fontWeight: FontWeight.w700))),
          ]);
    }
    return ListView.separated(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      itemCount: visibleItems.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) => SizedBox(
        height: 330,
        child: _productCard(visibleItems[index], compact: false),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
        future: content,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
                child: MiniDriveLoader(label: '쇼핑 상품을 불러오고 있어요'));
          }
          if (snapshot.hasError) {
            return Center(
                child: Column(mainAxisSize: MainAxisSize.min, children: [
              const MiniDriveLoader(label: '쇼핑 정보를 불러오지 못했어요'),
              const SizedBox(height: 12),
              TextButton.icon(
                  onPressed: reload,
                  icon: const Icon(Icons.refresh),
                  label: const Text('다시 불러오기')),
            ]));
          }
          final products = ((snapshot.data?['products'] as List?) ?? [])
              .whereType<Map>()
              .map((item) => Map<String, dynamic>.from(item))
              .toList();
          return DefaultTabController(
            length: 2,
            child: Column(children: [
              const SizedBox(height: 8),
              const CafeCommunityCard(),
              const SizedBox(height: 18),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Divider(
                  height: 1,
                  color: Theme.of(context).colorScheme.outlineVariant,
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 20, 18, 12),
                child: Row(children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.transparent
                          : Colors.white,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Icon(
                      Icons.shopping_bag_outlined,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.white
                          : Colors.black87,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('추천 아이템 · 공동구매',
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(fontWeight: FontWeight.w900)),
                        const SizedBox(height: 2),
                        Text('아이러브미니 쇼핑 정보',
                            style: TextStyle(
                                fontSize: 12,
                                color: Theme.of(context)
                                    .colorScheme
                                    .onSurfaceVariant)),
                      ],
                    ),
                  ),
                ]),
              ),
              const TabBar(tabs: [
                Tab(text: '추천아이템'),
                Tab(text: '공동구매'),
              ]),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: reload,
                  child: TabBarView(children: [
                    _productList(
                        products,
                        'recommended',
                        (snapshot.data?['configuration']
                                as Map?)?['show_demo_products'] !=
                            false),
                    _productList(
                        products,
                        'groupbuy',
                        (snapshot.data?['configuration']
                                as Map?)?['show_demo_products'] !=
                            false),
                  ]),
                ),
              ),
            ]),
          );
        },
      );
}

class EmbeddedWebPage extends StatefulWidget {
  const EmbeddedWebPage({required this.url, required this.title, super.key});
  final String url;
  final String title;
  @override
  State<EmbeddedWebPage> createState() => _EmbeddedWebPageState();
}

class _EmbeddedWebPageState extends State<EmbeddedWebPage> {
  late final WebViewController controller;
  int progress = 0;
  String? error;
  @override
  void initState() {
    super.initState();
    controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onProgress: (value) {
          if (mounted) setState(() => progress = value);
        },
        onPageStarted: (_) {
          if (mounted)
            setState(() {
              error = null;
              progress = 0;
            });
        },
        onPageFinished: (_) {
          if (mounted) setState(() => progress = 100);
        },
        onWebResourceError: (value) {
          if (value.isForMainFrame == true && mounted)
            setState(() => error = value.description);
        },
      ))
      ..loadRequest(Uri.parse(widget.url));
  }

  @override
  void didUpdateWidget(covariant EmbeddedWebPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.url != widget.url) {
      error = null;
      progress = 0;
      controller.loadRequest(Uri.parse(widget.url));
    }
  }

  @override
  Widget build(BuildContext context) => Stack(children: [
        Positioned.fill(child: WebViewWidget(controller: controller)),
        if (progress < 100 && error == null)
          Positioned.fill(
              child: ColoredBox(
                  color: Theme.of(context)
                      .colorScheme
                      .surface
                      .withValues(alpha: .94),
                  child: Center(
                      child:
                          MiniDriveLoader(label: '${widget.title} 불러오는 중')))),
        if (error != null)
          Positioned.fill(
              child: ColoredBox(
                  color: Theme.of(context).colorScheme.surface,
                  child: Center(
                      child: Padding(
                          padding: const EdgeInsets.all(24),
                          child:
                              Column(mainAxisSize: MainAxisSize.min, children: [
                            const Icon(Icons.wifi_off, size: 42),
                            const SizedBox(height: 12),
                            Text('${widget.title}를 불러오지 못했습니다.',
                                textAlign: TextAlign.center),
                            const SizedBox(height: 8),
                            Text(error!,
                                textAlign: TextAlign.center,
                                style: Theme.of(context).textTheme.bodySmall),
                            const SizedBox(height: 16),
                            FilledButton.icon(
                                onPressed: () {
                                  setState(() {
                                    error = null;
                                    progress = 0;
                                  });
                                  controller.loadRequest(Uri.parse(widget.url));
                                },
                                icon: const Icon(Icons.refresh),
                                label: const Text('다시 시도')),
                          ]))))),
      ]);
}

class RecommendedCafeItemsCarousel extends StatefulWidget {
  const RecommendedCafeItemsCarousel({super.key});
  @override
  State<RecommendedCafeItemsCarousel> createState() =>
      _RecommendedCafeItemsCarouselState();
}

class _RecommendedCafeItemsCarouselState
    extends State<RecommendedCafeItemsCarousel> {
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
      _controller.nextPage(
          duration: const Duration(milliseconds: 360),
          curve: Curves.easeOutCubic);
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
      Text('제품 정보와 MINI 호환 여부를 확인하고 있어요.',
          style: TextStyle(
              fontSize: 12,
              color: Theme.of(context).colorScheme.onSurfaceVariant)),
      const SizedBox(height: 9),
      Card(
          clipBehavior: Clip.antiAlias,
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            SizedBox(
              height: width,
              child: Stack(children: [
                PageView.builder(
                  controller: _controller,
                  itemCount: recommendedCafeItems.length + 2,
                  onPageChanged: _onPageChanged,
                  itemBuilder: (context, page) {
                    final itemIndex = page == 0
                        ? recommendedCafeItems.length - 1
                        : page == recommendedCafeItems.length + 1
                            ? 0
                            : page - 1;
                    final item = recommendedCafeItems[itemIndex];
                    return ColoredBox(
                      color: Colors.white,
                      child: Image.asset(item['image']!,
                          fit: BoxFit.contain,
                          semanticLabel: item['title'],
                          errorBuilder: (context, error, stackTrace) =>
                              const Center(
                                  child: Icon(
                                      Icons.image_not_supported_outlined,
                                      size: 42))),
                    );
                  },
                ),
                Positioned(
                    right: 9,
                    bottom: 9,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                          color: const Color(0xC7191A1E),
                          borderRadius: BorderRadius.circular(24)),
                      child: Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 5, vertical: 3),
                          child: Row(mainAxisSize: MainAxisSize.min, children: [
                            IconButton(
                                visualDensity: VisualDensity.compact,
                                tooltip: '이전 아이템',
                                onPressed: () => _controller.previousPage(
                                    duration: const Duration(milliseconds: 280),
                                    curve: Curves.easeOut),
                                icon: const Icon(Icons.chevron_left,
                                    color: Colors.white, size: 20)),
                            Text(
                                '$_logicalPage / ${recommendedCafeItems.length}',
                                style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w800)),
                            IconButton(
                                visualDensity: VisualDensity.compact,
                                tooltip: '다음 아이템',
                                onPressed: () => _controller.nextPage(
                                    duration: const Duration(milliseconds: 280),
                                    curve: Curves.easeOut),
                                icon: const Icon(Icons.chevron_right,
                                    color: Colors.white, size: 20)),
                            IconButton(
                                visualDensity: VisualDensity.compact,
                                tooltip: _paused ? '자동 넘김 재생' : '자동 넘김 일시정지',
                                onPressed: _togglePause,
                                icon: Icon(
                                    _paused ? Icons.play_arrow : Icons.pause,
                                    color: Colors.white,
                                    size: 18)),
                          ])),
                    )),
              ]),
            ),
            Padding(
                padding: const EdgeInsets.fromLTRB(14, 11, 14, 13),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(recommendedCafeItems[_logicalPage - 1]['title']!,
                          style: const TextStyle(
                              fontSize: 17, fontWeight: FontWeight.w900)),
                      const SizedBox(height: 3),
                      Text(recommendedCafeItems[_logicalPage - 1]['detail']!,
                          style: TextStyle(
                              fontSize: 12,
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurfaceVariant)),
                      const SizedBox(height: 8),
                      const Align(
                          alignment: Alignment.centerLeft,
                          child: Chip(
                              visualDensity: VisualDensity.compact,
                              label: Text('구매 링크 준비 중'))),
                    ])),
          ])),
      const SizedBox(height: 6),
      Text('실제 등록 전 상품명과 적용 차종을 확인할 예정입니다.',
          style: TextStyle(
              fontSize: 11,
              color: Theme.of(context).colorScheme.onSurfaceVariant)),
    ]);
  }
}

class CafeLatestFeed extends StatefulWidget {
  const CafeLatestFeed({required this.api, super.key});
  final ApiClient api;
  @override
  State<CafeLatestFeed> createState() => _CafeLatestFeedState();
}

class _CafeLatestFeedState extends State<CafeLatestFeed> {
  late Future<Map<String, dynamic>> posts;
  @override
  void initState() {
    super.initState();
    posts = widget.api.latestCafePosts();
  }

  void reload() => setState(() => posts = widget.api.latestCafePosts());

  Future<void> openPost(Map<String, dynamic> post) async {
    final uri = Uri.tryParse((post['link'] ?? '').toString());
    if (uri == null || uri.scheme != 'https' || uri.host != 'cafe.naver.com')
      return;
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication) &&
        mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('카페 글을 열지 못했습니다.')));
    }
  }

  @override
  Widget build(BuildContext context) => Card(
      child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 6),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Expanded(
                  child: SectionHeading(
                      title: '아이러브미니 최신글', subtitle: '네이버 카페 · 최신순')),
              IconButton(
                  tooltip: '최신글 새로고침',
                  onPressed: reload,
                  icon: const Icon(Icons.refresh_rounded)),
            ]),
            FutureBuilder<Map<String, dynamic>>(
              future: posts,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting)
                  return const Padding(
                      padding: EdgeInsets.symmetric(vertical: 22),
                      child: Center(child: MiniDriveLoader(compact: true)));
                if (snapshot.hasError)
                  return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Row(children: [
                        Expanded(
                            child: Text('최신글을 불러오지 못했어요. 네이버 API 설정을 확인해 주세요.',
                                style: TextStyle(
                                    fontSize: 12,
                                    color:
                                        Theme.of(context).colorScheme.error))),
                        TextButton(
                            onPressed: reload, child: const Text('다시 시도')),
                      ]));
                final rows = (snapshot.data?['items'] as List?)
                        ?.whereType<Map>()
                        .map((row) => Map<String, dynamic>.from(row))
                        .take(10)
                        .toList() ??
                    const <Map<String, dynamic>>[];
                if (rows.isEmpty)
                  return const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: Text('네이버 API에서 확인되는 공개 최신글이 없습니다.',
                          style: TextStyle(fontSize: 12)));
                return Column(
                    children: rows
                        .map((post) => InkWell(
                              onTap: () => openPost(post),
                              child: Padding(
                                  padding:
                                      const EdgeInsets.symmetric(vertical: 10),
                                  child: Row(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        const Padding(
                                            padding: EdgeInsets.only(
                                                top: 6, right: 9),
                                            child: Icon(Icons.circle,
                                                size: 6, color: brandRed)),
                                        Expanded(
                                            child: Column(
                                                crossAxisAlignment:
                                                    CrossAxisAlignment.start,
                                                children: [
                                              Text(
                                                  (post['title'] ??
                                                          '아이러브미니 카페 게시글')
                                                      .toString(),
                                                  maxLines: 2,
                                                  overflow:
                                                      TextOverflow.ellipsis,
                                                  style: const TextStyle(
                                                      fontSize: 14,
                                                      fontWeight:
                                                          FontWeight.w800,
                                                      height: 1.35)),
                                              if ((post['description'] ?? '')
                                                  .toString()
                                                  .isNotEmpty) ...[
                                                const SizedBox(height: 3),
                                                Text(
                                                    post['description']
                                                        .toString(),
                                                    maxLines: 2,
                                                    overflow:
                                                        TextOverflow.ellipsis,
                                                    style: TextStyle(
                                                        fontSize: 11,
                                                        color: Theme.of(context)
                                                            .colorScheme
                                                            .onSurfaceVariant,
                                                        height: 1.35)),
                                              ],
                                              const SizedBox(height: 3),
                                              Text(
                                                  '${post['cafe_name'] ?? '아이러브미니'} · 네이버 카페',
                                                  style: TextStyle(
                                                      fontSize: 10,
                                                      color: Theme.of(context)
                                                          .colorScheme
                                                          .onSurfaceVariant)),
                                            ])),
                                        const Icon(Icons.open_in_new_rounded,
                                            size: 15),
                                      ])),
                            ))
                        .toList());
              },
            ),
          ])));
}

class AttendanceCheckinCard extends StatefulWidget {
  const AttendanceCheckinCard(
      {required this.api,
      required this.signedIn,
      required this.onLogin,
      super.key});
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
  void initState() {
    super.initState();
    summary = _load();
  }

  @override
  void didUpdateWidget(covariant AttendanceCheckinCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.signedIn != widget.signedIn) summary = _load();
  }

  Future<Map<String, dynamic>> _load() =>
      !widget.signedIn && !ApiClient.demoMode
          ? Future.value({
              'balance_points': 0,
              'streak_days': 0,
              'checked_in_today': false,
              'checkins': []
            })
          : widget.api.attendanceSummary();

  Future<void> _checkIn() async {
    if (!widget.signedIn && !ApiClient.demoMode) {
      widget.onLogin();
      return;
    }
    setState(() => busy = true);
    try {
      final result = await widget.api.checkIn();
      if (!mounted) return;
      setState(() => summary = Future.value({
            ...result,
            // A successful POST (including an already-checked-in response) confirms today's state.
            'checked_in_today': true,
          }));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message']?.toString() ?? '출석 상태를 확인했어요.')));
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('출석 처리에 실패했어요. 잠시 후 다시 시도해 주세요.')));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Card(
        clipBehavior: Clip.antiAlias,
        child: Padding(
            padding: const EdgeInsets.all(16),
            child: FutureBuilder<Map<String, dynamic>>(
              future: summary,
              builder: (context, snapshot) {
                final data = snapshot.data ?? const <String, dynamic>{};
                final points = (data['balance_points'] as num?)?.toInt() ?? 0;
                final checked = data['checked_in_today'] == true;
                return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        const Icon(Icons.event_available, color: brandRed),
                        const SizedBox(width: 8),
                        const Expanded(
                            child: Text('오늘의 출석체크',
                                style: TextStyle(fontWeight: FontWeight.w800))),
                        Text('$points P',
                            style: const TextStyle(
                                fontSize: 19,
                                fontWeight: FontWeight.w900,
                                color: brandRed)),
                      ]),
                      const SizedBox(height: 6),
                      Text('하루 1회 출석 100P · 적립 포인트는 다음 날부터 사용할 수 있어요.',
                          style: TextStyle(
                              fontSize: 12,
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurfaceVariant)),
                      const SizedBox(height: 10),
                      SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed: checked ||
                                    busy ||
                                    snapshot.connectionState ==
                                        ConnectionState.waiting
                                ? null
                                : _checkIn,
                            icon: Icon(checked
                                ? Icons.check_circle_outline
                                : Icons.touch_app_outlined),
                            label: Text(busy
                                ? '처리 중…'
                                : !widget.signedIn && !ApiClient.demoMode
                                    ? '로그인하고 출석하기'
                                    : checked
                                        ? '오늘 출석 완료'
                                        : '출석하고 100P 받기'),
                          )),
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
    {
      'image': 'album-01.jpg',
      'title': '연휴 끝',
      'author': '꼬마악동',
      'meta': '01:05 · 조회 137'
    },
    {
      'image': 'album-02.jpg',
      'title': '명절이라 디테일링 …',
      'author': '구름아',
      'meta': '26.09.25 · 조회 220'
    },
    {
      'image': 'album-03.jpg',
      'title': '몇년만에 손세차.. F60',
      'author': '케인지F60촌놈',
      'meta': '26.09.25 · 조회 147'
    },
    {
      'image': 'album-04.jpg',
      'title': '블랙의 세차',
      'author': '집가이',
      'meta': '26.09.25 · 조회 187'
    },
    {
      'image': 'album-05.jpg',
      'title': '3개월만에 차 받았어…',
      'author': '빵빵도우',
      'meta': '26.09.23 · 조회 250'
    },
    {
      'image': 'album-06.jpg',
      'title': '하루를 마감하는 미니',
      'author': '집가이',
      'meta': '26.09.23 · 조회 159'
    },
  ];
  final ScrollController _scrollController = ScrollController();
  int _index = 0;

  void _updateIndex(double cardStep) {
    if (!_scrollController.hasClients) return;
    final next = (_scrollController.offset / cardStep)
        .round()
        .clamp(0, _posts.length - 1);
    if (next != _index && mounted) setState(() => _index = next);
  }

  void _move(double cardStep, int direction) {
    if (!_scrollController.hasClients) return;
    final destination = (_scrollController.offset + cardStep * direction)
        .clamp(0.0, _scrollController.position.maxScrollExtent)
        .toDouble();
    _scrollController.animateTo(destination,
        duration: const Duration(milliseconds: 280), curve: Curves.easeOut);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cardWidth = (MediaQuery.sizeOf(context).width - 40) * .7;
    final cardStep = cardWidth + 12;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const Expanded(
            child: SectionHeading(title: '미니앨범', subtitle: '카페 회원들의 MINI 이야기')),
        IconButton(
            tooltip: '이전 사진',
            onPressed: _index == 0 ? null : () => _move(cardStep, -1),
            icon: const Icon(Icons.chevron_left)),
        Text('${_index + 1} / ${_posts.length}',
            style: TextStyle(
                fontSize: 12, color: theme.colorScheme.onSurfaceVariant)),
        IconButton(
            tooltip: '다음 사진',
            onPressed:
                _index == _posts.length - 1 ? null : () => _move(cardStep, 1),
            icon: const Icon(Icons.chevron_right)),
      ]),
      SizedBox(
          height: cardWidth + 82,
          child: NotificationListener<ScrollNotification>(
            onNotification: (notification) {
              _updateIndex(cardStep);
              return false;
            },
            child: ListView.separated(
              controller: _scrollController,
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              itemCount: _posts.length,
              separatorBuilder: (_, __) => const SizedBox(width: 12),
              itemBuilder: (context, index) {
                final post = _posts[index];
                return SizedBox(
                    width: cardWidth,
                    child: Semantics(
                      button: true,
                      label:
                          '${post['title']}, ${post['author']}. 아이러브미니 카페 미니앨범 열기',
                      child: InkWell(
                        borderRadius: BorderRadius.circular(10),
                        onTap: () =>
                            _openCafeNotice(context, naverCafeMobileUrl),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: AspectRatio(
                                  aspectRatio: 1,
                                  child: Image.asset(
                                      'assets/images/mini-album/${post['image']}',
                                      fit: BoxFit.cover),
                                ),
                              ),
                              const SizedBox(height: 5),
                              Text(post['title']!,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w800)),
                              const SizedBox(height: 3),
                              Text(post['author']!,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                      fontSize: 12,
                                      color: theme.colorScheme.onSurface)),
                              const SizedBox(height: 2),
                              Text(post['meta']!,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                      fontSize: 11,
                                      color:
                                          theme.colorScheme.onSurfaceVariant)),
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
  const VehicleOverview(
      {required this.api,
      required this.signedIn,
      required this.onGarage,
      super.key});
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
    vehicles = widget.signedIn || ApiClient.demoMode
        ? widget.api.list('vehicles')
        : Future.value([]);
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<
          List<Map<String, dynamic>>>(
      future: vehicles,
      builder: (context, snapshot) {
        final vehicle = snapshot.data?.firstOrNull;
        final loading = snapshot.connectionState == ConnectionState.waiting;
        final subtitle = vehicle == null
            ? (snapshot.hasError
                ? '차량 정보를 불러오지 못했습니다'
                : loading
                    ? '차량 정보를 불러오는 중'
                    : '차량을 등록하고 기록을 시작하세요')
            : [
                vehicle['generation'],
                vehicle['trim'],
                vehicle['model_year'] == null
                    ? null
                    : '${vehicle['model_year']}년형'
              ]
                .where((part) => part != null && part.toString().isNotEmpty)
                .join(' · ');
        final modelName = (vehicle?['model_name'] ?? '내 차량').toString();
        final vehicleTitle = modelName;
        return InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: widget.onGarage,
          child: Card(
              child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(children: [
                          const Expanded(
                              child: Text('내 차량',
                                  style:
                                      TextStyle(fontWeight: FontWeight.w800))),
                          TextButton(
                              style: TextButton.styleFrom(
                                  minimumSize: const Size(0, 34),
                                  padding:
                                      const EdgeInsets.symmetric(horizontal: 8),
                                  tapTargetSize:
                                      MaterialTapTargetSize.shrinkWrap),
                              onPressed: widget.onGarage,
                              child: const Text('차량 관리')),
                        ]),
                        const SizedBox(height: 2),
                        Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (vehicle != null &&
                                  (hasFavouredF66Photo(vehicle) ||
                                      hasMaybachPhoto(vehicle) ||
                                      hasMiniVehiclePhoto(vehicle) ||
                                      hasBmwVehiclePhoto(vehicle)))
                                Padding(
                                    padding: const EdgeInsets.only(
                                        right: 10, top: 16),
                                    child: SizedBox(
                                        width: 88,
                                        child: VehiclePhoto(
                                            vehicle: vehicle, height: 54)))
                              else
                                const Padding(
                                    padding:
                                        EdgeInsets.only(right: 10, top: 16),
                                    child: SizedBox(
                                        width: 88,
                                        height: 54,
                                        child: Icon(Icons.directions_car,
                                            size: 36))),
                              Expanded(
                                  child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                    Text(vehicleTitle,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(
                                            fontSize: 17,
                                            fontWeight: FontWeight.w900,
                                            letterSpacing: -.5)),
                                    const SizedBox(height: 2),
                                    Text(subtitle,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: TextStyle(
                                            fontSize: 12,
                                            color: Theme.of(context)
                                                .colorScheme
                                                .onSurfaceVariant)),
                                  ])),
                              const Icon(Icons.chevron_right, size: 20),
                            ]),
                        const SizedBox(height: 2),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Padding(
                            padding: const EdgeInsets.only(left: 98),
                            child:
                                Row(mainAxisSize: MainAxisSize.min, children: [
                              const Icon(Icons.speed, size: 15),
                              const SizedBox(width: 4),
                              Text(
                                  '현재 주행거리  ${vehicle == null ? '미등록' : '${formatKilometers(vehicle['current_odometer_km'])} km'}',
                                  style: const TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700)),
                            ]),
                          ),
                        ),
                      ]))),
        );
      });
}

Map<String, String>? partnerExternalActions(String name) {
  if (name.contains('얼마면탈까'))
    return {
      'label': '상담',
      'contact': 'https://pf.kakao.com/_xerCTG/chat',
      'site': 'https://openestimate.co.kr/'
    };
  if (name.contains('프린트랩'))
    return {
      'label': '상담',
      'contact': 'https://pf.kakao.com/_mxlrHj/chat',
      'site': 'https://smartstore.naver.com/print_lab/'
    };
  return null;
}

Future<void> _openBimmerRefs(BuildContext context) async {
  final uri = Uri.parse('https://www.bimmerrefs.com/en/app');
  try {
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication) &&
        context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('순정 부품 조회를 열지 못했습니다.')));
    }
  } catch (_) {
    if (context.mounted)
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('순정 부품 조회를 열지 못했습니다.')));
  }
}

class CatalogPage extends StatefulWidget {
  const CatalogPage(
      {required this.api,
      required this.path,
      required this.title,
      this.compact = false,
      super.key});
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
    if (actions != null) {
      _openCafeNotice(context, actions['contact']!);
      return;
    }
    setState(() => mapQuery =
        '${item['name']} ${item['address'] ?? item['region'] ?? ''}'.trim());
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final panel = mapPanelKey.currentContext;
      if (panel != null)
        Scrollable.ensureVisible(panel,
            alignment: .1, duration: const Duration(milliseconds: 300));
    });
  }

  @override
  void initState() {
    super.initState();
    itemsFuture = widget.api.list(widget.path);
  }

  @override
  void didUpdateWidget(covariant CatalogPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path || oldWidget.api != widget.api) {
      itemsFuture = widget.api.list(widget.path);
      query = '';
      filter = '전체';
    }
  }

  Future<void> reload() async {
    final future = widget.api.list(widget.path);
    setState(() => itemsFuture = future);
    try {
      await future;
    } catch (_) {/* FutureBuilder displays the error. */}
  }

  bool matches(Map<String, dynamic> item) {
    final categories = (item['service_categories'] as List? ?? [])
        .join(' ')
        .replaceAll('휠.타이어', '휠·타이어');
    final text = '${item['name']} ${item['region']} $categories'.toLowerCase();
    final categoryMatch = switch (filter) {
      '정비' || '경정비' => categories.contains('정비') || categories.contains('수입차'),
      '사고수리' => categories.contains('사고') || categories.contains('판금'),
      '차량유리' => categories.contains('유리'),
      '오디오' => categories.contains('오디오'),
      '휠·타이어' => categories.contains('휠') || categories.contains('타이어'),
      '전장튜닝' => categories.contains('부품') ||
          categories.contains('튜닝') ||
          categories.contains('전장'),
      '신차패키지' => _partnerSpecialty(item) == '신차패키지',
      _ => filter == '전체' ||
          categories.contains(filter.replaceAll('휠.타이어', '휠·타이어')),
    };
    return categoryMatch &&
        (regionFilter == '전체 지역' ||
            _partnerRegionGroup(item) == regionFilter) &&
        text.contains(query.trim().toLowerCase());
  }

  void openItem(Map<String, dynamic> item) {
    Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => widget.path == 'partners'
            ? LivePartnerView(
                api: widget.api,
                initial: item,
                builder: (fresh) =>
                    PartnerDetailPage(api: widget.api, partner: fresh))
            : CatalogDetailPage(
                api: widget.api, path: widget.path, item: item)));
  }

  String _partnerRegionGroup(Map<String, dynamic> item) {
    final group = '${item['region_group'] ?? item['group'] ?? ''}';
    if (group.contains('신차패키지')) return '신차패키지';
    if (group.contains('전라') || group.contains('경상') || group.contains('충청'))
      return '전라/경상/충청 협력업체';
    final region = '${item['region'] ?? ''}';
    if (RegExp(r'부산|경남|경북|충남|충북|전남|전북|대전|광주|울산|세종|논산').hasMatch(region))
      return '전라/경상/충청 협력업체';
    return '서울/경기 협력업체';
  }

  String _partnerSpecialty(Map<String, dynamic> item) {
    final text =
        '${item['category'] ?? ''} ${(item['service_categories'] as List? ?? []).join(' ')}';
    if (text.contains('브랜드홍보')) return '브랜드홍보';
    if (text.contains('신차')) return '신차패키지';
    if (text.contains('사고')) return '사고수리 전문';
    if (text.contains('유리')) return '차량유리 전문';
    if (RegExp(r'전장|오디오|튜닝|부품').hasMatch(text)) return '전장류 전문';
    if (RegExp(r'휠|타이어').hasMatch(text)) return '휠·타이어 전문';
    return '정비 전문';
  }

  String _managedPartnerGroup(Map<String, dynamic> item) {
    final categories = (item['service_categories'] as List? ?? [])
        .map((e) => '$e'.replaceAll('휠.타이어', '휠·타이어'))
        .toList();
    for (final category in widget.api.serviceCategories) {
      final normalized = category.replaceAll('휠.타이어', '휠·타이어');
      if (categories.contains(normalized) ||
          (category == '경정비' && categories.any((e) => e.contains('정비'))))
        return category;
    }
    return '기타';
  }

  List<Widget> _partnerGroupTiles(List<Map<String, dynamic>> items) {
    final showNestedCounts =
        query.trim().isEmpty && filter == '전체' && regionFilter == '전체 지역';
    final groups = [...widget.api.serviceCategories, '기타'];
    return ['서울/경기 협력업체', '전라/경상/충청 협력업체', '신차패키지', '기타 협력업체'].expand((region) {
      final shops = items
          .where((item) => region == '신차패키지'
              ? _partnerSpecialty(item) == '신차패키지'
              : _partnerSpecialty(item) != '신차패키지' &&
                  _partnerRegionGroup(item) == region)
          .toList();
      if (shops.isEmpty) return <Widget>[];
      final headings = groups;
      return <Widget>[
        Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Row(children: [
              Expanded(
                  child: Text(
                      region == '서울/경기 협력업체'
                          ? '수도권 협력업체'
                          : region == '신차패키지'
                              ? '신차패키지 업체'
                              : region == '기타 협력업체'
                                  ? '기타 협력업체'
                                  : '전라/경상/충청 협력업체',
                      style: const TextStyle(
                          fontWeight: FontWeight.w800, fontSize: 18))),
              if (showNestedCounts) Text('${shops.length}곳')
            ])),
        ...headings.map((group) {
          final matching = shops
              .where((item) => _managedPartnerGroup(item) == group)
              .toList();
          final list = group == '사고수리 전문'
              ? sortAccidentRepairPartners(matching)
              : matching;
          if (list.isEmpty) return const SizedBox.shrink();
          return Card(
              clipBehavior: Clip.antiAlias,
              child: ExpansionTile(
                key: PageStorageKey('partner-$region-$group-$filter-$query'),
                initiallyExpanded: filter != '전체' || query.isNotEmpty,
                title: Text(group,
                    style: const TextStyle(fontWeight: FontWeight.w700)),
                trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                  if (showNestedCounts) ...[
                    Text('${list.length}곳'),
                    const SizedBox(width: 12),
                  ],
                  const Icon(Icons.add, color: brandRed)
                ]),
                children: list.map((item) {
                  final external = partnerExternalActions('${item['name']}');
                  final address = '${item['address'] ?? ''}'.trim();
                  final location = address.isNotEmpty
                      ? address
                      : '${item['region'] ?? ''}'.trim();
                  final category = '${item['category'] ?? group}'.trim();
                  final detail = [
                    if (location.isNotEmpty) location,
                    if (category.isNotEmpty) category,
                  ].join(' · ');
                  return Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            InkWell(
                                onTap: () => openItem(item),
                                child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                          [
                                            item['name'],
                                            if ((item['branch_label'] ?? '')
                                                .toString()
                                                .isNotEmpty)
                                              item['branch_label']
                                          ].join(' · '),
                                          softWrap: true,
                                          style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                              fontSize: 16)),
                                      const SizedBox(height: 6),
                                      Text(detail,
                                          softWrap: true,
                                          style: TextStyle(
                                              color: Theme.of(context)
                                                  .colorScheme
                                                  .onSurfaceVariant)),
                                      if ((item['service_categories']
                                                  as List? ??
                                              const [])
                                          .isNotEmpty) ...[
                                        const SizedBox(height: 8),
                                        Wrap(
                                            spacing: 6,
                                            runSpacing: 2,
                                            children: (item[
                                                        'service_categories']
                                                    as List)
                                                .map((category) => Chip(
                                                      visualDensity:
                                                          VisualDensity.compact,
                                                      label: Text(
                                                          category.toString(),
                                                          softWrap: true),
                                                    ))
                                                .toList()),
                                      ],
                                    ])),
                            const SizedBox(height: 10),
                            Row(children: [
                              Expanded(
                                  child: OutlinedButton(
                                      onPressed: () => showPartnerMap(item),
                                      child:
                                          Text(external?['label'] ?? '지도보기'))),
                              const SizedBox(width: 8),
                              Expanded(
                                  child: FilledButton(
                                      onPressed: () => external == null
                                          ? openItem(item)
                                          : _openCafeNotice(
                                              context, external['site']!),
                                      child: Text(external == null
                                          ? '예약 요청'
                                          : '사이트 이동')))
                            ]),
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
            return widget.path == 'partners'
                ? const SizedBox.shrink()
                : const Padding(
                    padding: EdgeInsets.all(20),
                    child:
                        Center(child: MiniDriveLoader(label: '목록을 불러오고 있어요')));
          }
          if (snapshot.hasError)
            return Column(children: [
              InfoCard(
                  text: snapshot.error is TimeoutException
                      ? '서버가 시작하는 데 시간이 걸리고 있습니다. 잠시 후 다시 시도해 주세요.'
                      : '목록 요청 실패: ${snapshot.error.toString().replaceFirst("Exception: ", "")}'),
              TextButton(onPressed: reload, child: const Text('다시 시도')),
            ]);
          final apiItems = snapshot.data ?? [];
          final isPartners = widget.path == 'partners';
          final all = isPartners ? alignPartnerDirectory(apiItems) : apiItems;
          final items = isPartners ? all.where(matches).toList() : all;
          return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (isPartners) ...[
                  if (!widget.compact) ...[
                    const Text('ILOVEMINI PARTNERS',
                        style: TextStyle(
                            color: brandRed,
                            letterSpacing: 3,
                            fontWeight: FontWeight.w800)),
                    const SizedBox(height: 18),
                    Row(children: [
                      Expanded(
                          flex: 3,
                          child: TextField(
                              decoration: const InputDecoration(
                                  hintText: '업체명 정비 항목 검색'),
                              onChanged: (value) =>
                                  setState(() => query = value))),
                      const SizedBox(width: 10),
                      Expanded(
                          flex: 2,
                          child: DropdownButtonFormField<String>(
                              isExpanded: true,
                              initialValue: regionFilter,
                              items: [
                                '전체 지역',
                                '서울/경기 협력업체',
                                '전라/경상/충청 협력업체',
                                '신차패키지',
                                '기타 협력업체'
                              ]
                                  .map((value) => DropdownMenuItem(
                                      value: value,
                                      child: Text(
                                          value == '서울/경기 협력업체'
                                              ? '수도권 협력업체'
                                              : value == '전라/경상/충청 협력업체'
                                                  ? '전라/경상/충청'
                                                  : value == '기타 협력업체'
                                                      ? '기타'
                                                      : value,
                                          overflow: TextOverflow.ellipsis)))
                                  .toList(),
                              onChanged: (value) =>
                                  setState(() => regionFilter = value!)))
                    ]),
                    const SizedBox(height: 12),
                    Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          '전체',
                          ...widget.api.serviceCategories,
                        ]
                            .map((name) => ChoiceChip(
                                label: Text(name),
                                selected: filter == name,
                                showCheckmark: false,
                                selectedColor: brandRed,
                                labelStyle: TextStyle(
                                    color: filter == name
                                        ? Colors.white
                                        : Theme.of(context)
                                            .colorScheme
                                            .onSurface),
                                shape: const StadiumBorder(),
                                onSelected: (_) =>
                                    setState(() => filter = name)))
                            .toList()),
                  ],
                  const SizedBox(height: 24),
                  const Text('업체지도',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 12),
                ],
                if (items.isEmpty)
                  InfoCard(
                      text: all.isEmpty ? widget.title : '검색 조건에 맞는 업체가 없습니다.'),
                if (isPartners) ...[
                  Padding(
                      key: mapPanelKey,
                      padding: const EdgeInsets.only(bottom: 16),
                      child: PartnerMap(query: mapQuery)),
                  Row(children: [
                    const Expanded(child: Text('검색 결과')),
                    Text('${items.length}곳',
                        style: const TextStyle(fontWeight: FontWeight.w800))
                  ]),
                  ..._partnerGroupTiles(items),
                ] else
                  ...items.map((item) => Card(
                      clipBehavior: Clip.antiAlias,
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 18, vertical: 8),
                        leading: CircleAvatar(
                            backgroundColor:
                                Theme.of(context).colorScheme.primaryContainer,
                            child: Text(widget.path == 'notices' ? '📣' : '🎁',
                                style: const TextStyle(fontSize: 21))),
                        title: Row(children: [
                          Expanded(
                              child: Text(
                                  (item['title'] ?? item['name'] ?? '')
                                      .toString(),
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w800))),
                          if (item['is_new'] == true) const _NewBadge(),
                          if (item['is_sponsored'] == true)
                            const _SponsoredBadge(),
                        ]),
                        subtitle: Text(
                            (item['summary'] ??
                                    item['region'] ??
                                    item['description'] ??
                                    '')
                                .toString(),
                            maxLines: widget.compact ? 2 : 3,
                            overflow: TextOverflow.ellipsis),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => openItem(item),
                      ))),
              ]);
        });
    if (widget.compact) return content;
    if (widget.path == 'partners') {
      return Stack(children: [
        RefreshIndicator(
            onRefresh: reload,
            child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(20),
                children: [PartnerToolsShortcuts(api: widget.api), content])),
        FutureBuilder<List<Map<String, dynamic>>>(
            future: itemsFuture,
            builder: (context, snapshot) => snapshot.connectionState ==
                    ConnectionState.waiting
                ? const Positioned.fill(
                    child:
                        Center(child: MiniDriveLoader(label: '목록을 불러오고 있어요')))
                : const SizedBox.shrink()),
      ]);
    }
    return RefreshIndicator(
        onRefresh: reload,
        child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(20),
            children: [
              content,
            ]));
  }
}

class PartnerToolsShortcuts extends StatefulWidget {
  const PartnerToolsShortcuts({required this.api, super.key});
  final ApiClient api;

  @override
  State<PartnerToolsShortcuts> createState() => _PartnerToolsShortcutsState();
}

class _PartnerToolsShortcutsState extends State<PartnerToolsShortcuts> {
  late Future<List<Map<String, dynamic>>> _workplaces;

  @override
  void initState() {
    super.initState();
    _workplaces = widget.api.list('partners/my-workplaces');
  }

  @override
  Widget build(BuildContext context) =>
      FutureBuilder<List<Map<String, dynamic>>>(
        future: _workplaces,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done ||
              snapshot.hasError ||
              snapshot.data?.isNotEmpty != true) {
            return const SizedBox.shrink();
          }
          return Padding(
            padding: const EdgeInsets.only(bottom: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _PartnerToolButton(
                  icon: Icons.calendar_month_outlined,
                  title: '예약 현황판',
                  subtitle: '예약 일정 확인 및 처리',
                  height: 118,
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) =>
                          PartnerBookingCalendarPage(api: widget.api),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                _PartnerToolButton(
                  icon: Icons.qr_code_scanner,
                  title: '회원 차량 QR 스캔',
                  subtitle: '차량 확인 · 정비 등록',
                  height: 96,
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => PartnerRecordPage(api: widget.api),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      );
}

class PartnerPointRedemptionPage extends StatefulWidget {
  const PartnerPointRedemptionPage({
    required this.api,
    required this.initialVehiclePublicId,
    required this.initialPlateNumber,
    required this.initialPartnerId,
    super.key,
  });
  final ApiClient api;
  final String initialVehiclePublicId;
  final String initialPlateNumber;
  final int initialPartnerId;

  @override
  State<PartnerPointRedemptionPage> createState() =>
      _PartnerPointRedemptionPageState();
}

class _PartnerPointRedemptionPageState
    extends State<PartnerPointRedemptionPage> {
  final _formKey = GlobalKey<FormState>();
  final _amount = TextEditingController();
  final _points = TextEditingController();
  late Future<List<Map<String, dynamic>>> _workplaces;
  Map<String, dynamic>? _selectedPartner;
  String? _vehiclePublicId;
  int? _availablePoints;
  String? _vehiclePlateNumber;
  int? _approvedRedemptionId;
  bool _loadingBalance = false;
  Map<String, dynamic>? _request;
  String? _error;
  bool _busy = false;
  Timer? _statusPoller;

  @override
  void initState() {
    super.initState();
    _workplaces = widget.api.list('partners/my-workplaces');
    _vehiclePublicId = widget.initialVehiclePublicId;
    _vehiclePlateNumber = widget.initialPlateNumber;
    _loadingBalance = true;
    _primeScannedVehicle();
  }

  Future<void> _primeScannedVehicle() async {
    try {
      final workplaces = await _workplaces;
      if (!mounted) return;
      if (workplaces.isEmpty) {
        setState(() {
          _loadingBalance = false;
          _error = '협력업체 권한을 확인할 수 없습니다.';
        });
        return;
      }
      _selectedPartner = workplaces.firstWhere(
          (partner) => partner['id'] == widget.initialPartnerId,
          orElse: () => workplaces.first);
      await _loadPointBalance();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loadingBalance = false;
        _error = error.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  @override
  void dispose() {
    _statusPoller?.cancel();
    _amount.dispose();
    _points.dispose();
    super.dispose();
  }

  Future<void> _scanVehicle() async {
    final publicId = await Navigator.of(context).push<String>(
        MaterialPageRoute(builder: (_) => const ScanVehicleQrPage()));
    if (publicId != null && mounted) {
      setState(() {
        _vehiclePublicId = publicId;
        _availablePoints = null;
        _vehiclePlateNumber = null;
        _loadingBalance = true;
        _error = null;
      });
      await _loadPointBalance();
    }
  }

  Future<void> _loadPointBalance() async {
    final publicId = _vehiclePublicId;
    final partnerId = (_selectedPartner?['id'] as num?)?.toInt();
    if (publicId == null || partnerId == null) return;
    setState(() {
      _loadingBalance = true;
      _availablePoints = null;
      _points.clear();
      _error = null;
    });
    try {
      final balance =
          await widget.api.pointBalanceForVehicle(publicId, partnerId);
      if (!mounted || publicId != _vehiclePublicId) return;
      setState(() {
        _availablePoints = (balance['available_points'] as num?)?.toInt() ?? 0;
        _vehiclePlateNumber = balance['plate_number']?.toString();
        _loadingBalance = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loadingBalance = false;
        _error = error.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  void _fillMaximumPoints() {
    final balance = _availablePoints ?? 0;
    final amount = int.tryParse(_amount.text.replaceAll(',', '')) ?? 0;
    _points.text = (balance < amount ? balance : amount).toString();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() ||
        _selectedPartner == null ||
        _vehiclePublicId == null ||
        _availablePoints == null) {
      setState(() => _error = _selectedPartner == null
          ? '협력업체를 선택해 주세요.'
          : _vehiclePublicId == null
              ? '회원의 차량 QR을 스캔해 주세요.'
              : _availablePoints == null
                  ? 'QR의 사용 가능 포인트를 먼저 확인해 주세요.'
                  : null);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final request = await widget.api.createPointRedemption({
        'vehicle_public_id': _vehiclePublicId,
        'partner': _selectedPartner!['id'],
        'payment_amount_krw': int.parse(_amount.text.replaceAll(',', '')),
        'points_requested': int.parse(_points.text.replaceAll(',', '')),
      });
      if (!mounted) return;
      setState(() {
        _request = request;
        _approvedRedemptionId = null;
        _busy = false;
      });
      _statusPoller = Timer.periodic(const Duration(seconds: 2), (_) {
        _refreshRequestStatus();
      });
      _refreshRequestStatus();
    } catch (error) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = error.toString().replaceFirst('Exception: ', '');
        });
      }
    }
  }

  Future<void> _refreshRequestStatus() async {
    final id = (_request?['id'] as num?)?.toInt();
    if (id == null || !mounted) return;
    try {
      final refreshed = await widget.api.readPointRedemption(id);
      if (!mounted) return;
      setState(() {
        _request = refreshed;
        if (refreshed['status'] == 'completed') {
          _approvedRedemptionId = (refreshed['id'] as num?)?.toInt();
        }
      });
      if (refreshed['status'] != 'pending') {
        _statusPoller?.cancel();
        _statusPoller = null;
      }
    } catch (_) {
      // Keep polling until the request expires or the connection returns.
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('포인트 사용 승인')),
        body: FutureBuilder<List<Map<String, dynamic>>>(
          future: _workplaces,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: MiniDriveLoader(compact: true));
            }
            if (snapshot.hasError) {
              return Center(
                  child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(snapshot.error.toString()),
              ));
            }
            final workplaces = snapshot.data ?? const [];
            if (_selectedPartner == null && workplaces.isNotEmpty) {
              _selectedPartner = workplaces.first;
            }
            final request = _request;
            if (request != null) {
              final status = request['status']?.toString() ?? 'pending';
              final finished = status != 'pending';
              final statusText = switch (status) {
                'completed' => '회원이 승인했습니다. 포인트 결제를 완료해 주세요.',
                'rejected' => '회원이 포인트 사용을 거절했습니다.',
                'expired' => '요청 시간이 만료되었습니다. 다시 요청해 주세요.',
                _ => '회원 앱에서 승인 대기 중입니다. 회원이 앱을 열면 승인 화면이 표시됩니다.',
              };
              return Center(
                  child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 520),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(22),
                      child: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Icon(
                                finished ? Icons.verified : Icons.hourglass_top,
                                size: 48,
                                color: brandRed),
                            const SizedBox(height: 16),
                            Text(statusText,
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                    fontSize: 17, fontWeight: FontWeight.w800)),
                            const SizedBox(height: 12),
                            Text(
                                '총액 ${formatKilometers((request['payment_amount_krw'] as num?)?.toInt() ?? 0)}원 · 포인트 −${formatKilometers((request['points_requested'] as num?)?.toInt() ?? 0)}P\n실결제 ${formatKilometers((request['actual_payment_krw'] as num?)?.toInt() ?? (((request['payment_amount_krw'] as num?)?.toInt() ?? 0) - ((request['points_requested'] as num?)?.toInt() ?? 0)))}원',
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                    height: 1.5, fontWeight: FontWeight.w700)),
                            if (finished && status == 'completed') ...[
                              const SizedBox(height: 10),
                              const Text(
                                '포인트를 사용한 결제 건은 추가 포인트가 적립되지 않습니다.',
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 10),
                              OutlinedButton.icon(
                                onPressed: _approvedRedemptionId == null
                                    ? null
                                    : () async {
                                        final partnerId =
                                            (_selectedPartner?['id'] as num?)
                                                ?.toInt();
                                        final saved =
                                            await Navigator.of(context)
                                                .push<bool>(
                                          MaterialPageRoute(
                                              builder: (_) => PartnerRecordPage(
                                                    api: widget.api,
                                                    initialPartnerId: partnerId,
                                                    initialPlateNumber:
                                                        _vehiclePlateNumber,
                                                    initialVehiclePublicId:
                                                        _vehiclePublicId,
                                                    pointRedemptionId:
                                                        _approvedRedemptionId,
                                                    initialAmountKrw: (request[
                                                                'actual_payment_krw']
                                                            as num?)
                                                        ?.toInt(),
                                                    initialPointsUsed: (request[
                                                                'points_requested']
                                                            as num?)
                                                        ?.toInt(),
                                                  )),
                                        );
                                        if (saved == true && mounted) {
                                          setState(() {
                                            _request = null;
                                            _vehiclePublicId = null;
                                            _availablePoints = null;
                                            _vehiclePlateNumber = null;
                                            _approvedRedemptionId = null;
                                            _amount.clear();
                                            _points.clear();
                                          });
                                        }
                                      },
                                icon: const Icon(Icons.receipt_long_outlined),
                                label: const Text('포인트 사용 정비기록 등록'),
                              ),
                            ],
                            if (finished) ...[
                              const SizedBox(height: 20),
                              FilledButton(
                                  onPressed: () => setState(() {
                                        _request = null;
                                        _vehiclePublicId = null;
                                        _availablePoints = null;
                                        _vehiclePlateNumber = null;
                                        _approvedRedemptionId = null;
                                        _amount.clear();
                                        _points.clear();
                                      }),
                                  child: const Text('다음 요청')),
                            ],
                          ]),
                    ),
                  ),
                ),
              ));
            }
            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Form(
                      key: _formKey,
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            const Text('회원 포인트 사용 요청',
                                style: TextStyle(
                                    fontSize: 19, fontWeight: FontWeight.w900)),
                            const SizedBox(height: 6),
                            const Text(
                                '회원 QR을 스캔해 사용 가능 포인트를 확인한 뒤 금액을 선택하세요.'),
                            const SizedBox(height: 18),
                            DropdownButtonFormField<Map<String, dynamic>>(
                              initialValue: _selectedPartner,
                              decoration:
                                  const InputDecoration(labelText: '협력업체'),
                              items: workplaces
                                  .map((partner) => DropdownMenuItem(
                                        value: partner,
                                        child: Text(
                                            '${partner['name'] ?? '협력업체'}${(partner['branch_label'] ?? '').toString().isEmpty ? '' : ' · ${partner['branch_label']}'}'),
                                      ))
                                  .toList(),
                              onChanged: _busy
                                  ? null
                                  : (partner) {
                                      setState(
                                          () => _selectedPartner = partner);
                                      if (_vehiclePublicId != null)
                                        _loadPointBalance();
                                    },
                            ),
                            const SizedBox(height: 12),
                            if (_vehiclePublicId != null)
                              ListTile(
                                contentPadding: EdgeInsets.zero,
                                leading: const Icon(Icons.qr_code_2),
                                title: const Text('회원 차량 QR 확인 완료'),
                                subtitle: Text(
                                    '${_vehiclePlateNumber ?? '차량 확인됨'} · 사용 포인트 확인'),
                              )
                            else
                              OutlinedButton.icon(
                                  onPressed: _busy ? null : _scanVehicle,
                                  icon: const Icon(Icons.qr_code_scanner),
                                  label: const Text('회원 차량 QR 스캔')),
                            const SizedBox(height: 12),
                            if (_loadingBalance)
                              const LinearProgressIndicator()
                            else if (_availablePoints != null)
                              Card(
                                color: Theme.of(context)
                                    .colorScheme
                                    .surfaceContainerHighest,
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 14, vertical: 12),
                                  child: Row(
                                    children: [
                                      const Icon(Icons
                                          .account_balance_wallet_outlined),
                                      const SizedBox(width: 10),
                                      const Expanded(child: Text('사용 가능 포인트')),
                                      Text(
                                          '${formatKilometers(_availablePoints!)} P',
                                          style: const TextStyle(
                                              fontWeight: FontWeight.w900,
                                              color: brandRed)),
                                    ],
                                  ),
                                ),
                              ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _amount,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                  labelText: '결제 금액', suffixText: '원'),
                              validator: (value) => int.tryParse((value ?? '')
                                              .replaceAll(',', '')) ==
                                          null ||
                                      int.parse((value ?? '')
                                              .replaceAll(',', '')) <
                                          1
                                  ? '결제 금액을 입력해 주세요.'
                                  : null,
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _points,
                              enabled:
                                  _availablePoints != null && !_loadingBalance,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                  labelText: '사용할 포인트', suffixText: 'P'),
                              validator: (value) {
                                final points = int.tryParse(
                                    (value ?? '').replaceAll(',', ''));
                                final amount = int.tryParse(
                                    _amount.text.replaceAll(',', ''));
                                if (points == null || points < 1) {
                                  return '사용할 포인트를 입력해 주세요.';
                                }
                                if (amount != null && points > amount) {
                                  return '포인트는 결제 금액을 넘을 수 없습니다.';
                                }
                                if (points > (_availablePoints ?? 0)) {
                                  return '사용 가능한 포인트를 넘을 수 없습니다.';
                                }
                                return null;
                              },
                            ),
                            if (_availablePoints != null &&
                                _availablePoints! > 0)
                              Align(
                                alignment: Alignment.centerRight,
                                child: TextButton.icon(
                                  onPressed: _fillMaximumPoints,
                                  icon: const Icon(Icons.done_all),
                                  label: const Text('사용 가능 포인트 전액'),
                                ),
                              ),
                            if (_error != null) ...[
                              const SizedBox(height: 12),
                              Text(_error!,
                                  style: TextStyle(
                                      color:
                                          Theme.of(context).colorScheme.error)),
                            ],
                            const SizedBox(height: 18),
                            FilledButton.icon(
                              onPressed: _busy ||
                                      workplaces.isEmpty ||
                                      _availablePoints == null ||
                                      _loadingBalance
                                  ? null
                                  : _submit,
                              icon: _busy
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2))
                                  : const Icon(Icons.send_rounded),
                              label: Text(_busy ? '요청 중…' : '회원에게 승인 요청'),
                            ),
                          ]),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      );
}

class _PartnerToolButton extends StatelessWidget {
  const _PartnerToolButton({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.height,
    required this.onPressed,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final double height;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => SizedBox(
        height: height,
        child: FilledButton(
          style: FilledButton.styleFrom(
            backgroundColor: brandRed,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
          ),
          onPressed: onPressed,
          child: Row(
            children: [
              Icon(icon, size: 36),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        style: const TextStyle(
                            fontSize: 19, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 3),
                    Text(subtitle,
                        style: const TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, size: 28),
            ],
          ),
        ),
      );
}

class PartnerBookingCalendarPage extends StatefulWidget {
  const PartnerBookingCalendarPage({required this.api, super.key});
  final ApiClient api;

  @override
  State<PartnerBookingCalendarPage> createState() =>
      _PartnerBookingCalendarPageState();
}

class _PartnerBookingCalendarPageState
    extends State<PartnerBookingCalendarPage> {
  late Future<List<Map<String, dynamic>>> future;
  late DateTime month;
  late DateTime selectedDay;

  @override
  void initState() {
    super.initState();
    final today = DateTime.now();
    month = DateTime(today.year, today.month);
    selectedDay = DateTime(today.year, today.month, today.day);
    reload();
  }

  void reload() => future = widget.api.list('bookings');

  DateTime? _dateOf(Map<String, dynamic> row) =>
      DateTime.tryParse(row['scheduled_at']?.toString() ?? '')?.toLocal();

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  List<Map<String, dynamic>> _activeBookings(List<Map<String, dynamic>> rows) =>
      rows.where((row) {
        final status = row['status']?.toString();
        return row['can_manage'] == true &&
            (status == 'requested' || status == 'confirmed');
      }).toList();

  Future<void> _act(Future<void> Function() action) async {
    try {
      await action();
      if (mounted) setState(reload);
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(error.toString().replaceFirst('Exception: ', '')),
        ));
    }
  }

  Future<void> _openRecord(Map<String, dynamic> row) async {
    final plate = (row['vehicle_plate_number'] ?? '').toString();
    if (plate.isEmpty) return;
    final saved = await Navigator.of(context).push<bool>(MaterialPageRoute(
        builder: (_) => PartnerRecordPage(
              api: widget.api,
              initialPlateNumber: plate,
              initialPartnerId: row['partner'] as int?,
            )));
    if (saved == true && mounted) setState(reload);
  }

  Widget _calendar(List<Map<String, dynamic>> rows) {
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    final firstWeekday = DateTime(month.year, month.month, 1).weekday % 7;
    final daysInMonth = DateUtils.getDaysInMonth(month.year, month.month);
    final cells = ((firstWeekday + daysInMonth + 6) ~/ 7) * 7;
    final today = DateTime.now();
    return Card(
        child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(children: [
              Row(children: [
                IconButton(
                    tooltip: '이전 달',
                    onPressed: () => setState(() {
                          month = DateTime(month.year, month.month - 1);
                        }),
                    icon: const Icon(Icons.chevron_left)),
                Expanded(
                    child: Center(
                        child: Text('${month.year}년 ${month.month}월',
                            style: const TextStyle(
                                fontSize: 18, fontWeight: FontWeight.w900)))),
                IconButton(
                    tooltip: '다음 달',
                    onPressed: () => setState(() {
                          month = DateTime(month.year, month.month + 1);
                        }),
                    icon: const Icon(Icons.chevron_right)),
              ]),
              Row(
                  children: weekdays
                      .map((day) => Expanded(
                              child: Center(
                                  child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Text(day,
                                style: TextStyle(
                                    fontWeight: FontWeight.w800,
                                    color: day == '일'
                                        ? brandRed
                                        : Theme.of(context)
                                            .colorScheme
                                            .onSurfaceVariant)),
                          ))))
                      .toList()),
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: cells,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 7,
                  mainAxisExtent: 46,
                ),
                itemBuilder: (context, index) {
                  final dayNumber = index - firstWeekday + 1;
                  if (dayNumber < 1 || dayNumber > daysInMonth)
                    return const SizedBox.shrink();
                  final date = DateTime(month.year, month.month, dayNumber);
                  final count = rows.where((row) {
                    final scheduled = _dateOf(row);
                    return scheduled != null && _sameDay(scheduled, date);
                  }).length;
                  final isSelected = _sameDay(date, selectedDay);
                  final isToday = _sameDay(
                      date, DateTime(today.year, today.month, today.day));
                  return InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: () => setState(() => selectedDay = date),
                    child: Container(
                      margin: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        color: isSelected ? brandRed : null,
                        borderRadius: BorderRadius.circular(12),
                        border: isToday && !isSelected
                            ? Border.all(color: brandRed)
                            : null,
                      ),
                      child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text('$dayNumber',
                                style: TextStyle(
                                    fontWeight: isSelected || isToday
                                        ? FontWeight.w900
                                        : FontWeight.w500,
                                    color: isSelected
                                        ? Colors.white
                                        : Theme.of(context)
                                            .colorScheme
                                            .onSurface)),
                            if (count > 0)
                              Container(
                                width: count > 1 ? 16 : 5,
                                height: 5,
                                decoration: BoxDecoration(
                                    color: isSelected ? Colors.white : brandRed,
                                    borderRadius: BorderRadius.circular(8)),
                                alignment: Alignment.center,
                                child: count > 1
                                    ? Text('$count',
                                        style: const TextStyle(
                                            fontSize: 8,
                                            color: Colors.white,
                                            height: 1))
                                    : null,
                              ),
                          ]),
                    ),
                  );
                },
              ),
              const SizedBox(height: 4),
              Row(children: [
                Container(
                    width: 7,
                    height: 7,
                    decoration: const BoxDecoration(
                        color: brandRed, shape: BoxShape.circle)),
                const SizedBox(width: 6),
                const Text('예약 차량이 있는 날짜')
              ]),
            ])));
  }

  Widget _bookingCard(Map<String, dynamic> row) {
    final status = row['status']?.toString() ?? '';
    final date = _dateOf(row);
    final vehicle = row['vehicle'] is Map
        ? Map<String, dynamic>.from(row['vehicle'] as Map)
        : const <String, dynamic>{};
    final model = (row['vehicle_model_name'] ??
            row['vehicle_name'] ??
            row['model_name'] ??
            vehicle['model_name'] ??
            vehicle['name'] ??
            '예약 차량')
        .toString();
    final plate = (row['vehicle_plate_number'] ?? vehicle['plate_number'] ?? '')
        .toString();
    final time = date == null
        ? '시간 미정'
        : '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    final statusLabel =
        (row['status_label'] ?? (status == 'requested' ? '접수 대기' : '예약 확정'))
            .toString();
    return Card(
        child: Padding(
            padding: const EdgeInsets.all(14),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(Icons.directions_car_outlined,
                    color: brandRed, size: 26),
                const SizedBox(width: 10),
                Expanded(
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                      Text(model,
                          style: const TextStyle(
                              fontSize: 17, fontWeight: FontWeight.w900)),
                      if (plate.isNotEmpty)
                        Text(plate,
                            style: TextStyle(
                                color: Theme.of(context)
                                    .colorScheme
                                    .onSurfaceVariant,
                                fontWeight: FontWeight.w700)),
                      const SizedBox(height: 5),
                      Text(
                          '$time · ${row['service_type'] ?? '방문 예약'} · $statusLabel',
                          style: TextStyle(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurfaceVariant)),
                      if ((row['customer_note'] ?? '')
                          .toString()
                          .trim()
                          .isNotEmpty)
                        Padding(
                            padding: const EdgeInsets.only(top: 5),
                            child: Text(row['customer_note'].toString())),
                    ])),
              ]),
              if (status == 'requested') ...[
                const SizedBox(height: 10),
                Row(mainAxisAlignment: MainAxisAlignment.end, children: [
                  TextButton(
                      onPressed: () => _act(() => widget.api
                          .respondToPartnerBooking(row['id'] as int,
                              status: 'rejected')),
                      child: const Text('거절')),
                  const SizedBox(width: 8),
                  FilledButton(
                      onPressed: () => _act(() => widget.api
                          .respondToPartnerBooking(row['id'] as int,
                              status: 'confirmed')),
                      child: const Text('예약 확정')),
                ]),
              ],
              if (status == 'confirmed') ...[
                const SizedBox(height: 8),
                Wrap(
                    alignment: WrapAlignment.end,
                    spacing: 8,
                    runSpacing: 4,
                    children: [
                      if (row['can_verify_records'] == true && plate.isNotEmpty)
                        OutlinedButton.icon(
                            onPressed: () => _openRecord(row),
                            icon: const Icon(Icons.qr_code_scanner),
                            label: const Text('차량 확인')),
                      TextButton.icon(
                          onPressed: () => _act(() => widget.api
                              .respondToPartnerBooking(row['id'] as int,
                                  status: 'completed')),
                          icon: const Icon(Icons.check_circle_outline),
                          label: const Text('작업 완료')),
                    ]),
              ],
            ])));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('업체 예약 캘린더'), actions: [
          IconButton(
              tooltip: '새로고침',
              onPressed: () => setState(reload),
              icon: const Icon(Icons.refresh)),
        ]),
        body: FutureBuilder<List<Map<String, dynamic>>>(
          future: future,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting)
              return const Center(child: MiniDriveLoader());
            if (snapshot.hasError)
              return ListView(padding: const EdgeInsets.all(20), children: [
                const InfoCard(
                    text: '업체 예약을 불러오지 못했습니다. 협력업체 담당자 계정과 연결 상태를 확인해 주세요.'),
                TextButton.icon(
                    onPressed: () => setState(reload),
                    icon: const Icon(Icons.refresh),
                    label: const Text('다시 불러오기')),
              ]);
            final rows = _activeBookings(snapshot.data ?? []);
            final selectedRows = rows.where((row) {
              final date = _dateOf(row);
              return date != null && _sameDay(date, selectedDay);
            }).toList()
              ..sort((a, b) => (_dateOf(a) ?? DateTime(0))
                  .compareTo(_dateOf(b) ?? DateTime(0)));
            return ListView(
                padding: EdgeInsets.fromLTRB(20.0, 16, 20.0, 28),
                children: [
                  const Text('예약 차량 일정',
                      style:
                          TextStyle(fontSize: 23, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 6),
                  Text('날짜를 선택하면 해당일에 예약된 차량과 처리 상태를 확인할 수 있어요.',
                      style: TextStyle(
                          color:
                              Theme.of(context).colorScheme.onSurfaceVariant)),
                  const SizedBox(height: 14),
                  _calendar(rows),
                  const SizedBox(height: 14),
                  Text(
                      '${selectedDay.year}년 ${selectedDay.month}월 ${selectedDay.day}일 예약 · ${selectedRows.length}대',
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  if (selectedRows.isEmpty)
                    const InfoCard(text: '선택한 날짜에 예약된 차량이 없습니다.'),
                  ...selectedRows.map(_bookingCard),
                  if (rows.isEmpty)
                    const InfoCard(text: '확인할 예약이 없습니다. 예약이 접수되면 캘린더에 표시됩니다.'),
                ]);
          },
        ),
      );
}

class CatalogDetailPage extends StatelessWidget {
  const CatalogDetailPage(
      {required this.api, required this.path, required this.item, super.key});
  final ApiClient api;
  final String path;
  final Map<String, dynamic> item;
  Future<void> openLink(BuildContext context, String value) async {
    final uri = Uri.tryParse(value);
    try {
      if (uri == null ||
          !['https', 'http'].contains(uri.scheme) ||
          uri.host.isEmpty ||
          !await launchUrl(uri, mode: LaunchMode.externalApplication))
        throw Exception();
    } catch (_) {
      if (context.mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('원문을 열지 못했습니다.')));
    }
  }

  Future<void> openPartner(BuildContext context) async {
    try {
      final rows = await api.list('partners');
      final partner =
          rows.where((row) => row['id'] == item['partner']).firstOrNull;
      if (!context.mounted) return;
      if (partner == null) throw Exception();
      await Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => PartnerDetailPage(api: api, partner: partner)));
    } catch (_) {
      if (context.mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('업체 정보를 불러오지 못했습니다.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final original = (item['original_url'] ?? '').toString();
    final body = (item['body'] ?? '').toString();
    return Scaffold(
        appBar: AppBar(title: Text(path == 'notices' ? '카페 소식' : '협력업체 혜택')),
        body: ListView(padding: const EdgeInsets.all(20), children: [
          Text((item['title'] ?? '').toString(),
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 16),
          Text(body.isNotEmpty
              ? body
              : (item['summary'] ?? item['description'] ?? '상세 내용이 없습니다.')
                  .toString()),
          if ((item['redemption_instructions'] ?? '')
              .toString()
              .isNotEmpty) ...[
            const SizedBox(height: 16),
            InfoCard(text: item['redemption_instructions'].toString()),
          ],
          if (original.isNotEmpty)
            TextButton.icon(
                onPressed: () => openLink(context, original),
                icon: const Icon(Icons.open_in_new),
                label: const Text('카페 원문 보기')),
          if (path == 'offers' && item['partner'] != null)
            FilledButton.icon(
                onPressed: () => openPartner(context),
                icon: const Icon(Icons.storefront),
                label: const Text('업체 정보 및 문의')),
        ]));
  }
}

class PartnerDetailPage extends StatelessWidget {
  const PartnerDetailPage(
      {required this.api, required this.partner, super.key});
  final ApiClient api;
  final Map<String, dynamic> partner;

  Future<void> _launch(BuildContext context, Uri uri) async {
    try {
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication) &&
          context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('연결할 앱을 열지 못했습니다.')));
      }
    } catch (_) {
      if (context.mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('연결할 앱을 열지 못했습니다.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final name = (partner['name'] ?? '협력업체').toString();
    final branchLabel = (partner['branch_label'] ?? '').toString();
    final phone = (partner['phone'] ?? '').toString();
    final address = (partner['address'] ?? '').toString().trim();
    final region = (partner['region'] ?? '').toString().trim();
    final usableRegion = region.isNotEmpty &&
        !region.contains('확인 필요') &&
        !region.contains('협력업체') &&
        region != '서울/경기';
    final location =
        address.isNotEmpty ? address : (usableRegion ? region : '');
    final mapLink = (partner['map_url'] ?? '').toString().trim();
    final cafeLink = (partner['cafe_url'] ?? '').toString();
    final infoPending =
        (partner['region'] ?? '').toString().contains('확인 필요') &&
            cafeLink.isEmpty;
    final externalActions = partnerExternalActions(name);
    final categories = (partner['service_categories'] as List? ?? const [])
        .map((item) => item.toString())
        .toList();
    final introductionImages =
        (partner['introduction_images'] as List? ?? const [])
            .whereType<Map>()
            .map((row) => Map<String, dynamic>.from(row))
            .where((row) => (row['url'] ?? '').toString().isNotEmpty)
            .toList();
    final introductionPhotoUrls = <String>[
      if ((partner['storefront_photo_url'] ?? '').toString().isNotEmpty)
        partner['storefront_photo_url'].toString(),
      ...introductionImages.map((image) => image['url'].toString()),
    ];
    final details = <Widget>[
      if (location.isNotEmpty)
        ListTile(
            leading: const Icon(Icons.location_on_outlined),
            title: Text(address.isNotEmpty ? '주소' : '지역'),
            subtitle: Text(location)),
      if (phone.isNotEmpty)
        ListTile(
            leading: const Icon(Icons.call_outlined),
            title: const Text('전화번호'),
            subtitle: Text(phone)),
      if ((partner['hours'] ?? '').toString().isNotEmpty)
        ListTile(
            leading: const Icon(Icons.schedule_outlined),
            title: const Text('영업시간'),
            subtitle: Text(partner['hours'].toString())),
    ];
    final suppliedMapUri = Uri.tryParse(mapLink);
    final usableMapUri = suppliedMapUri != null &&
            suppliedMapUri.scheme == 'https' &&
            suppliedMapUri.host.isNotEmpty
        ? suppliedMapUri
        : Uri.https('www.google.com', '/maps/search/', {
            'api': '1',
            'query':
                '$name $branchLabel ${location.isNotEmpty ? location : region}'
                    .trim()
          });
    return Scaffold(
      appBar: AppBar(title: const Text('업체 정보')),
      body: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          children: [
            Container(
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                  color: ink, borderRadius: BorderRadius.circular(22)),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (partner['is_sponsored'] == true)
                      const _SponsoredBadge(),
                    const SizedBox(height: 12),
                    Text(
                        [name, if (branchLabel.isNotEmpty) branchLabel]
                            .join(' · '),
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 25,
                            fontWeight: FontWeight.w900)),
                    if (infoPending) ...[
                      const SizedBox(height: 10),
                      const Chip(
                          avatar: Icon(Icons.info_outline, size: 18),
                          label: Text('정보 확인 중')),
                    ],
                    if ((partner['region'] ?? '').toString().isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(partner['region'].toString(),
                          style: const TextStyle(color: Color(0xFFD7DCDD))),
                    ],
                  ]),
            ),
            const SizedBox(height: 16),
            if (externalActions == null)
              PartnerMap(
                  query:
                      '$name $branchLabel ${address.isEmpty ? partner['region'] ?? '' : address}'),
            if (externalActions != null)
              Row(children: [
                Expanded(
                    child: OutlinedButton(
                        onPressed: () => _launch(
                            context, Uri.parse(externalActions['contact']!)),
                        child: Text(externalActions['label']!))),
                const SizedBox(width: 12),
                Expanded(
                    child: FilledButton(
                        onPressed: () => _launch(
                            context, Uri.parse(externalActions['site']!)),
                        child: const Text('사이트이동'))),
              ]),
            if (categories.isNotEmpty) ...[
              const SizedBox(height: 18),
              Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: categories
                      .map((category) => Chip(label: Text(category)))
                      .toList()),
            ],
            if ((partner['description'] ?? '').toString().isNotEmpty ||
                introductionPhotoUrls.isNotEmpty) ...[
              const SizedBox(height: 18),
              const SectionHeading(title: '업체 소개', subtitle: '서비스 안내'),
              Card(
                  child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (introductionPhotoUrls.isNotEmpty) ...[
                              SizedBox(
                                height: 190,
                                child: ListView.separated(
                                  scrollDirection: Axis.horizontal,
                                  itemCount: introductionPhotoUrls.length,
                                  separatorBuilder: (_, __) =>
                                      const SizedBox(width: 10),
                                  itemBuilder: (context, index) => ClipRRect(
                                    borderRadius: BorderRadius.circular(12),
                                    child: Image.network(
                                      introductionPhotoUrls[index],
                                      width: 280,
                                      height: 190,
                                      fit: BoxFit.cover,
                                      errorBuilder: (_, __, ___) => Container(
                                        width: 280,
                                        height: 190,
                                        alignment: Alignment.center,
                                        color: Theme.of(context)
                                            .colorScheme
                                            .surfaceContainerHighest,
                                        child: const Icon(
                                            Icons.broken_image_outlined,
                                            size: 36),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              if ((partner['description'] ?? '')
                                  .toString()
                                  .isNotEmpty)
                                const SizedBox(height: 12),
                            ],
                            if ((partner['description'] ?? '')
                                .toString()
                                .isNotEmpty)
                              Text(partner['description'].toString(),
                                  style: const TextStyle(height: 1.5)),
                          ]))),
            ],
            if (details.isNotEmpty) ...[
              const SizedBox(height: 18),
              const SectionHeading(title: '기본 정보', subtitle: '방문 전 확인해 주세요'),
              Card(child: Column(children: details)),
            ],
            const SizedBox(height: 12),
            if (phone.isNotEmpty || mapLink.isNotEmpty || location.isNotEmpty)
              Row(children: [
                if (phone.isNotEmpty)
                  Expanded(
                      child: FilledButton.icon(
                          onPressed: () =>
                              _launch(context, Uri(scheme: 'tel', path: phone)),
                          icon: const Icon(Icons.call),
                          label: const Text('전화하기'))),
                if (phone.isNotEmpty &&
                    (mapLink.isNotEmpty || location.isNotEmpty))
                  const SizedBox(width: 10),
                if (mapLink.isNotEmpty || location.isNotEmpty)
                  Expanded(
                      child: OutlinedButton.icon(
                          onPressed: () => _launch(context, usableMapUri),
                          icon: const Icon(Icons.map_outlined),
                          label: const Text('지도보기'))),
              ]),
            PartnerExtraInformation(partner: partner),
            if (infoPending)
              const InfoCard(
                  text:
                      '이 업체는 협력업체 목록에서 확인했지만 지역·연락처·카페 게시글은 아직 확인되지 않았습니다. 확인 전 정보는 표시하지 않습니다.')
            else if (phone.isEmpty && mapLink.isEmpty && location.isEmpty)
              const InfoCard(text: '업체 연락처와 위치는 실제 정보를 등록한 뒤 표시됩니다.'),
            const SizedBox(height: 12),
            if (partner['catalog_only'] == true)
              const InfoCard(
                  text: '이 지점은 위치 확인만 가능합니다. 서버에 지점 등록 후 예약을 연결합니다.'),
            if (externalActions == null && partner['catalog_only'] != true)
              FilledButton.icon(
                onPressed: () async {
                  final result =
                      await Navigator.of(context).push<bool>(MaterialPageRoute(
                    builder: (_) =>
                        PartnerBookingPage(api: api, partner: partner),
                  ));
                  if (result == true && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                        content:
                            Text('업체에 예약 요청을 보냈습니다. MY에서 상태를 확인할 수 있어요.')));
                  }
                },
                icon: const Icon(Icons.calendar_month_outlined),
                label: const Text('예약 요청'),
              ),
            const SizedBox(height: 24),
            const SectionHeading(title: '진행 중인 혜택', subtitle: '협력업체 프로모션'),
            FutureBuilder<List<Map<String, dynamic>>>(
              future: api.list('offers'),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting)
                  return const Center(child: MiniDriveLoader(compact: true));
                if (snapshot.hasError)
                  return const InfoCard(text: '혜택 정보를 불러오지 못했습니다.');
                final partnerId = partner['id'];
                final offers = (snapshot.data ?? [])
                    .where((offer) => offer['partner'] == partnerId)
                    .toList();
                if (offers.isEmpty)
                  return const InfoCard(text: '현재 진행 중인 혜택이 없습니다.');
                return Column(
                    children: offers
                        .map((offer) => Card(
                                child: ListTile(
                              leading: const Icon(Icons.local_offer_outlined),
                              title: Text((offer['title'] ?? '').toString(),
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w800)),
                              subtitle: Text([
                                if ((offer['description'] ?? '')
                                    .toString()
                                    .isNotEmpty)
                                  offer['description'].toString(),
                                if ((offer['redemption_instructions'] ?? '')
                                    .toString()
                                    .isNotEmpty)
                                  '이용 방법: ${offer['redemption_instructions']}',
                              ].join('\n')),
                            )))
                        .toList());
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
        decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(20)),
        child: Text('제휴',
            style: TextStyle(
                color: Theme.of(context).colorScheme.onPrimaryContainer,
                fontSize: 11,
                fontWeight: FontWeight.w900)),
      );
}

class _NewBadge extends StatelessWidget {
  const _NewBadge();
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(right: 6),
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
        decoration: BoxDecoration(
            color: const Color(0xFFFF4E55),
            borderRadius: BorderRadius.circular(20)),
        child: const Text('N',
            style: TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.w900)),
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
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.create('ledger', {
        'vehicle': widget.vehicleId,
        'kind': kind,
        'entry_date': DateTime.now().toIso8601String().substring(0, 10),
        'description': description.text.trim(),
        'amount_krw': int.parse(amount.text.trim()),
        'odometer_km': odometer.text.trim().isEmpty
            ? null
            : int.parse(odometer.text.trim()),
      });
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted)
        setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: const Text('차계부 기록 추가'),
        content: SizedBox(
            width: 420,
            child: SingleChildScrollView(
                child: Form(
                    key: formKey,
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      DropdownButtonFormField<String>(
                          initialValue: kind,
                          decoration: const InputDecoration(labelText: '기록 종류'),
                          items: const [
                            DropdownMenuItem(value: 'fuel', child: Text('주유')),
                            DropdownMenuItem(
                                value: 'service', child: Text('정비')),
                            DropdownMenuItem(value: 'part', child: Text('소모품')),
                            DropdownMenuItem(value: 'wash', child: Text('세차')),
                            DropdownMenuItem(value: 'other', child: Text('기타')),
                          ],
                          onChanged: busy
                              ? null
                              : (value) =>
                                  setState(() => kind = value ?? 'fuel')),
                      TextFormField(
                          controller: description,
                          decoration: const InputDecoration(
                              labelText: '내용', hintText: '예: 셀프 주유'),
                          validator: (value) => value?.trim().isNotEmpty == true
                              ? null
                              : '기록 내용을 입력해 주세요.'),
                      TextFormField(
                          controller: amount,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: '금액 원'),
                          validator: (value) =>
                              int.tryParse(value ?? '') != null &&
                                      int.parse(value!) >= 0
                                  ? null
                                  : '금액을 숫자로 입력해 주세요.'),
                      TextFormField(
                          controller: odometer,
                          keyboardType: TextInputType.number,
                          decoration:
                              const InputDecoration(labelText: '주행거리 km (선택)'),
                          validator: (value) => value == null ||
                                  value.trim().isEmpty ||
                                  (int.tryParse(value.trim()) != null &&
                                      int.parse(value.trim()) >= 0)
                              ? null
                              : '주행거리를 0 이상의 숫자로 입력해 주세요.'),
                      if (error != null)
                        Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Text(error!,
                                style: const TextStyle(color: Colors.red))),
                    ])))),
        actions: [
          TextButton(
              onPressed: busy ? null : () => Navigator.pop(context, false),
              child: const Text('취소')),
          FilledButton(
              onPressed: busy ? null : save,
              child: Text(busy ? '저장 중…' : '저장')),
        ],
      );

  @override
  void dispose() {
    description.dispose();
    amount.dispose();
    odometer.dispose();
    super.dispose();
  }
}

class GaragePage extends StatefulWidget {
  const GaragePage(
      {required this.api,
      required this.signedIn,
      required this.onLogin,
      super.key});
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
    vehiclesFuture = widget.signedIn || ApiClient.demoMode
        ? widget.api.list('vehicles')
        : Future.value([]);
  }

  void reloadVehicles() => setState(() {
        vehiclesFuture = widget.api.list('vehicles');
        maintenanceSummaryFutures.clear();
      });

  Future<Map<String, dynamic>> maintenanceSummary(int vehicleId) =>
      maintenanceSummaryFutures.putIfAbsent(
          vehicleId, () => widget.api.getVehicleMaintenanceSummary(vehicleId));

  Future<void> showRecordEvidence(Map<String, dynamic> entry) async {
    final url = '${entry['evidence_url'] ?? ''}';
    final images = (entry['evidence_images'] as List?)?.cast<Map>() ?? const [];
    if (url.isEmpty && images.isEmpty) return;
    try {
      if (url.endsWith('/evidence/') || images.isNotEmpty) {
        final recordId = entry['id'] as int;
        final photoIds =
            images.map((image) => (image['id'] as num).toInt()).toList();
        final photos = photoIds.isEmpty
            ? [await widget.api.partnerRecordEvidence(recordId)]
            : await Future.wait(photoIds.map((imageId) =>
                widget.api.partnerRecordEvidence(recordId, imageId: imageId)));
        if (!mounted) return;
        await showDialog<void>(
            context: context,
            builder: (context) => Dialog(
                  clipBehavior: Clip.antiAlias,
                  child: PageView.builder(
                    itemCount: photos.length,
                    itemBuilder: (context, index) => InteractiveViewer(
                      child: Image.memory(photos[index], fit: BoxFit.contain),
                    ),
                  ),
                ));
      } else {
        await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      }
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('첨부 사진을 불러오지 못했습니다.')));
    }
  }

  void refreshMaintenanceSummary(int vehicleId) {
    maintenanceSummaryFutures[vehicleId] =
        widget.api.getVehicleMaintenanceSummary(vehicleId);
  }

  Future<void> showVehicleQr(Map<String, dynamic> vehicle) async {
    await showVehiclePassportQr(context, vehicle);
  }

  Future<void> issueTransferCode(int vehicleId) async {
    try {
      final transfer = await widget.api.createVehicleTransferCode(vehicleId);
      if (!mounted) return;
      final code = transfer['code'].toString();
      final expires = transfer['expires_at']
          .toString()
          .replaceFirst('T', ' ')
          .split('.')
          .first;
      await showDialog<void>(
          context: context,
          builder: (dialogContext) => AlertDialog(
                title: const Text('차량 인계 코드'),
                content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(transfer['model_name']?.toString() ?? '등록 차량',
                          style: const TextStyle(fontWeight: FontWeight.w800)),
                      if ((transfer['plate_number'] ?? '')
                          .toString()
                          .isNotEmpty)
                        Text('차량 번호: ${transfer['plate_number']}',
                            style:
                                const TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 12),
                      SelectableText(code,
                          style: const TextStyle(
                              fontSize: 30,
                              letterSpacing: 4,
                              fontWeight: FontWeight.w900)),
                      const SizedBox(height: 8),
                      Text('만료: $expires'),
                      const SizedBox(height: 12),
                      Text(
                          '구매자가 코드를 확인하고 승인하면 차계부 ${transfer['ledger_count']}건(업체 인증 ${transfer['verified_record_count']}건 · 정정 ${transfer['correction_count']}건)과 정비 알림 ${transfer['reminder_count']}건이 함께 전달됩니다. 완료 후 판매자 계정에서는 차량이 사라집니다.',
                          style: const TextStyle(height: 1.45)),
                      const SizedBox(height: 8),
                      const Text('코드는 구매자에게만 전달해 주세요.',
                          style: TextStyle(fontWeight: FontWeight.w800)),
                    ]),
                actions: [
                  TextButton.icon(
                    onPressed: () async {
                      try {
                        await widget.api.cancelVehicleTransfer(vehicleId);
                        if (dialogContext.mounted) Navigator.pop(dialogContext);
                        if (mounted)
                          ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('인계 코드를 취소했습니다.')));
                      } catch (_) {
                        if (dialogContext.mounted)
                          ScaffoldMessenger.of(dialogContext).showSnackBar(
                              const SnackBar(
                                  content: Text(
                                      '코드를 취소하지 못했습니다. 차량 상태를 새로고침해 주세요.')));
                      }
                    },
                    icon: const Icon(Icons.cancel_outlined),
                    label: const Text('코드 취소'),
                  ),
                  TextButton.icon(
                    onPressed: () async {
                      await Clipboard.setData(ClipboardData(text: code));
                      if (dialogContext.mounted)
                        ScaffoldMessenger.of(dialogContext).showSnackBar(
                            const SnackBar(content: Text('인계 코드를 복사했습니다.')));
                    },
                    icon: const Icon(Icons.copy),
                    label: const Text('코드 복사'),
                  ),
                  TextButton(
                      onPressed: () => Navigator.pop(dialogContext),
                      child: const Text('닫기')),
                ],
              ));
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('인계 코드를 만들지 못했습니다. $error')));
    }
  }

  Future<void> acceptVehicleTransfer() async {
    final codeController = TextEditingController();
    String? inputError;
    final result = await showDialog<Map<String, dynamic>>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
            builder: (dialogContext, setDialogState) => AlertDialog(
                  title: const Text('구매한 차량 인계받기'),
                  content: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('판매자가 전달한 10자리 코드를 입력하세요.'),
                        const SizedBox(height: 12),
                        TextField(
                            controller: codeController,
                            textCapitalization: TextCapitalization.characters,
                            maxLength: 10,
                            decoration: const InputDecoration(
                                labelText: '인계 코드', counterText: '')),
                        if (inputError != null)
                          Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(inputError!,
                                  style: const TextStyle(color: Colors.red))),
                      ]),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(dialogContext),
                        child: const Text('취소')),
                    FilledButton(
                        onPressed: () async {
                          if (codeController.text.trim().length != 10) {
                            setDialogState(
                                () => inputError = '10자리 인계 코드를 입력해 주세요.');
                            return;
                          }
                          try {
                            final preview = await widget.api
                                .previewVehicleTransfer(codeController.text);
                            if (dialogContext.mounted)
                              Navigator.pop(dialogContext, {
                                'code':
                                    codeController.text.trim().toUpperCase(),
                                'preview': preview
                              });
                          } catch (_) {
                            if (dialogContext.mounted)
                              setDialogState(() => inputError =
                                  '코드를 확인하지 못했습니다. 만료 여부를 확인해 주세요.');
                          }
                        },
                        child: const Text('차량 정보 확인')),
                  ],
                )));
    codeController.dispose();
    if (result == null || !mounted) return;
    final preview = result['preview'] as Map<String, dynamic>;
    final year =
        preview['model_year'] == null ? '' : ' · ${preview['model_year']}년식';
    final generation = (preview['generation'] ?? '').toString().trim();
    final plateNumber = (preview['plate_number'] ?? '').toString().trim();
    final odometer = preview['current_odometer_km'] == null
        ? '미등록'
        : '${preview['current_odometer_km']} km';
    String incomingRelationship = 'owned';
    final acceptedRelationship = await showDialog<String?>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
            builder: (dialogContext, setDialogState) => AlertDialog(
                  title: const Text('차량과 기록을 인계받을까요?'),
                  content: SingleChildScrollView(
                      child: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                        Text(
                          '${preview['model_name'] ?? 'MINI'}$year${generation.isEmpty ? '' : ' · $generation'}\n'
                          '차량 번호: ${plateNumber.isEmpty ? '미등록' : plateNumber}\n'
                          '현재 주행거리: $odometer\n'
                          '차계부 ${preview['ledger_count']}건 · 업체 실차 확인 기록 ${preview['verified_record_count']}건 · 정정 이력 ${preview['correction_count']}건\n'
                          '정비 알림 ${preview['reminder_count']}건\n\n'
                          '이 차량을 이용하는 형태를 선택해 주세요. 등록 정보는 법적 소유권을 확인하지 않습니다. 차량과 판매자를 확인한 뒤 승인하세요.',
                          style: const TextStyle(height: 1.5),
                        ),
                        DropdownButtonFormField<String>(
                            initialValue: incomingRelationship,
                            decoration:
                                const InputDecoration(labelText: '내 차량 이용 형태'),
                            items: const [
                              DropdownMenuItem(
                                  value: 'owned', child: Text('자가 차량')),
                              DropdownMenuItem(
                                  value: 'lease', child: Text('리스 차량')),
                              DropdownMenuItem(
                                  value: 'rental', child: Text('렌트 차량')),
                              DropdownMenuItem(
                                  value: 'family', child: Text('가족 차량')),
                              DropdownMenuItem(
                                  value: 'other', child: Text('기타 이용 차량')),
                            ],
                            onChanged: (value) => setDialogState(
                                () => incomingRelationship = value ?? 'owned')),
                      ])),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(dialogContext),
                        child: const Text('취소')),
                    FilledButton(
                        onPressed: () =>
                            Navigator.pop(dialogContext, incomingRelationship),
                        child: const Text('인계 승인')),
                  ],
                )));
    if (acceptedRelationship == null) return;
    try {
      final transferred = await widget.api.acceptVehicleTransfer(
          result['code'].toString(), acceptedRelationship);
      final vehicle = transferred['vehicle'] as Map<String, dynamic>;
      if (!mounted) return;
      setState(() {
        selectedVehicleId = vehicle['id'] as int;
        vehiclesFuture = widget.api.list('vehicles');
      });
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('차량과 차계부 기록을 인계받았습니다.')));
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('차량 인계를 완료하지 못했습니다. $error')));
    }
  }

  Future<void> addVehicle() async {
    final formKey = GlobalKey<FormState>();
    final model = TextEditingController();
    final generation = TextEditingController();
    final plate = TextEditingController();
    final odometer = TextEditingController();
    const fieldPadding = EdgeInsets.symmetric(horizontal: 16, vertical: 16);
    String? error;
    String useRelationship = 'owned';
    Uint8List? vehiclePhotoBytes;
    String? vehiclePhotoStatus;
    bool isPreparingVehiclePhoto = false;
    bool vehiclePhotoSaveFailed = false;

    Future<void> chooseVehiclePhoto(StateSetter setDialogState) async {
      final picked = await ImagePicker().pickImage(
          source: ImageSource.gallery,
          imageQuality: 84,
          maxWidth: 1800,
          maxHeight: 1800);
      if (picked == null) return;
      final original = await picked.readAsBytes();
      setDialogState(() {
        vehiclePhotoBytes = original;
        vehiclePhotoStatus = '배경을 제거하고 있어요…';
        isPreparingVehiclePhoto = true;
      });
      try {
        final cutout = await removeVehiclePhotoBackground(context, original);
        setDialogState(() {
          vehiclePhotoBytes = cutout ?? original;
          vehiclePhotoStatus = cutout == null
              ? '원본 사진을 사용합니다.'
              : '배경을 제거했습니다. 차량 가장자리를 확인해 주세요.';
          isPreparingVehiclePhoto = false;
        });
      } catch (_) {
        setDialogState(() {
          vehiclePhotoBytes = original;
          vehiclePhotoStatus = '자동 배경 제거에 실패해 원본 사진을 사용합니다.';
          isPreparingVehiclePhoto = false;
        });
      }
    }

    final created = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
            builder: (dialogContext, setDialogState) => AlertDialog(
                  title: const Text('내 차량 등록'),
                  content: SizedBox(
                      width: 420,
                      child: SingleChildScrollView(
                          child: Form(
                              key: formKey,
                              child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    VehicleCatalogPicker(
                                      modelController: model,
                                      generationController: generation,
                                    ),
                                    TextFormField(
                                        controller: plate,
                                        textCapitalization:
                                            TextCapitalization.characters,
                                        decoration: const InputDecoration(
                                            labelText: '차량 번호판 *',
                                            hintText: '예: 12가3456',
                                            contentPadding: fieldPadding),
                                        validator: (v) => _isValidKoreanPlate(v)
                                            ? null
                                            : '차량 번호를 확인해 주세요. 예: 12가3456'),
                                    DropdownButtonFormField<String>(
                                        initialValue: useRelationship,
                                        decoration: const InputDecoration(
                                            labelText: '차량 이용 형태 *',
                                            contentPadding: fieldPadding),
                                        items: const [
                                          DropdownMenuItem(
                                              value: 'owned',
                                              child: Text('자가 차량')),
                                          DropdownMenuItem(
                                              value: 'lease',
                                              child: Text('리스 차량')),
                                          DropdownMenuItem(
                                              value: 'rental',
                                              child: Text('렌트 차량')),
                                          DropdownMenuItem(
                                              value: 'family',
                                              child: Text('가족 차량')),
                                          DropdownMenuItem(
                                              value: 'other',
                                              child: Text('기타 이용 차량')),
                                        ],
                                        onChanged: (value) => setDialogState(
                                            () => useRelationship =
                                                value ?? 'owned')),
                                    const Padding(
                                        padding: EdgeInsets.only(top: 6),
                                        child: Text(
                                            '이 선택은 차량 이용 형태를 기록합니다. 법적 소유권을 증명하지 않습니다.',
                                            style: TextStyle(fontSize: 12))),
                                    const SizedBox(height: 8),
                                    TextFormField(
                                        controller: odometer,
                                        keyboardType: TextInputType.number,
                                        decoration: const InputDecoration(
                                            labelText: '현재 주행거리 km *',
                                            contentPadding: fieldPadding),
                                        validator: (v) => (v == null ||
                                                v.trim().isEmpty)
                                            ? '현재 주행거리를 입력해 주세요.'
                                            : int.tryParse(v.trim()) == null ||
                                                    int.parse(v.trim()) < 0
                                                ? '주행거리는 0 이상의 숫자로 입력해 주세요.'
                                                : null),
                                    const SizedBox(height: 12),
                                    Align(
                                        alignment: Alignment.centerLeft,
                                        child: Text('내 차량 사진 (선택)',
                                            style: Theme.of(context)
                                                .textTheme
                                                .labelLarge)),
                                    if (vehiclePhotoBytes != null) ...[
                                      const SizedBox(height: 8),
                                      Container(
                                          height: 138,
                                          width: double.infinity,
                                          padding: const EdgeInsets.all(8),
                                          decoration: BoxDecoration(
                                              color: Theme.of(context)
                                                  .colorScheme
                                                  .surfaceContainerHighest,
                                              borderRadius:
                                                  BorderRadius.circular(12)),
                                          child: Image.memory(
                                              vehiclePhotoBytes!,
                                              fit: BoxFit.contain)),
                                    ],
                                    if (vehiclePhotoStatus != null)
                                      Padding(
                                          padding:
                                              const EdgeInsets.only(top: 6),
                                          child: Text(vehiclePhotoStatus!,
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .bodySmall)),
                                    const SizedBox(height: 6),
                                    Row(children: [
                                      Expanded(
                                          child: OutlinedButton.icon(
                                              onPressed: isPreparingVehiclePhoto
                                                  ? null
                                                  : () => chooseVehiclePhoto(
                                                      setDialogState),
                                              icon: const Icon(
                                                  Icons.image_outlined),
                                              label:
                                                  const Text('사진 선택 · 배경 제거'))),
                                      if (vehiclePhotoBytes != null)
                                        IconButton(
                                            tooltip: '사진 삭제',
                                            onPressed: () => setDialogState(() {
                                                  vehiclePhotoBytes = null;
                                                  vehiclePhotoStatus = null;
                                                }),
                                            icon: const Icon(
                                                Icons.delete_outline)),
                                    ]),
                                    if (error != null)
                                      if (error != null)
                                        Padding(
                                            padding:
                                                const EdgeInsets.only(top: 8),
                                            child: Text(error!,
                                                style: const TextStyle(
                                                    color: Colors.red))),
                                  ])))),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(dialogContext, false),
                        child: const Text('취소')),
                    FilledButton(
                        onPressed: () async {
                          if (!formKey.currentState!.validate()) return;
                          try {
                            await widget.api.create('vehicles', {
                              'model_name': model.text.trim(),
                              'generation': generation.text.trim(),
                              'plate_number': plate.text.trim(),
                              'use_relationship': useRelationship,
                              'current_odometer_km':
                                  int.parse(odometer.text.trim()),
                            });
                            if (vehiclePhotoBytes != null) {
                              try {
                                await VehiclePhotoStorage.saveForPlate(
                                    plate.text.trim(), vehiclePhotoBytes!);
                              } catch (_) {
                                vehiclePhotoSaveFailed = true;
                              }
                            }
                            if (dialogContext.mounted)
                              Navigator.pop(dialogContext, true);
                          } catch (e) {
                            setDialogState(() => error = e.toString());
                          }
                        },
                        child: const Text('등록'))
                  ],
                )));
    // showDialog completes as soon as pop starts; keep controllers alive until
    // the reverse transition has removed the form subtree from the widget tree.
    await Future<void>.delayed(const Duration(milliseconds: 250));
    model.dispose();
    generation.dispose();
    plate.dispose();
    odometer.dispose();
    if (created == true && mounted) {
      reloadVehicles();
      if (vehiclePhotoSaveFailed) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('차량은 등록했지만 사진을 기기에 저장하지 못했습니다.')));
      }
    }
  }

  Future<void> editVehiclePlate(Map<String, dynamic> vehicle) async {
    final id = vehicle['id'] as int;
    final plate =
        TextEditingController(text: (vehicle['plate_number'] ?? '').toString());
    String? error;
    String useRelationship =
        (vehicle['ownership_relationship'] ?? 'other').toString();
    final saved = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
            builder: (dialogContext, setDialogState) => AlertDialog(
                  title: const Text('차량 번호판 등록·변경'),
                  content: Column(mainAxisSize: MainAxisSize.min, children: [
                    TextFormField(
                        controller: plate,
                        autofocus: true,
                        textCapitalization: TextCapitalization.characters,
                        decoration: const InputDecoration(
                            labelText: '차량 번호판', hintText: '예: 12가3456')),
                    DropdownButtonFormField<String>(
                        initialValue: const [
                          'owned',
                          'lease',
                          'rental',
                          'family',
                          'other'
                        ].contains(useRelationship)
                            ? useRelationship
                            : 'other',
                        decoration:
                            const InputDecoration(labelText: '차량 이용 형태'),
                        items: const [
                          DropdownMenuItem(
                              value: 'owned', child: Text('자가 차량')),
                          DropdownMenuItem(
                              value: 'lease', child: Text('리스 차량')),
                          DropdownMenuItem(
                              value: 'rental', child: Text('렌트 차량')),
                          DropdownMenuItem(
                              value: 'family', child: Text('가족 차량')),
                          DropdownMenuItem(
                              value: 'other', child: Text('기타 이용 차량')),
                        ],
                        onChanged: (value) => setDialogState(
                            () => useRelationship = value ?? 'other')),
                    const SizedBox(height: 8),
                    const Text('번호판 변경 이력은 보관됩니다. 이용 형태 선택은 소유권 증명이 아닙니다.',
                        style: TextStyle(fontSize: 12)),
                    if (error != null)
                      Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(error!,
                              style: const TextStyle(color: Colors.red))),
                  ]),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(dialogContext, false),
                        child: const Text('취소')),
                    FilledButton(
                        onPressed: () async {
                          if (!_isValidKoreanPlate(plate.text)) {
                            setDialogState(() => error = '차량 번호 형식을 확인해 주세요.');
                            return;
                          }
                          try {
                            await widget.api.updateVehiclePlate(
                                id, plate.text.trim(), useRelationship);
                            if (dialogContext.mounted)
                              Navigator.pop(dialogContext, true);
                          } catch (e) {
                            setDialogState(() => error =
                                e.toString().replaceFirst('Exception: ', ''));
                          }
                        },
                        child: const Text('저장')),
                  ],
                )));
    // Keep the controller alive until the dialog's reverse transition has
    // removed its TextFormField from the tree.
    await Future<void>.delayed(const Duration(milliseconds: 250));
    plate.dispose();
    if (saved == true && mounted) reloadVehicles();
  }

  Future<void> addLedgerEntry(int vehicleId) async {
    final created = await showDialog<bool>(
      context: context,
      builder: (_) => _LedgerEntryDialog(api: widget.api, vehicleId: vehicleId),
    );
    if (created == true && mounted)
      setState(() {
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
    final created = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
            builder: (dialogContext, setDialogState) => AlertDialog(
                  title: const Text('정비 알림 추가'),
                  content: SizedBox(
                      width: 420,
                      child: SingleChildScrollView(
                          child: Form(
                              key: formKey,
                              child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    TextFormField(
                                        controller: title,
                                        decoration: const InputDecoration(
                                            labelText: '알림 내용',
                                            hintText: '예: 엔진오일 교환'),
                                        validator: (v) =>
                                            (v == null || v.trim().isEmpty)
                                                ? '알림 내용을 입력해 주세요.'
                                                : null),
                                    const SizedBox(height: 10),
                                    OutlinedButton.icon(
                                      onPressed: () async {
                                        final picked = await showDatePicker(
                                            context: dialogContext,
                                            initialDate: dueDate ??
                                                DateTime.now().add(
                                                    const Duration(days: 30)),
                                            firstDate: DateTime.now(),
                                            lastDate: DateTime.now().add(
                                                const Duration(days: 3650)));
                                        if (picked != null)
                                          setDialogState(
                                              () => dueDate = picked);
                                      },
                                      icon: const Icon(
                                          Icons.calendar_month_outlined),
                                      label: Text(dueDate == null
                                          ? '날짜 알림 설정 (선택)'
                                          : '날짜: ${dueDate!.toIso8601String().substring(0, 10)}'),
                                    ),
                                    TextFormField(
                                        controller: odometer,
                                        keyboardType: TextInputType.number,
                                        decoration: const InputDecoration(
                                            labelText: '주행거리 알림 km (선택)',
                                            hintText: '예: 85000'),
                                        validator: (v) => (v != null &&
                                                v.isNotEmpty &&
                                                (int.tryParse(v) == null ||
                                                    int.parse(v) < 0))
                                            ? '주행거리를 숫자로 입력해 주세요.'
                                            : null),
                                    if (error != null)
                                      Padding(
                                          padding:
                                              const EdgeInsets.only(top: 8),
                                          child: Text(error!,
                                              style: const TextStyle(
                                                  color: Colors.red))),
                                  ])))),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(dialogContext, false),
                        child: const Text('취소')),
                    FilledButton(
                        onPressed: () async {
                          if (!formKey.currentState!.validate()) return;
                          if (dueDate == null && odometer.text.trim().isEmpty) {
                            setDialogState(
                                () => error = '날짜 또는 주행거리 중 하나는 설정해 주세요.');
                            return;
                          }
                          try {
                            await widget.api.create('reminders', {
                              'vehicle': vehicleId,
                              'title': title.text.trim(),
                              'due_date':
                                  dueDate?.toIso8601String().substring(0, 10),
                              'due_odometer_km': odometer.text.trim().isEmpty
                                  ? null
                                  : int.parse(odometer.text.trim()),
                            });
                            if (dialogContext.mounted)
                              Navigator.pop(dialogContext, true);
                          } catch (e) {
                            setDialogState(() => error = e.toString());
                          }
                        },
                        child: const Text('알림 저장'))
                  ],
                )));
    // The route result arrives before the dialog's reverse animation finishes.
    // Disposing earlier leaves TextFormFields subscribed to dead controllers.
    await Future<void>.delayed(const Duration(milliseconds: 250));
    title.dispose();
    odometer.dispose();
    if (created == true && mounted)
      setState(() {
        reminderRevision++;
        refreshMaintenanceSummary(vehicleId);
      });
  }

  Future<void> completeReminder(int reminderId, int vehicleId) async {
    try {
      await widget.api.completeReminder(reminderId);
      if (mounted)
        setState(() {
          reminderRevision++;
          refreshMaintenanceSummary(vehicleId);
        });
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('알림을 완료 처리하지 못했습니다. 다시 시도해 주세요.')));
    }
  }

  Future<void> deleteReminder(int reminderId, int vehicleId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('정비 알림 삭제'),
        content: const Text('이 알림을 삭제할까요?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('취소')),
          FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('삭제')),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.api.deleteReminder(reminderId);
      if (mounted) {
        setState(() {
          reminderRevision++;
          refreshMaintenanceSummary(vehicleId);
        });
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('알림을 삭제하지 못했습니다. 다시 시도해 주세요.')));
      }
    }
  }

  Future<void> deleteVehicle(Map<String, dynamic> vehicle) async {
    final vehicleId = vehicle['id'] as int;
    final name = (vehicle['nickname']?.toString().trim().isNotEmpty ?? false)
        ? vehicle['nickname'].toString()
        : (vehicle['model_name'] ?? '등록 차량').toString();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('차량 삭제'),
        content: Text(
            '$name 차량을 삭제할까요? 연결된 차계부와 정비 알림도 함께 삭제됩니다. 업체 인증 정비 기록이 있는 차량은 삭제할 수 없습니다.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('취소')),
          FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('삭제')),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.api.deleteVehicle(vehicleId);
      if (!mounted) return;
      setState(() {
        if (selectedVehicleId == vehicleId) selectedVehicleId = null;
        ledgerRevision++;
        reminderRevision++;
        vehiclesFuture = widget.api.list('vehicles');
        maintenanceSummaryFutures.clear();
      });
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('차량을 삭제했습니다.')));
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', ''))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.signedIn)
      return ListView(padding: const EdgeInsets.all(20), children: [
        const Text('내 차량',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
        const SizedBox(height: 16),
        const InfoCard(text: '로그인 후 내 차량과 차계부를 사용할 수 있어요.'),
        const SizedBox(height: 12),
        FilledButton(onPressed: widget.onLogin, child: const Text('네이버로 로그인')),
      ]);
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: vehiclesFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting)
          return const Center(child: MiniDriveLoader(label: '내 차량을 불러오고 있어요'));
        if (snapshot.hasError)
          return ListView(padding: const EdgeInsets.all(20), children: [
            const Text('내 차량',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
            const SizedBox(height: 16),
            const InfoCard(text: '차량을 불러오지 못했습니다.'),
            FilledButton(
                onPressed: reloadVehicles, child: const Text('다시 불러오기')),
          ]);
        final vehicles = snapshot.data ?? [];
        if (vehicles.isEmpty)
          return ListView(padding: const EdgeInsets.all(20), children: [
            const Text('내 차량',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
            const SizedBox(height: 16),
            const InfoCard(text: '내 차를 등록하고 주유·정비 기록을 모아보세요.'),
            const SizedBox(height: 12),
            FilledButton.icon(
                onPressed: addVehicle,
                icon: const Icon(Icons.add),
                label: const Text('차량 등록')),
            if (!ApiClient.demoMode) ...[
              const SizedBox(height: 8),
              OutlinedButton.icon(
                  onPressed: acceptVehicleTransfer,
                  icon: const Icon(Icons.swap_horiz),
                  label: const Text('구매한 차량 인계 코드 입력')),
            ],
          ]);
        final matchingVehicles =
            vehicles.where((v) => v['id'] == selectedVehicleId).toList();
        final vehicle = matchingVehicles.isNotEmpty
            ? matchingVehicles.first
            : vehicles.first;
        final vehicleId = vehicle['id'] as int;
        return ListView(padding: const EdgeInsets.all(20), children: [
          Row(children: [
            const Expanded(
                child: Text('내 차량',
                    style:
                        TextStyle(fontSize: 24, fontWeight: FontWeight.w900))),
            IconButton(
                onPressed: reloadVehicles,
                tooltip: '차량 새로고침',
                icon: const Icon(Icons.refresh)),
            IconButton(
                onPressed: addVehicle,
                tooltip: '차량 추가',
                icon: const Icon(Icons.add_circle_outline)),
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
                final name =
                    (item['nickname']?.toString().trim().isNotEmpty ?? false)
                        ? item['nickname'].toString()
                        : item['model_name'].toString();
                final selected = id == vehicleId;
                final colors = Theme.of(context).colorScheme;
                return Material(
                  color: selected ? colors.primary : colors.surface,
                  borderRadius: BorderRadius.circular(13),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(13),
                    onTap: () => setState(() {
                      selectedVehicleId = id;
                      ledgerFilter = '전체';
                    }),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 11, vertical: 8),
                      decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(13),
                          border: Border.all(
                              color: selected
                                  ? colors.primary
                                  : colors.outlineVariant)),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text('차량 ${entry.key + 1}',
                                style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    color: selected
                                        ? colors.onPrimary.withValues(alpha: .8)
                                        : colors.onSurfaceVariant)),
                            const SizedBox(height: 3),
                            Text(name,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                    fontSize: 12,
                                    height: 1.2,
                                    fontWeight: FontWeight.w800,
                                    color: selected
                                        ? colors.onPrimary
                                        : colors.onSurface)),
                          ]),
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 10),
          Card(
              child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(children: [
                          Expanded(
                              child: Text(
                                  vehicle['nickname']
                                              ?.toString()
                                              .trim()
                                              .isNotEmpty ==
                                          true
                                      ? vehicle['nickname'].toString()
                                      : vehicle['model_name'].toString(),
                                  style: const TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.w900))),
                          IconButton(
                              onPressed: () => editVehiclePlate(vehicle),
                              tooltip: '차량 번호판 등록·변경',
                              icon: const Icon(Icons.edit_road_outlined)),
                          IconButton(
                              onPressed: () => deleteVehicle(vehicle),
                              tooltip: '차량 삭제',
                              icon: const Icon(Icons.delete_outline)),
                          IconButton(
                              onPressed: () => _openBimmerRefs(context),
                              tooltip: '순정 부품 조회',
                              icon: const Icon(Icons.settings_outlined)),
                        ]),
                        if (hasFavouredF66Photo(vehicle) ||
                            hasMaybachPhoto(vehicle) ||
                            hasMiniVehiclePhoto(vehicle) ||
                            hasBmwVehiclePhoto(vehicle))
                          VehiclePhoto(vehicle: vehicle, height: 132),
                        Text(
                            '차량 번호  ${(vehicle['plate_number'] ?? '').toString().isEmpty ? '미등록' : vehicle['plate_number']}',
                            style:
                                const TextStyle(fontWeight: FontWeight.w700)),
                        Text(
                            '이용 형태  ${_vehicleRelationshipLabel(vehicle['ownership_relationship'])} · 소유권 미확인',
                            style: const TextStyle(fontSize: 12)),
                        Text(
                            [
                              if (vehicle['generation'] != null)
                                vehicle['generation'],
                              if (vehicle['model_year'] != null)
                                '${vehicle['model_year']}년형',
                              '현재 ${vehicle['current_odometer_km'] == null ? '주행거리 미등록' : '${formatKilometers(vehicle['current_odometer_km'])} km'}',
                            ].join(' · '),
                            style: TextStyle(
                                color: Theme.of(context)
                                    .colorScheme
                                    .onSurfaceVariant)),
                      ]))),
          const SizedBox(height: 12),
          FutureBuilder<Map<String, dynamic>>(
            key: ValueKey('maintenance-summary-$vehicleId'),
            future: maintenanceSummary(vehicleId),
            builder: (context, summary) {
              if (summary.connectionState == ConnectionState.waiting)
                return const SizedBox(height: 4);
              if (summary.hasError || summary.data == null)
                return const InfoCard(
                    text: '정비 요약을 불러오지 못했습니다. 새로고침을 눌러 다시 확인해 주세요.');
              final data = summary.data!;
              final last = data['last_maintenance'] as Map<String, dynamic>?;
              final dueDate = data['next_due_date']?.toString();
              final dueKm = data['next_due_odometer_km']?.toString();
              final overdue =
                  (data['overdue_reminder_count'] as num?)?.toInt() ?? 0;
              final nextManagementItems = [
                if (dueDate != null) dueDate,
                if (dueKm != null) '$dueKm km',
              ];
              return Card(
                  child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(children: [
                              const Expanded(
                                  child: Text('정비 이력 요약',
                                      style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w900))),
                              if (overdue > 0)
                                Chip(
                                    avatar: const Icon(
                                        Icons.warning_amber_rounded,
                                        size: 16),
                                    label: Text('기한 경과 $overdue건')),
                            ]),
                            Wrap(spacing: 8, runSpacing: 4, children: [
                              Chip(
                                  label: Text(
                                      '업체 인증 ${data['verified_record_count']}건')),
                              Chip(
                                  label: Text(
                                      '정정 이력 ${data['correction_count']}건')),
                              Chip(
                                  label: Text(
                                      '예정 알림 ${data['pending_reminder_count']}건')),
                            ]),
                            const Divider(),
                            Text(
                                last == null
                                    ? '등록된 정비·소모품 기록이 없습니다.'
                                    : '최근 정비  ${last['entry_date']} · ${last['description']?.toString().isNotEmpty == true ? last['description'] : last['kind']} · ${last['odometer_km'] ?? '주행거리 미입력'} km',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w700)),
                            const SizedBox(height: 6),
                            Text(
                                '다음 관리  ${nextManagementItems.isEmpty ? '일정 미등록' : nextManagementItems.join(' · ')}',
                                style: TextStyle(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .onSurfaceVariant)),
                          ])));
            },
          ),
          const SizedBox(height: 20),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('차량 이력',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
            TextButton.icon(
                onPressed: () => addLedgerEntry(vehicleId),
                icon: const Icon(Icons.add),
                label: const Text('기록 추가'))
          ]),
          FutureBuilder<List<Map<String, dynamic>>>(
              key: ValueKey('ledger-$vehicleId-$ledgerRevision'),
              future: widget.api.list('ledger?vehicle=$vehicleId'),
              builder: (context, records) {
                if (records.connectionState == ConnectionState.waiting)
                  return const Center(child: MiniDriveLoader(compact: true));
                if (records.hasError)
                  return const InfoCard(text: '차계부를 불러오지 못했습니다.');
                final allRecords = records.data ?? [];
                final now = DateTime.now();
                final monthRecords = allRecords.where((entry) {
                  final date =
                      DateTime.tryParse((entry['entry_date'] ?? '').toString());
                  return date != null &&
                      date.year == now.year &&
                      date.month == now.month;
                }).toList();
                int amountFor(Set<String> kinds) => monthRecords
                    .where((entry) => kinds.contains('${entry['kind']}'))
                    .fold<int>(
                        0,
                        (total, entry) =>
                            total +
                            ((entry['amount_krw'] as num?)?.toInt() ?? 0));
                final monthlyTotal =
                    amountFor({'fuel', 'service', 'part', 'wash', 'other'});
                final visibleRecords = ledgerFilter == '전체'
                    ? allRecords
                    : allRecords.where((entry) {
                        final kind = switch ('${entry['kind']}') {
                          'fuel' => '주유',
                          'service' => '정비',
                          'part' => '소모품',
                          'wash' => '세차',
                          _ => '기타',
                        };
                        return kind == ledgerFilter;
                      }).toList();
                return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Card(
                          child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('${now.month}월 차량 지출',
                                        style: TextStyle(
                                            color: Theme.of(context)
                                                .colorScheme
                                                .onSurfaceVariant,
                                            fontWeight: FontWeight.w700)),
                                    const SizedBox(height: 3),
                                    Text(
                                        '₩${monthlyTotal.toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',')}',
                                        style: const TextStyle(
                                            fontSize: 26,
                                            fontWeight: FontWeight.w900)),
                                    const SizedBox(height: 12),
                                    Wrap(spacing: 7, runSpacing: 7, children: [
                                      Chip(
                                          label: Text('주유 ₩${amountFor({
                                            'fuel'
                                          }).toString()}')),
                                      Chip(
                                          label: Text('정비 ₩${amountFor({
                                            'service'
                                          }).toString()}')),
                                      Chip(
                                          label: Text('소모품 ₩${amountFor({
                                            'part'
                                          }).toString()}')),
                                      Chip(
                                          label: Text(
                                              '${monthRecords.length}건 기록')),
                                    ]),
                                  ]))),
                      const SizedBox(height: 12),
                      SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                              children: ['전체', '주유', '정비', '소모품', '세차', '기타']
                                  .map((label) => Padding(
                                        padding:
                                            const EdgeInsets.only(right: 7),
                                        child: ChoiceChip(
                                            label: Text(label),
                                            selected: ledgerFilter == label,
                                            onSelected: (_) => setState(
                                                () => ledgerFilter = label)),
                                      ))
                                  .toList())),
                      if (allRecords.isNotEmpty && visibleRecords.isEmpty)
                        InfoCard(text: '이 종류로 기록한 내역이 없습니다.')
                      else
                        ...visibleRecords.map((entry) {
                          final verified = entry['source'] == 'partner';
                          final integrityValid =
                              entry['integrity_valid'] != false;
                          final partnerName =
                              (entry['partner_name'] ?? '').toString();
                          final partNumber =
                              (entry['part_number'] ?? '').toString();
                          final detail = [
                            '기록 #${entry['id']}',
                            '${entry['entry_date']} · ${entry['odometer_km'] ?? '주행거리 미입력'} km',
                            if (verified && partnerName.isNotEmpty) partnerName,
                            if (entry['corrects'] != null)
                              '정정 기록 #${entry['corrects']} · ${entry['correction_reason'] ?? ''}',
                            if (entry['is_corrected'] == true)
                              '정정된 기록 · 아래 정정 이력 확인',
                            if (partNumber.isNotEmpty) '부품번호 $partNumber',
                            if ((entry['evidence_url'] ?? '')
                                    .toString()
                                    .isNotEmpty ||
                                ((entry['evidence_images'] as List?)
                                        ?.isNotEmpty ??
                                    false))
                              '증빙 사진 ${(entry['evidence_images'] as List?)?.length ?? 1}장 등록',
                          ].join('\n');
                          return Card(
                              child: ListTile(
                            leading: verified
                                ? Icon(
                                    integrityValid
                                        ? Icons.verified
                                        : Icons.gpp_bad_outlined,
                                    color: integrityValid
                                        ? Colors.green
                                        : Colors.red)
                                : const Icon(Icons.edit_note),
                            title: Row(children: [
                              Expanded(
                                  child: Text(entry['description']
                                              ?.toString()
                                              .isNotEmpty ==
                                          true
                                      ? entry['description']
                                      : entry['kind'])),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                    color: verified && integrityValid
                                        ? const Color.fromARGB(45, 76, 175, 80)
                                        : Theme.of(context)
                                            .colorScheme
                                            .surfaceContainerHighest,
                                    borderRadius: BorderRadius.circular(12)),
                                child: Text(
                                    integrityValid
                                        ? (entry['trust_label'] ?? '차주 입력')
                                            .toString()
                                        : '검증 이상',
                                    style: const TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.w800)),
                              ),
                            ]),
                            subtitle: Text(detail),
                            onTap: (entry['evidence_url'] ?? '')
                                        .toString()
                                        .isNotEmpty ||
                                    ((entry['evidence_images'] as List?)
                                            ?.isNotEmpty ??
                                        false)
                                ? () => showRecordEvidence(entry)
                                : null,
                            trailing: Text(entry['details_redacted'] == true
                                ? '이전 이력'
                                : '₩${entry['amount_krw']}'),
                          ));
                        }),
                    ]);
              }),
          const SizedBox(height: 20),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('정비 알림',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
            TextButton.icon(
                onPressed: () => addReminder(vehicleId),
                icon: const Icon(Icons.add),
                label: const Text('알림 추가'))
          ]),
          FutureBuilder<List<Map<String, dynamic>>>(
              key: ValueKey('reminders-$vehicleId-$reminderRevision'),
              future: widget.api.list('reminders?vehicle=$vehicleId'),
              builder: (context, reminders) {
                if (reminders.connectionState == ConnectionState.waiting)
                  return const Center(child: MiniDriveLoader(compact: true));
                if (reminders.hasError)
                  return const InfoCard(text: '정비 알림을 불러오지 못했습니다.');
                final rows = reminders.data ?? [];
                if (rows.isEmpty)
                  return const InfoCard(text: '엔진오일, 검사 일정 등을 알림으로 등록해 보세요.');
                return Column(
                    children: rows.map((reminder) {
                  final complete = reminder['is_complete'] == true;
                  final date = reminder['due_date']?.toString();
                  final km = reminder['due_odometer_km'];
                  final due = date != null ? DateTime.tryParse(date) : null;
                  final today = DateTime.now();
                  final overdue = !complete &&
                      due != null &&
                      DateTime(due.year, due.month, due.day).isBefore(
                          DateTime(today.year, today.month, today.day));
                  final details = [
                    if (date != null) date,
                    if (km != null) '$km km'
                  ].join(' · ');
                  return Card(
                      child: ListTile(
                    leading: Icon(
                        complete
                            ? Icons.check_circle
                            : (overdue
                                ? Icons.warning_amber_rounded
                                : Icons.notifications_active_outlined),
                        color: complete
                            ? Colors.green
                            : (overdue ? Colors.deepOrange : null)),
                    title: Text(reminder['title']?.toString() ?? '정비 알림',
                        style: TextStyle(
                            fontWeight: FontWeight.w800,
                            decoration:
                                complete ? TextDecoration.lineThrough : null)),
                    subtitle: Text(
                        '${details.isEmpty ? '일정 미설정' : details}${overdue ? ' · 예정일 지남' : ''}'),
                    trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                      if (!complete)
                        IconButton(
                            tooltip: '완료 처리',
                            onPressed: () => completeReminder(
                                reminder['id'] as int, vehicleId),
                            icon: const Icon(Icons.check_circle_outline)),
                      IconButton(
                          tooltip: '알림 삭제',
                          onPressed: () =>
                              deleteReminder(reminder['id'] as int, vehicleId),
                          icon: const Icon(Icons.delete_outline)),
                    ]),
                  ));
                }).toList());
              }),
          const SizedBox(height: 20),
          SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                  onPressed: () => addLedgerEntry(vehicleId),
                  icon: const Icon(Icons.add),
                  label: const Text('차계부 기록 추가'))),
          const SizedBox(height: 8),
          if (!ApiClient.demoMode) ...[
            Row(children: [
              Expanded(
                  child: OutlinedButton.icon(
                      onPressed: () => issueTransferCode(vehicleId),
                      icon: const Icon(Icons.share_outlined),
                      label: const Text('판매 차량 인계'))),
              const SizedBox(width: 8),
              Expanded(
                  child: OutlinedButton.icon(
                      onPressed: acceptVehicleTransfer,
                      icon: const Icon(Icons.swap_horiz),
                      label: const Text('구매 차량 인계'))),
            ]),
            const SizedBox(height: 8),
          ],
          OutlinedButton.icon(
              onPressed: () => addReminder(vehicleId),
              icon: const Icon(Icons.notifications_active_outlined),
              label: const Text('정비 알림 추가')),
        ]);
      },
    );
  }
}

class CafeNicknameSection extends StatefulWidget {
  const CafeNicknameSection({required this.api, super.key});
  final ApiClient api;

  @override
  State<CafeNicknameSection> createState() => _CafeNicknameSectionState();
}

class _CafeNicknameSectionState extends State<CafeNicknameSection> {
  late Future<Map<String, dynamic>> _overview;

  @override
  void initState() {
    super.initState();
    _overview = widget.api.memberOverview();
  }

  Future<void> _edit(String current) async {
    var draft = current;
    final nickname = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('카페 닉네임 설정'),
        content: TextFormField(
          initialValue: current,
          onChanged: (value) => draft = value,
          autofocus: true,
          maxLength: 40,
          decoration: const InputDecoration(
            labelText: '아이러브미니 카페 닉네임',
            hintText: '카페에서 사용하는 닉네임을 입력하세요',
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('취소')),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, draft.trim()),
            child: const Text('저장'),
          ),
        ],
      ),
    );
    if (nickname == null || nickname.trim().isEmpty || !mounted) return;
    try {
      await widget.api.updateCafeNickname(nickname);
      if (!mounted) return;
      setState(() {
        _overview = widget.api.memberOverview();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('카페 닉네임을 저장했습니다.')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
        future: _overview,
        builder: (context, snapshot) {
          final nickname = snapshot.data?['cafe_nickname']?.toString() ?? '';
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: Row(children: [
              const Icon(Icons.badge_outlined, color: brandRed),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('카페 닉네임',
                          style: TextStyle(fontWeight: FontWeight.w700)),
                      Text(
                        nickname.isEmpty ? '등록된 닉네임이 없습니다.' : nickname,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                            color:
                                Theme.of(context).colorScheme.onSurfaceVariant),
                      ),
                    ]),
              ),
              TextButton(
                onPressed: snapshot.connectionState == ConnectionState.waiting
                    ? null
                    : () => _edit(nickname),
                child: Text(nickname.isEmpty ? '등록' : '수정'),
              ),
            ]),
          );
        },
      );
}

class AccountPage extends StatelessWidget {
  const AccountPage(
      {required this.api,
      required this.signedIn,
      required this.pushEnabled,
      required this.onPushChanged,
      required this.onLogin,
      required this.onLogout,
      required this.onManageVehicles,
      super.key});
  final ApiClient api;
  final bool signedIn;
  final bool pushEnabled;
  final ValueChanged<bool> onPushChanged;
  final VoidCallback onLogin;
  final VoidCallback onLogout;
  final VoidCallback onManageVehicles;

  Future<void> _deleteAccount(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('회원 계정을 삭제할까요?'),
        content: const Text(
          '로그인 정보와 회원 식별정보, 차량번호 등 차량 식별정보를 삭제합니다. '
          '협력업체 인증 정비 이력은 식별정보와 분리해 최대 1년 보관한 뒤 삭제합니다. '
          '이 작업은 되돌릴 수 없습니다.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: brandRed),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('계정 삭제'),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    try {
      final requirements = await api.accountDeletionRequirements();
      if (!context.mounted) return;
      if (requirements['deletion_available'] != true) {
        throw Exception('Apple 계정 연결 해제 설정을 준비 중입니다. 잠시 후 다시 시도해 주세요.');
      }
      String? appleToken;
      String? appleNonce;
      String? appleCode;
      if (requirements['requires_apple_reauthentication'] == true) {
        appleNonce = generateNonce();
        final credential = await SignInWithApple.getAppleIDCredential(
          scopes: [AppleIDAuthorizationScopes.email],
          nonce: appleNonce,
        );
        appleToken = credential.identityToken;
        appleCode = credential.authorizationCode;
        if (appleToken == null || appleToken.isEmpty || appleCode.isEmpty) {
          throw Exception('Apple 본인 확인을 완료하지 못했습니다. 다시 시도해 주세요.');
        }
      }
      await api.deleteAccount(
          appleIdentityToken: appleToken,
          appleNonce: appleNonce,
          appleAuthorizationCode: appleCode);
      if (!context.mounted) return;
      onLogout();
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('계정과 로그인 정보를 삭제했습니다.')),
        );
      }
    } on SignInWithAppleAuthorizationException catch (error) {
      if (error.code != AuthorizationErrorCode.canceled && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Apple 본인 확인을 완료하지 못했습니다. 다시 시도해 주세요.')),
        );
      }
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text(error.toString().replaceFirst('Exception: ', ''))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) =>
      ListView(padding: const EdgeInsets.all(20), children: [
        Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const Text('MY',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 16),
          MembershipSummaryCard(
            api: api,
            signedIn: signedIn,
            onLogin: onLogin,
            nicknameSection: signedIn && !ApiClient.demoMode
                ? CafeNicknameSection(api: api)
                : null,
          ),
          if (signedIn && !ApiClient.demoMode) ...[
            const SizedBox(height: 12),
            MaintenanceRequests(api: api),
            ListTile(
                leading: const Icon(Icons.history),
                title: const Text('포인트 적립·사용 내역'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => MemberPointHistoryPage(api: api)))),
            MaintenanceReceiptSection(api: api),
          ],
          if (signedIn && !ApiClient.demoMode) ...[
            const SizedBox(height: 12),
            BookingListSection(api: api),
          ],
          const SizedBox(height: 20),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('내 차량',
                style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
            TextButton.icon(
                onPressed: onManageVehicles,
                icon: const Icon(Icons.add),
                label: const Text('차량 추가')),
          ]),
          if (!signedIn && !ApiClient.demoMode)
            const InfoCard(text: '로그인 후 MINI와 다른 차종을 함께 등록할 수 있어요.')
          else
            FutureBuilder<List<Map<String, dynamic>>>(
                future: api.list('vehicles'),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting)
                    return const Center(child: MiniDriveLoader(compact: true));
                  if (snapshot.hasError)
                    return const InfoCard(text: '차량 목록을 불러오지 못했습니다.');
                  final vehicles = snapshot.data ?? [];
                  if (vehicles.isEmpty)
                    return const InfoCard(text: '등록된 차량이 없습니다. 차량을 추가해 주세요.');
                  return Column(
                      children: vehicles.map((vehicle) {
                    final name =
                        (vehicle['nickname']?.toString().trim().isNotEmpty ??
                                false)
                            ? vehicle['nickname'].toString()
                            : (vehicle['model_name'] ?? '등록 차량').toString();
                    final details = [
                      if (vehicle['generation'] != null &&
                          vehicle['generation'].toString().isNotEmpty)
                        vehicle['generation'],
                      if (vehicle['model_year'] != null)
                        '${vehicle['model_year']}년형',
                      if (vehicle['current_odometer_km'] != null)
                        '${formatKilometers(vehicle['current_odometer_km'])} km',
                    ].join(' · ');
                    return Card(
                        child: InkWell(
                            borderRadius: BorderRadius.circular(14),
                            onTap: onManageVehicles,
                            child: Padding(
                              padding: const EdgeInsets.all(14),
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(children: [
                                      Expanded(
                                          child: Text(name,
                                              style: const TextStyle(
                                                  fontWeight:
                                                      FontWeight.w800))),
                                      const Icon(Icons.chevron_right)
                                    ]),
                                    if (hasFavouredF66Photo(vehicle) ||
                                        hasMaybachPhoto(vehicle) ||
                                        hasMiniVehiclePhoto(vehicle) ||
                                        hasBmwVehiclePhoto(vehicle))
                                      VehiclePhoto(
                                          vehicle: vehicle, height: 104),
                                    if (details.isNotEmpty)
                                      Text(details,
                                          style: TextStyle(
                                              color: Theme.of(context)
                                                  .colorScheme
                                                  .onSurfaceVariant)),
                                  ]),
                            )));
                  }).toList());
                }),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: () => _openCafeNotice(context, partnerInquiryUrl),
            icon: const Icon(Icons.storefront_outlined),
            label: const Text('협력업체 입점 문의'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
              onPressed: () => showDialog<void>(
                  context: context,
                  builder: (dialogContext) => AlertDialog(
                        title: const Text('이용약관 · 개인정보 안내'),
                        content: const Text(
                            '아이러브미니 서비스 이용약관과 개인정보 처리방침은 최신 웹 문서에서 확인할 수 있습니다.'),
                        actions: [
                          TextButton(
                              onPressed: () {
                                Navigator.pop(dialogContext);
                                launchUrl(Uri.https(
                                    'ilovemini.onrender.com', '/terms/'));
                              },
                              child: const Text('이용약관 보기')),
                          TextButton(
                              onPressed: () {
                                Navigator.pop(dialogContext);
                                launchUrl(Uri.https(
                                    'ilovemini.onrender.com', '/privacy/'));
                              },
                              child: const Text('개인정보 처리방침')),
                          TextButton(
                              onPressed: () => Navigator.pop(dialogContext),
                              child: const Text('닫기'))
                        ],
                      )),
              icon: const Icon(Icons.description_outlined),
              label: const Text('이용약관 · 개인정보 안내')),
          if (signedIn && !ApiClient.demoMode)
            SwitchListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 14),
              value: pushEnabled,
              onChanged: onPushChanged,
              title: const Text('정비 푸시 알림'),
              subtitle: const Text('설정한 날짜 또는 주행거리에 도달하면 알림을 받아요.'),
              secondary: const Icon(Icons.notifications_active_outlined),
            ),
          const SizedBox(height: 12),
          if (!ApiClient.demoMode)
            FilledButton(
                onPressed: signedIn ? onLogout : onLogin,
                child: Text(signedIn ? '로그아웃' : '로그인 / 가입')),
          if (signedIn && !ApiClient.demoMode) ...[
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => _deleteAccount(context),
              style: TextButton.styleFrom(foregroundColor: brandRed),
              child: const Text('회원 계정 삭제'),
            ),
          ],
          const SizedBox(height: 20),
          ManagedUpdateNotice(api: api),
          const AppVersionLabel(),
        ]),
      ]);
}

class MaintenanceReceiptSection extends StatefulWidget {
  const MaintenanceReceiptSection({required this.api, super.key});
  final ApiClient api;

  @override
  State<MaintenanceReceiptSection> createState() =>
      _MaintenanceReceiptSectionState();
}

class _MaintenanceReceiptSectionState extends State<MaintenanceReceiptSection> {
  late Future<List<Map<String, dynamic>>> _receipts;

  @override
  void initState() {
    super.initState();
    _receipts = _loadReceipts();
  }

  Future<List<Map<String, dynamic>>> _loadReceipts() async {
    final results = await Future.wait([
      widget.api.list('ledger'),
      widget.api.list('vehicles'),
    ]);
    final vehicleById = {
      for (final vehicle in results[1]) '${vehicle['id']}': vehicle,
    };
    return results[0].where((row) {
      return row['source'] == 'partner' &&
          row['verified_at'] != null &&
          row['integrity_valid'] == true &&
          row['details_redacted'] != true &&
          row['is_corrected'] != true;
    }).map((row) {
      final vehicle = vehicleById['${row['vehicle']}'];
      return {
        ...row,
        'receipt_vehicle_name':
            vehicle?['nickname']?.toString().trim().isNotEmpty == true
                ? vehicle!['nickname']
                : vehicle?['model_name'],
        'receipt_plate_number': vehicle?['plate_number'],
      };
    }).toList()
      ..sort((a, b) {
        final byDate = (b['entry_date'] ?? '').toString().compareTo(
              (a['entry_date'] ?? '').toString(),
            );
        if (byDate != 0) return byDate;
        return (b['id'] as num? ?? 0).compareTo(a['id'] as num? ?? 0);
      });
  }

  String _dateHeading(String value) {
    final date = DateTime.tryParse(value);
    if (date == null) return value.isEmpty ? '날짜 미상' : value;
    const weekdays = ['월', '화', '수', '목', '금', '토', '일'];
    return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')} (${weekdays[date.weekday - 1]})';
  }

  String _money(dynamic value) {
    final amount = (value as num?)?.toInt();
    if (amount == null) return '금액 비공개';
    return '₩${amount.toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',')}';
  }

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(children: [
                const Icon(Icons.receipt_long_outlined, color: brandRed),
                const SizedBox(width: 8),
                const Expanded(
                    child: Text('정비 전자영수증',
                        style: TextStyle(
                            fontSize: 17, fontWeight: FontWeight.w900))),
                IconButton(
                  tooltip: '새로고침',
                  visualDensity: VisualDensity.compact,
                  onPressed: () => setState(() => _receipts = _loadReceipts()),
                  icon: const Icon(Icons.refresh),
                ),
              ]),
              Text('협력업체가 인증한 정비 기록과 증빙을 확인할 수 있어요.',
                  style: TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).colorScheme.onSurfaceVariant)),
              const SizedBox(height: 8),
              FutureBuilder<List<Map<String, dynamic>>>(
                future: _receipts,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Padding(
                        padding: EdgeInsets.all(12),
                        child: Center(child: MiniDriveLoader(compact: true)));
                  }
                  if (snapshot.hasError) {
                    return const InfoCard(text: '정비 전자영수증을 불러오지 못했습니다.');
                  }
                  final rows = snapshot.data ?? const [];
                  if (rows.isEmpty) {
                    return const Padding(
                      padding: EdgeInsets.symmetric(vertical: 10),
                      child: Text('아직 업체 인증 정비 기록이 없습니다.'),
                    );
                  }
                  final groups = <String, List<Map<String, dynamic>>>{};
                  for (final row in rows) {
                    final date = (row['entry_date'] ?? '').toString();
                    (groups[date] ??= []).add(row);
                  }
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      for (final group in groups.entries) ...[
                        Padding(
                          padding: const EdgeInsets.only(top: 12, bottom: 4),
                          child: Text(
                            _dateHeading(group.key),
                            style: TextStyle(
                              fontWeight: FontWeight.w900,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                        ),
                        for (final row in group.value)
                          ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading:
                                const Icon(Icons.verified, color: Colors.green),
                            title: Text(
                              (row['partner_name'] ?? '협력업체').toString(),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w800),
                            ),
                            subtitle: Text(
                              '${row['description'] ?? row['kind'] ?? '정비 기록'} · 영수증 보기',
                            ),
                            trailing: Text(
                              _money(row['amount_krw']),
                              style:
                                  const TextStyle(fontWeight: FontWeight.w800),
                            ),
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => MaintenanceReceiptPage(
                                    api: widget.api, entry: row),
                              ),
                            ),
                          ),
                      ],
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      );
}

class MaintenanceReceiptPage extends StatelessWidget {
  const MaintenanceReceiptPage(
      {required this.api, required this.entry, super.key});
  final ApiClient api;
  final Map<String, dynamic> entry;

  String _money(dynamic value) {
    final amount = (value as num?)?.toInt();
    if (amount == null) return '금액 비공개';
    return '₩${amount.toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',')}';
  }

  String _kindLabel(String value) => switch (value) {
        'fuel' => '주유',
        'service' => '정비·소모품',
        'part' => '정비·소모품',
        'wash' => '세차',
        'bodywork' => '판금·도색·보험처리',
        'wheel_tire' => '휠·타이어',
        'electrical' => '전장류',
        _ => '기타',
      };

  @override
  Widget build(BuildContext context) {
    final attachments = (entry['evidence_images'] as List?) ?? const [];
    final lineItems = (entry['line_items'] as List?)
            ?.map((item) => Map<String, dynamic>.from(item as Map))
            .toList() ??
        const <Map<String, dynamic>>[];
    final lineItemsTotal = lineItems.fold<int>(0,
        (total, item) => total + ((item['amount_krw'] as num?)?.toInt() ?? 0));
    final pointsUsed = (entry['points_used'] as num?)?.toInt() ?? 0;
    final partner = (entry['partner_name'] ?? '협력업체').toString();
    return Scaffold(
      appBar: AppBar(title: const Text('정비 전자영수증')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.verified_outlined,
                      color: brandRed, size: 34),
                  const SizedBox(height: 8),
                  Text(partner,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          fontSize: 20, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 4),
                  Text('협력업체 인증 정비 기록',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                          color:
                              Theme.of(context).colorScheme.onSurfaceVariant)),
                  const Divider(height: 28),
                  _ReceiptDetailRow(
                      label: '정비일', value: '${entry['entry_date'] ?? '-'}'),
                  _ReceiptDetailRow(
                      label: '작업 종류',
                      value: _kindLabel('${entry['kind'] ?? ''}')),
                  _ReceiptDetailRow(
                      label: '주행거리',
                      value: entry['odometer_km'] == null
                          ? '-'
                          : '${formatKilometers(entry['odometer_km'])} km'),
                  if ((entry['line_items'] as List?)?.isNotEmpty == true) ...[
                    const SizedBox(height: 8),
                    const Text('정비 내역',
                        style: TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    ...(entry['line_items'] as List).map((rawItem) {
                      final item = Map<String, dynamic>.from(rawItem as Map);
                      return _ReceiptDetailRow(
                        label: (item['description'] ?? '정비 항목').toString(),
                        value: _money(item['amount_krw']),
                      );
                    }),
                    const Divider(height: 20),
                  ],
                  if ((entry['description'] ?? '').toString().isNotEmpty &&
                      ((entry['line_items'] as List?)?.isEmpty ?? true))
                    _ReceiptDetailRow(
                        label: '작업 내용', value: '${entry['description']}'),
                  if ((entry['receipt_vehicle_name'] ?? '')
                      .toString()
                      .isNotEmpty)
                    _ReceiptDetailRow(
                        label: '차량', value: '${entry['receipt_vehicle_name']}'),
                  if ((entry['receipt_plate_number'] ?? '')
                      .toString()
                      .isNotEmpty)
                    _ReceiptDetailRow(
                        label: '차량 번호',
                        value: '${entry['receipt_plate_number']}'),
                  if ((entry['part_number'] ?? '').toString().isNotEmpty)
                    _ReceiptDetailRow(
                        label: '부품번호', value: '${entry['part_number']}'),
                  if ((entry['verified_at'] ?? '').toString().isNotEmpty)
                    _ReceiptDetailRow(
                        label: '인증 일시',
                        value: '${entry['verified_at']}'
                            .replaceFirst('T', ' ')
                            .split('.')
                            .first),
                  const Divider(height: 28),
                  if (lineItems.isNotEmpty)
                    _ReceiptDetailRow(
                        label: '정비 합계', value: _money(lineItemsTotal)),
                  if (pointsUsed > 0)
                    _ReceiptDetailRow(
                        label: '사용 포인트',
                        value: '−${formatKilometers(pointsUsed)} P'),
                  _ReceiptDetailRow(
                      label: lineItems.isNotEmpty ? '실결제 금액' : '기록된 결제 금액',
                      value: _money(entry['amount_krw']),
                      emphasized: true),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color:
                          Theme.of(context).colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                        '이 화면은 협력업체가 등록한 앱 정비 기록입니다. 세무 신고용 영수증이나 카드 결제 증빙을 대신하지 않습니다.',
                        style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),
          ),
          if (attachments.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('업체 첨부 증빙',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            ...attachments.map((attachment) {
              final imageId = (attachment['id'] as num).toInt();
              return Card(
                clipBehavior: Clip.antiAlias,
                child: FutureBuilder<Uint8List>(
                  future: api.partnerRecordEvidence(
                      (entry['id'] as num).toInt(),
                      imageId: imageId),
                  builder: (context, snapshot) {
                    if (snapshot.hasError) {
                      return const ListTile(
                          leading: Icon(Icons.broken_image_outlined),
                          title: Text('첨부 사진을 불러오지 못했습니다.'));
                    }
                    if (!snapshot.hasData) {
                      return const Padding(
                          padding: EdgeInsets.all(24),
                          child: Center(child: MiniDriveLoader(compact: true)));
                    }
                    return Image.memory(snapshot.data!, fit: BoxFit.contain);
                  },
                ),
              );
            }),
          ],
          if ((entry['evidence_url'] ?? '').toString().isNotEmpty &&
              attachments.isEmpty) ...[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => launchUrl(
                Uri.parse(entry['evidence_url'].toString()),
                mode: LaunchMode.externalApplication,
              ),
              icon: const Icon(Icons.open_in_new),
              label: const Text('업체 증빙 열기'),
            ),
          ],
        ],
      ),
    );
  }
}

class _ReceiptDetailRow extends StatelessWidget {
  const _ReceiptDetailRow(
      {required this.label, required this.value, this.emphasized = false});
  final String label;
  final String value;
  final bool emphasized;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(
              width: 112,
              child: Text(label,
                  style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                      fontWeight: emphasized ? FontWeight.w800 : null))),
          Expanded(
              child: Text(value,
                  textAlign: TextAlign.right,
                  style: TextStyle(
                      fontWeight:
                          emphasized ? FontWeight.w900 : FontWeight.w600,
                      fontSize: emphasized ? 18 : null,
                      color: emphasized ? brandRed : null))),
        ]),
      );
}

class AppVersionLabel extends StatefulWidget {
  const AppVersionLabel({super.key});

  @override
  State<AppVersionLabel> createState() => _AppVersionLabelState();
}

class _AppVersionLabelState extends State<AppVersionLabel> {
  late final Future<PackageInfo> _packageInfo = PackageInfo.fromPlatform();

  @override
  Widget build(BuildContext context) => FutureBuilder<PackageInfo>(
        future: _packageInfo,
        builder: (context, snapshot) {
          final info = snapshot.data;
          if (info == null) return const SizedBox.shrink();
          return Center(
            child: Text(
              '버전 ${info.version} · 빌드 ${info.buildNumber}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          );
        },
      );
}

class MembershipSummaryCard extends StatefulWidget {
  const MembershipSummaryCard(
      {required this.api,
      required this.signedIn,
      required this.onLogin,
      this.nicknameSection,
      super.key});
  final ApiClient api;
  final bool signedIn;
  final VoidCallback onLogin;
  final Widget? nicknameSection;
  @override
  State<MembershipSummaryCard> createState() => _MembershipSummaryCardState();
}

class _MembershipSummaryCardState extends State<MembershipSummaryCard> {
  late Future<Map<String, dynamic>> _grade;
  late Future<Map<String, dynamic>> _points;
  bool _checkingIn = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

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
    showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
              title: const Text('회원 등급 안내'),
              content: const Text('''일반회원
기본 가입 회원

미니회원
아이러브미니에서 승인한 MINI 회원

협력업체
아이러브미니에서 등록된 협력업체 담당자'''),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('닫기'))
              ],
            ));
  }

  Future<void> _checkIn() async {
    if (!widget.signedIn && !ApiClient.demoMode) {
      widget.onLogin();
      return;
    }
    setState(() => _checkingIn = true);
    try {
      final result = await widget.api.checkIn();
      if (!mounted) return;
      setState(() => _points = Future.value({
            ...result,
            'checked_in_today': true,
          }));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message']?.toString() ?? '출석 상태를 확인했어요.')));
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('출석 처리에 실패했어요. 잠시 후 다시 시도해 주세요.')));
    } finally {
      if (mounted) setState(() => _checkingIn = false);
    }
  }

  @override
  Widget build(BuildContext context) => Card(
      child: Padding(
          padding: const EdgeInsets.all(16),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Expanded(
                  child: Text('회원등급 · 멤버십',
                      style: TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w900))),
              IconButton(
                  tooltip: '등급안내',
                  visualDensity: VisualDensity.compact,
                  constraints:
                      const BoxConstraints(minWidth: 36, minHeight: 36),
                  padding: EdgeInsets.zero,
                  onPressed: _showGradeGuide,
                  icon: const Icon(Icons.info_outline, size: 21)),
            ]),
            const SizedBox(height: 5),
            if (widget.nicknameSection != null) ...[
              widget.nicknameSection!,
              const Divider(height: 16),
            ],
            FutureBuilder<Map<String, dynamic>>(
                future: _grade,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting)
                    return const Center(child: MiniDriveLoader(compact: true));
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(children: [
                        const Icon(Icons.verified_user_outlined,
                            color: brandRed),
                        const SizedBox(width: 8),
                        const Text('회원 등급',
                            style: TextStyle(fontWeight: FontWeight.w700)),
                        const Spacer(),
                        Text(
                            (snapshot.data?['grade_label'] ?? '등급 확인 불가')
                                .toString(),
                            textAlign: TextAlign.right,
                            style: const TextStyle(
                                color: brandRed, fontWeight: FontWeight.w900)),
                      ]),
                      if (snapshot.data?['grade'] == 'partner')
                        Padding(
                          padding: const EdgeInsets.only(top: 12),
                          child: PartnerToolsShortcuts(api: widget.api),
                        ),
                    ],
                  );
                }),
            const Divider(height: 22),
            FutureBuilder<Map<String, dynamic>>(
                future: _points,
                builder: (context, snapshot) {
                  final data = snapshot.data ?? const <String, dynamic>{};
                  final points = (data['balance_points'] as num?)?.toInt() ?? 0;
                  final availablePoints =
                      (data['available_points'] as num?)?.toInt() ?? points;
                  final checked = data['checked_in_today'] == true;
                  return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Row(children: [
                          Expanded(
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                Text('보유 포인트',
                                    style: TextStyle(
                                        fontSize: 12,
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onSurfaceVariant)),
                                const SizedBox(height: 3),
                                Text('${formatKilometers(points)} P',
                                    style: const TextStyle(
                                        fontSize: 19,
                                        color: brandRed,
                                        fontWeight: FontWeight.w900)),
                              ])),
                          Expanded(
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                Text('사용 가능 포인트',
                                    style: TextStyle(
                                        fontSize: 12,
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onSurfaceVariant)),
                                const SizedBox(height: 3),
                                Text('${formatKilometers(availablePoints)} P',
                                    style: const TextStyle(
                                        fontSize: 19,
                                        fontWeight: FontWeight.w900)),
                              ])),
                        ]),
                        const SizedBox(height: 12),
                        SizedBox(
                            width: double.infinity,
                            child: FilledButton.icon(
                              onPressed: checked ||
                                      _checkingIn ||
                                      snapshot.connectionState ==
                                          ConnectionState.waiting
                                  ? null
                                  : _checkIn,
                              icon: Icon(checked
                                  ? Icons.check_circle_outline
                                  : Icons.event_available_outlined),
                              label: Text(_checkingIn
                                  ? '처리 중…'
                                  : !widget.signedIn && !ApiClient.demoMode
                                      ? '로그인하고 출석하기'
                                      : checked
                                          ? '오늘 출석 완료'
                                          : '출석체크'),
                            )),
                      ]);
                }),
          ])));
}

class PartnerBookingPage extends StatefulWidget {
  const PartnerBookingPage(
      {required this.api, required this.partner, super.key});
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
    final cats = (widget.partner['service_categories'] as List? ?? const [])
        .map((e) => e.toString())
        .toList();
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
      if (mounted)
        setState(() {
          loadingVehicles = false;
          error = e.toString().replaceFirst('Exception: ', '');
        });
    }
  }

  Future<void> chooseTime() async {
    final date = await showDatePicker(
        context: context,
        initialDate: selected,
        firstDate: DateTime.now(),
        lastDate: DateTime.now().add(const Duration(days: 180)));
    if (date == null || !mounted) return;
    final time = await showTimePicker(
        context: context, initialTime: TimeOfDay.fromDateTime(selected));
    if (time == null || !mounted) return;
    setState(() => selected =
        DateTime(date.year, date.month, date.day, time.hour, time.minute));
  }

  Future<void> submit() async {
    if (!formKey.currentState!.validate()) return;
    Map<String, dynamic>? selectedVehicle;
    for (final vehicle in vehicles) {
      if (vehicle['id'] == selectedVehicleId) {
        selectedVehicle = vehicle;
        break;
      }
    }
    if (selectedVehicle == null) {
      setState(() => error = '예약할 차량을 선택해 주세요.');
      return;
    }
    if ((selectedVehicle['plate_number'] ?? '').toString().trim().isEmpty) {
      setState(() => error = '선택한 차량의 번호판을 먼저 등록해 주세요.');
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final payload = <String, dynamic>{
        'partner': widget.partner['id'],
        'scheduled_at': selected.toUtc().toIso8601String(),
        'service_type': service.text.trim(),
        'contact_phone': phone.text.trim(),
        'customer_note': note.text.trim(),
      };
      payload['vehicle'] = selectedVehicleId;
      await widget.api.createPartnerBooking(payload);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted)
        setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('업체 예약 요청')),
        body: Form(
            key: formKey,
            child: ListView(padding: const EdgeInsets.all(20), children: [
              Text(
                  [
                    widget.partner['name'] ?? '협력업체',
                    if ((widget.partner['branch_label'] ?? '')
                        .toString()
                        .isNotEmpty)
                      widget.partner['branch_label'],
                  ].join(' · '),
                  style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              const InfoCard(
                  text:
                      '예약 요청을 보내면 업체 담당자가 확인 후 확정하거나 안내를 남깁니다. 예약 확정 전에는 업체와 통화해 주세요.'),
              const SizedBox(height: 16),
              if (loadingVehicles)
                const Center(child: MiniDriveLoader(compact: true)),
              if (!loadingVehicles && vehicles.isEmpty)
                const InfoCard(text: '예약 전 MY > 내 차량에서 차량과 번호판을 등록해 주세요.'),
              if (vehicles.isNotEmpty)
                DropdownButtonFormField<int>(
                  initialValue: selectedVehicleId,
                  decoration: const InputDecoration(labelText: '예약할 차량 *'),
                  items: vehicles
                      .map((row) => DropdownMenuItem<int>(
                          value: row['id'] as int,
                          child: Text(
                              '${row['model_name'] ?? '내 차량'} · ${row['plate_number'] ?? '번호판 미등록'}')))
                      .toList(),
                  onChanged: (value) =>
                      setState(() => selectedVehicleId = value),
                  validator: (value) =>
                      value == null ? '예약할 차량을 선택해 주세요.' : null,
                ),
              const SizedBox(height: 12),
              TextFormField(
                  controller: service,
                  decoration: const InputDecoration(labelText: '방문 목적'),
                  validator: (v) =>
                      v?.trim().isNotEmpty == true ? null : '방문 목적을 입력해 주세요.'),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                  onPressed: chooseTime,
                  icon: const Icon(Icons.schedule),
                  label: Text(
                      '희망 일시  ${selected.year}-${selected.month.toString().padLeft(2, '0')}-${selected.day.toString().padLeft(2, '0')}  ${selected.hour.toString().padLeft(2, '0')}:${selected.minute.toString().padLeft(2, '0')}')),
              const SizedBox(height: 12),
              TextFormField(
                  controller: phone,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                      labelText: '연락처 (선택)', hintText: '업체가 연락할 번호')),
              const SizedBox(height: 12),
              TextFormField(
                  controller: note,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: '요청사항 (선택)')),
              if (error != null)
                Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(error!,
                        style: const TextStyle(color: Colors.red))),
              const SizedBox(height: 18),
              FilledButton(
                  onPressed: busy || loadingVehicles || vehicles.isEmpty
                      ? null
                      : submit,
                  child: Text(busy ? '요청 중…' : '예약 요청 보내기')),
            ])),
      );

  @override
  void dispose() {
    service.dispose();
    phone.dispose();
    note.dispose();
    super.dispose();
  }
}

class BookingListSection extends StatefulWidget {
  const BookingListSection({required this.api, super.key});
  final ApiClient api;
  @override
  State<BookingListSection> createState() => _BookingListSectionState();
}

class _BookingListSectionState extends State<BookingListSection> {
  late Future<List<Map<String, dynamic>>> future;
  void reload() {
    future = widget.api.list('bookings');
  }

  @override
  void initState() {
    super.initState();
    reload();
  }

  Future<void> act(Future<void> Function() action) async {
    try {
      await action();
      if (mounted) {
        setState(() {
          future = widget.api.list('bookings');
        });
      }
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.toString().replaceFirst('Exception: ', ''))));
    }
  }

  @override
  Widget build(BuildContext context) =>
      FutureBuilder<List<Map<String, dynamic>>>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting)
            return const Center(child: MiniDriveLoader(compact: true));
          if (snapshot.hasError)
            return const InfoCard(text: '예약 목록을 불러오지 못했습니다.');
          final rows = (snapshot.data ?? []).where((row) {
            final status = row['status']?.toString();
            if (status == null) return false;
            return true;
          }).toList();
          if (rows.isEmpty) return const SizedBox.shrink();
          return Card(
              child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('업체 예약',
                            style: TextStyle(
                                fontSize: 17, fontWeight: FontWeight.w900)),
                        ...rows.map((row) {
                          final manager = row['can_manage'] == true;
                          final owner = row['is_customer'] == true;
                          final status = row['status']?.toString() ?? '';
                          final date = DateTime.tryParse(
                                  row['scheduled_at']?.toString() ?? '')
                              ?.toLocal();
                          final when = date == null
                              ? ''
                              : '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
                          return Column(children: [
                            ListTile(
                                contentPadding: EdgeInsets.zero,
                                title: Text(
                                    [
                                      (row['partner_name'] ?? '').toString(),
                                      if ((row['partner_branch_label'] ?? '')
                                          .toString()
                                          .isNotEmpty)
                                        (row['partner_branch_label'] ?? '')
                                            .toString(),
                                      if ((row['partner_region'] ?? '')
                                          .toString()
                                          .isNotEmpty)
                                        (row['partner_region'] ?? '')
                                            .toString(),
                                    ].join(' · '),
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w800)),
                                subtitle: Text(
                                    '$when · ${row['service_type']} · ${row['status_label']}\n${row['status'] == 'cancelled' ? '취소 사유: ${row['cancellation_reason'] ?? '이전 기록에 사유 없음'}' : (row['partner_note'] ?? row['customer_note'] ?? '').toString()}'),
                                trailing: owner &&
                                        (status == 'requested' ||
                                            status == 'confirmed')
                                    ? TextButton(
                                        onPressed: () async {
                                          final reason =
                                              await askBookingCancellationReason(
                                                  context);
                                          if (reason == null || !mounted)
                                            return;
                                          await act(() => widget.api
                                              .cancelPartnerBooking(
                                                  row['id'] as int,
                                                  reason: reason));
                                        },
                                        child: const Text('취소'))
                                    : null),
                            if (manager && status == 'requested')
                              Row(
                                  mainAxisAlignment: MainAxisAlignment.end,
                                  children: [
                                    TextButton(
                                        onPressed: () => act(() => widget.api
                                            .respondToPartnerBooking(
                                                row['id'] as int,
                                                status: 'rejected')),
                                        child: const Text('거절')),
                                    const SizedBox(width: 6),
                                    FilledButton(
                                        onPressed: () => act(() => widget.api
                                            .respondToPartnerBooking(
                                                row['id'] as int,
                                                status: 'confirmed')),
                                        child: const Text('예약 확정')),
                                  ]),
                            if (manager && status == 'confirmed')
                              Align(
                                  alignment: Alignment.centerRight,
                                  child: TextButton.icon(
                                      onPressed: () => act(() => widget.api
                                          .respondToPartnerBooking(
                                              row['id'] as int,
                                              status: 'completed')),
                                      icon: const Icon(
                                          Icons.check_circle_outline),
                                      label: const Text('작업 완료 처리'))),
                            if (manager &&
                                row['can_verify_records'] == true &&
                                status == 'confirmed' &&
                                (row['vehicle_plate_number'] ?? '')
                                    .toString()
                                    .isNotEmpty)
                              Align(
                                alignment: Alignment.centerRight,
                                child: FilledButton.tonalIcon(
                                    onPressed: () async {
                                      final saved = await Navigator.of(context)
                                          .push<bool>(MaterialPageRoute(
                                              builder: (_) => PartnerRecordPage(
                                                    api: widget.api,
                                                    initialPlateNumber:
                                                        row['vehicle_plate_number']
                                                            .toString(),
                                                    initialPartnerId:
                                                        row['partner'] as int?,
                                                  )));
                                      if (saved == true && mounted)
                                        setState(reload);
                                    },
                                    icon: const Icon(Icons.qr_code_scanner),
                                    label: const Text('번호판 확인 후 QR 정비 등록')),
                              ),
                            const Divider(),
                          ]);
                        }),
                      ])));
        },
      );
}

class PartnerRecordPage extends StatefulWidget {
  const PartnerRecordPage(
      {required this.api,
      this.initialPlateNumber,
      this.initialPartnerId,
      this.pointRedemptionId,
      this.initialVehiclePublicId,
      this.initialAmountKrw,
      this.initialPointsUsed,
      super.key});
  final ApiClient api;
  final String? initialPlateNumber;
  final int? initialPartnerId;
  final int? pointRedemptionId;
  final String? initialVehiclePublicId;
  final int? initialAmountKrw;
  final int? initialPointsUsed;
  @override
  State<PartnerRecordPage> createState() => _PartnerRecordPageState();
}

class _MaintenanceReceiptItemInput {
  final description = TextEditingController();
  final amount = TextEditingController();

  void dispose() {
    description.dispose();
    amount.dispose();
  }
}

class _PartnerRecordPageState extends State<PartnerRecordPage> {
  final formKey = GlobalKey<FormState>();
  final vehiclePublicId = TextEditingController();
  final plateNumber = TextEditingController();
  final odometer = TextEditingController();
  final List<_MaintenanceReceiptItemInput> receiptItems = [
    _MaintenanceReceiptItemInput(),
  ];
  final corrects = TextEditingController();
  final correctionReason = TextEditingController();
  final evidencePicker = ImagePicker();
  final List<XFile> evidencePhotos = [];
  late Future<List<Map<String, dynamic>>> workplaces;
  int? partnerId;
  String kind = 'service';
  bool busy = false;
  String? error;
  Map<String, dynamic>? scannedPassport;
  Map<String, dynamic>? matchedVehicle;
  int? scannedAvailablePoints;
  bool loadingScannedPoints = false;
  String? scannedPointsError;
  String? pointScanVehiclePublicId;
  String? pointScanPlateNumber;
  int? pointScanAvailablePoints;
  bool loadingPointScan = false;
  String? pointScanError;
  bool plateConfirmed = false;
  bool isCorrection = false;

  int get receiptTotalKrw => receiptItems.fold<int>(0, (total, item) {
        return total +
            (int.tryParse(item.amount.text.replaceAll(',', '').trim()) ?? 0);
      });

  void addReceiptItem() {
    if (receiptItems.length >= 20) return;
    setState(() => receiptItems.add(_MaintenanceReceiptItemInput()));
  }

  void removeReceiptItem(int index) {
    if (receiptItems.length <= 1) return;
    final removed = receiptItems.removeAt(index);
    removed.dispose();
    setState(() {});
  }

  Future<void> scanVehicleForPoints() async {
    final selectedPartnerId = partnerId;
    if (selectedPartnerId == null) return;
    final publicId = await Navigator.of(context).push<String>(
        MaterialPageRoute(builder: (_) => const ScanVehicleQrPage()));
    if (publicId == null || !mounted) return;
    setState(() {
      loadingPointScan = true;
      pointScanVehiclePublicId = publicId;
      pointScanPlateNumber = null;
      pointScanAvailablePoints = null;
      pointScanError = null;
    });
    try {
      final balance =
          await widget.api.pointBalanceForVehicle(publicId, selectedPartnerId);
      if (!mounted || selectedPartnerId != partnerId) return;
      setState(() {
        loadingPointScan = false;
        pointScanPlateNumber = balance['plate_number']?.toString();
        pointScanAvailablePoints =
            (balance['available_points'] as num?)?.toInt() ?? 0;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loadingPointScan = false;
        pointScanError = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  Future<void> loadScannedPointBalance() async {
    final publicId = vehiclePublicId.text.trim();
    final selectedPartnerId = partnerId;
    if (publicId.isEmpty || selectedPartnerId == null) return;
    setState(() {
      loadingScannedPoints = true;
      scannedAvailablePoints = null;
      scannedPointsError = null;
    });
    try {
      final balance =
          await widget.api.pointBalanceForVehicle(publicId, selectedPartnerId);
      if (!mounted || publicId != vehiclePublicId.text.trim()) return;
      setState(() {
        scannedAvailablePoints =
            (balance['available_points'] as num?)?.toInt() ?? 0;
        loadingScannedPoints = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loadingScannedPoints = false;
        scannedPointsError = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  Future<void> chooseEvidencePhoto(ImageSource source) async {
    try {
      final remaining = 5 - evidencePhotos.length;
      if (remaining <= 0) {
        setState(() => error = '사진은 최대 5장까지 첨부할 수 있습니다.');
        return;
      }
      final picked = source == ImageSource.gallery
          ? await evidencePicker.pickMultiImage(
              imageQuality: 68,
              maxWidth: 1600,
              maxHeight: 1600,
              limit: remaining,
            )
          : await evidencePicker
              .pickImage(
                source: source,
                imageQuality: 68,
                maxWidth: 1600,
                maxHeight: 1600,
              )
              .then((image) => image == null ? <XFile>[] : <XFile>[image]);
      if (picked.isNotEmpty && mounted) {
        setState(() {
          evidencePhotos.addAll(picked.take(remaining));
          error = null;
        });
      }
    } catch (_) {
      if (mounted) setState(() => error = '사진을 선택하지 못했습니다. 사진 접근 권한을 확인해 주세요.');
    }
  }

  Future<void> addEvidencePhoto() async {
    final source = await showModalBottomSheet<ImageSource>(
        context: context,
        builder: (context) => SafeArea(
              child: Wrap(children: [
                ListTile(
                    leading: const Icon(Icons.photo_library_outlined),
                    title: const Text('사진 보관함에서 여러 장 선택'),
                    onTap: () => Navigator.pop(context, ImageSource.gallery)),
                ListTile(
                    leading: const Icon(Icons.camera_alt_outlined),
                    title: const Text('카메라로 촬영'),
                    onTap: () => Navigator.pop(context, ImageSource.camera)),
              ]),
            ));
    if (source != null) await chooseEvidencePhoto(source);
  }

  Future<void> lookupPlate() async {
    if (!_isValidKoreanPlate(plateNumber.text)) {
      setState(() => error = '차량 번호 형식을 확인해 주세요. 예: 12가3456');
      return;
    }
    setState(() {
      busy = true;
      error = null;
      matchedVehicle = null;
      plateConfirmed = false;
      scannedPassport = null;
      scannedAvailablePoints = null;
      scannedPointsError = null;
      vehiclePublicId.clear();
    });
    try {
      final result =
          await widget.api.lookupVehicleByPlate(plateNumber.text.trim());
      if (!mounted) return;
      setState(() {
        matchedVehicle = Map<String, dynamic>.from(result['vehicle'] as Map);
        plateNumber.text = matchedVehicle!['plate_number'].toString();
      });
    } catch (e) {
      if (mounted)
        setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> scanVehicle() async {
    final vehicle = matchedVehicle;
    if (vehicle == null) return;
    final confirmed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
              title: const Text('실차 번호판 확인'),
              content: Text(
                  '실제 차량 번호판이 ${vehicle['plate_number']}와 같은지 확인해 주세요. 확인 후 해당 차량의 QR을 스캔합니다.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(dialogContext, false),
                    child: const Text('다시 확인')),
                FilledButton(
                    onPressed: () => Navigator.pop(dialogContext, true),
                    child: const Text('번호판 확인 · QR 스캔')),
              ],
            ));
    if (confirmed != true || !mounted) return;
    setState(() {
      plateConfirmed = true;
      error = null;
      scannedPassport = null;
      vehiclePublicId.clear();
    });
    final scanned = await Navigator.of(context).push<String>(
        MaterialPageRoute(builder: (_) => const ScanVehicleQrPage()));
    if (scanned != null && mounted) {
      setState(() {
        vehiclePublicId.text = scanned;
        scannedPassport = null;
        error = null;
      });
      try {
        final passport = await widget.api
            .scanVehiclePassport(scanned, plateNumber.text.trim());
        if (!mounted) return;
        final scannedVehicle =
            Map<String, dynamic>.from(passport['vehicle'] as Map);
        if (scannedVehicle['public_id'] != vehicle['public_id'] ||
            scannedVehicle['plate_number'] != vehicle['plate_number']) {
          setState(() {
            plateConfirmed = false;
            vehiclePublicId.clear();
            error = '번호판 조회 결과와 QR 차량이 일치하지 않습니다.';
          });
          return;
        }
        setState(() => scannedPassport = passport);
        await loadScannedPointBalance();
      } catch (e) {
        if (mounted)
          setState(() {
            plateConfirmed = false;
            vehiclePublicId.clear();
            error = e.toString().replaceFirst('Exception: ', '');
          });
      }
    }
  }

  @override
  void initState() {
    super.initState();
    workplaces = widget.api.list('partners/my-workplaces');
    partnerId = widget.initialPartnerId;
    if (widget.pointRedemptionId != null) {
      if (widget.initialVehiclePublicId != null) {
        vehiclePublicId.text = widget.initialVehiclePublicId!;
      }
      if (widget.initialAmountKrw != null) {
        receiptItems.first.amount.text =
            (widget.initialAmountKrw! + (widget.initialPointsUsed ?? 0))
                .toString();
      }
    }
    if (widget.pointRedemptionId != null &&
        widget.initialVehiclePublicId != null &&
        widget.initialPlateNumber != null) {
      plateNumber.text = widget.initialPlateNumber!;
      vehiclePublicId.text = widget.initialVehiclePublicId!;
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        try {
          final passport = await widget.api.scanVehiclePassport(
              widget.initialVehiclePublicId!, widget.initialPlateNumber!);
          if (!mounted) return;
          setState(() {
            matchedVehicle =
                Map<String, dynamic>.from(passport['vehicle'] as Map);
            plateNumber.text =
                (matchedVehicle?['plate_number'] ?? '').toString();
            scannedPassport = passport;
            plateConfirmed = true;
          });
        } catch (_) {
          // Staff can verify the plate and QR through the standard flow if needed.
        }
      });
    } else if (widget.initialPlateNumber != null) {
      plateNumber.text = widget.initialPlateNumber!;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) lookupPlate();
      });
    }
  }

  Future<void> submit() async {
    if (!formKey.currentState!.validate() ||
        partnerId == null ||
        !plateConfirmed ||
        scannedPassport == null) {
      setState(() => error = partnerId == null
          ? '인증 권한이 있는 협력업체를 선택해 주세요.'
          : '차량 번호 확인 후 일치하는 QR을 스캔해 주세요.');
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final amountEnteredKrw = receiptTotalKrw;
      final amountForServerKrw = amountEnteredKrw;
      final itemDescriptions = receiptItems
          .map((item) => item.description.text.trim())
          .where((value) => value.isNotEmpty)
          .toList();
      final descriptionSummary = itemDescriptions.join(' · ');
      await widget.api.createPartnerVerifiedRecord({
        'vehicle_public_id': vehiclePublicId.text.trim(),
        'plate_number': plateNumber.text.trim(),
        'partner': partnerId,
        'kind': kind,
        'entry_date': DateTime.now().toIso8601String().substring(0, 10),
        'odometer_km': int.parse(odometer.text),
        // Item prices are the full recorded service total.
        'amount_krw': amountForServerKrw,
        'description': descriptionSummary.length > 160
            ? descriptionSummary.substring(0, 160)
            : descriptionSummary,
        'line_items': receiptItems
            .map((item) => {
                  'description': item.description.text.trim(),
                  'amount_krw':
                      int.parse(item.amount.text.replaceAll(',', '').trim()),
                })
            .toList(),
        if (widget.pointRedemptionId != null)
          'point_redemption_id': widget.pointRedemptionId,
        if (corrects.text.trim().isNotEmpty)
          'corrects': int.parse(corrects.text.trim()),
        if (corrects.text.trim().isNotEmpty)
          'correction_reason': correctionReason.text.trim(),
      },
          evidenceImages: await Future.wait(
              evidencePhotos.map((photo) => photo.readAsBytes())),
          evidenceImageNames:
              evidencePhotos.map((photo) => photo.name).toList());
      if (!mounted) return;
      await showDialog<void>(
          context: context,
          builder: (dialogContext) => AlertDialog(
                title: const Text('업체 인증기록 등록 완료'),
                content: const Text(
                    '차량 차계부에 협력업체 인증 배지와 함께 기록되었습니다. 등록된 원본은 수정하거나 삭제할 수 없습니다.'),
                actions: [
                  FilledButton(
                      onPressed: () => Navigator.pop(dialogContext),
                      child: const Text('확인'))
                ],
              ));
      if (mounted) Navigator.pop(context, true);
    } catch (_) {
      if (mounted)
        setState(() => error = '등록하지 못했습니다. 차량 QR과 협력업체 권한, 입력 내용을 확인해 주세요.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('회원 차량 QR 스캔')),
        body: FutureBuilder<List<Map<String, dynamic>>>(
          future: workplaces,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting)
              return const Center(
                  child: MiniDriveLoader(label: '업체 정보를 불러오고 있어요'));
            if (snapshot.hasError)
              return const Center(
                  child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text('협력업체 권한을 확인하지 못했습니다.')));
            final partners = snapshot.data ?? [];
            if (partners.isEmpty)
              return const Center(
                  child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text(
                          '운영자에게 협력업체 담당자 권한을 승인받은 계정만 인증기록을 등록할 수 있습니다.',
                          textAlign: TextAlign.center)));
            partnerId ??=
                widget.initialPartnerId ?? partners.first['id'] as int;
            return Form(
                key: formKey,
                child: ListView(padding: const EdgeInsets.all(20), children: [
                  const InfoCard(
                      text:
                          '① 차량 번호를 조회해 실차 번호판을 확인합니다. ② 확인 버튼을 누르고 같은 차량에 부착된 QR을 스캔합니다. 두 차량 정보가 일치해야 인증기록을 등록할 수 있습니다.'),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<int>(
                    initialValue: partnerId,
                    decoration: const InputDecoration(labelText: '협력업체'),
                    items: partners
                        .map((row) => DropdownMenuItem<int>(
                            value: row['id'] as int,
                            child: Text(row['name'].toString())))
                        .toList(),
                    onChanged: (value) {
                      setState(() {
                        partnerId = value;
                        scannedAvailablePoints = null;
                      });
                      if (scannedPassport != null) {
                        loadScannedPointBalance();
                      }
                      pointScanVehiclePublicId = null;
                      pointScanAvailablePoints = null;
                      pointScanPlateNumber = null;
                    },
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed:
                        busy || loadingPointScan ? null : scanVehicleForPoints,
                    icon: loadingPointScan
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.qr_code_scanner),
                    label: Text(loadingPointScan
                        ? '포인트 확인 중…'
                        : '회원 차량 QR 스캔 · 포인트 확인'),
                  ),
                  if (pointScanVehiclePublicId != null) ...[
                    const SizedBox(height: 8),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Row(children: [
                              const Icon(Icons.account_balance_wallet_outlined),
                              const SizedBox(width: 10),
                              const Expanded(child: Text('사용 가능 포인트')),
                              if (loadingPointScan)
                                const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2))
                              else if (pointScanAvailablePoints != null)
                                Text(
                                    '${formatKilometers(pointScanAvailablePoints!)} P',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w900,
                                        color: brandRed))
                              else
                                Text(pointScanError ?? '확인할 수 없습니다.'),
                            ]),
                            if (pointScanPlateNumber != null) ...[
                              const SizedBox(height: 4),
                              Text('${pointScanPlateNumber!} 차량 확인'),
                            ],
                            const SizedBox(height: 8),
                            FilledButton.icon(
                              onPressed: loadingPointScan ||
                                      pointScanAvailablePoints == null ||
                                      pointScanPlateNumber == null
                                  ? null
                                  : () => Navigator.of(context).push(
                                        MaterialPageRoute(
                                          builder: (_) =>
                                              PartnerPointRedemptionPage(
                                            api: widget.api,
                                            initialVehiclePublicId:
                                                pointScanVehiclePublicId!,
                                            initialPlateNumber:
                                                pointScanPlateNumber!,
                                            initialPartnerId: partnerId!,
                                          ),
                                        ),
                                      ),
                              icon: const Icon(Icons.toll_outlined),
                              label: const Text('포인트 사용 승인 요청'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  TextFormField(
                      controller: plateNumber,
                      textCapitalization: TextCapitalization.characters,
                      decoration: const InputDecoration(
                          labelText: '차량 번호판 *', hintText: '예: 12가3456'),
                      onChanged: (_) => setState(() {
                            matchedVehicle = null;
                            plateConfirmed = false;
                            scannedPassport = null;
                            scannedAvailablePoints = null;
                            scannedPointsError = null;
                            vehiclePublicId.clear();
                            error = null;
                          }),
                      validator: (value) => _isValidKoreanPlate(value)
                          ? null
                          : '차량 번호를 확인해 주세요.'),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                      onPressed: busy ? null : lookupPlate,
                      icon: const Icon(Icons.search),
                      label: Text(busy ? '차량 확인 중…' : '차량 번호 조회')),
                  if (matchedVehicle != null) ...[
                    const SizedBox(height: 8),
                    Card(
                        child: ListTile(
                      leading: const Icon(Icons.directions_car_filled_outlined),
                      title: Text(matchedVehicle!['plate_number'].toString(),
                          style: const TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          '${matchedVehicle!['model_name'] ?? '차종 미등록'} · ${(matchedVehicle!['generation'] ?? '').toString()}'),
                    )),
                    FilledButton.icon(
                        onPressed: scanVehicle,
                        icon: const Icon(Icons.qr_code_scanner),
                        label: const Text('실차 번호판 확인 · QR 스캔')),
                  ],
                  if (scannedPassport != null) ...[
                    const SizedBox(height: 8),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 10),
                        child: Row(
                          children: [
                            const Icon(Icons.account_balance_wallet_outlined),
                            const SizedBox(width: 10),
                            const Expanded(child: Text('사용 가능 포인트')),
                            if (loadingScannedPoints)
                              const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child:
                                      CircularProgressIndicator(strokeWidth: 2))
                            else if (scannedAvailablePoints != null)
                              Text(
                                  '${formatKilometers(scannedAvailablePoints!)} P',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w900,
                                      color: brandRed))
                            else
                              Text(scannedPointsError ?? '확인할 수 없습니다.'),
                          ],
                        ),
                      ),
                    ),
                    FilledButton.icon(
                      onPressed: loadingScannedPoints ||
                              scannedAvailablePoints == null ||
                              partnerId == null
                          ? null
                          : () => Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => PartnerPointRedemptionPage(
                                    api: widget.api,
                                    initialVehiclePublicId:
                                        vehiclePublicId.text.trim(),
                                    initialPlateNumber: plateNumber.text.trim(),
                                    initialPartnerId: partnerId!,
                                  ),
                                ),
                              ),
                      icon: const Icon(Icons.toll_outlined),
                      label: const Text('포인트 사용 승인 요청'),
                    ),
                  ],
                  DropdownButtonFormField<String>(
                      initialValue: kind,
                      decoration: const InputDecoration(labelText: '작업 종류'),
                      items: const [
                        DropdownMenuItem(
                            value: 'service', child: Text('정비·소모품')),
                        DropdownMenuItem(
                            value: 'bodywork', child: Text('판금·도색·보험처리')),
                        DropdownMenuItem(
                            value: 'wheel_tire', child: Text('휠·타이어')),
                        DropdownMenuItem(
                            value: 'electrical', child: Text('전장류')),
                        DropdownMenuItem(value: 'other', child: Text('기타')),
                      ],
                      onChanged: (value) =>
                          setState(() => kind = value ?? 'service')),
                  Row(children: [
                    const Expanded(
                        child: Text('정비 내역',
                            style: TextStyle(fontWeight: FontWeight.w800))),
                    TextButton.icon(
                      onPressed: busy || receiptItems.length >= 20
                          ? null
                          : addReceiptItem,
                      icon: const Icon(Icons.add),
                      label: const Text('항목 추가'),
                    ),
                  ]),
                  ...receiptItems.asMap().entries.map((entry) {
                    final index = entry.key;
                    final item = entry.value;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              flex: 3,
                              child: TextFormField(
                                controller: item.description,
                                decoration: InputDecoration(
                                  labelText:
                                      '작업 내용${receiptItems.length > 1 ? ' ${index + 1}' : ''} *',
                                  hintText: '예: 엔진오일 교환',
                                ),
                                validator: (value) =>
                                    value == null || value.trim().isEmpty
                                        ? '작업 내용을 입력해 주세요.'
                                        : null,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              flex: 2,
                              child: TextFormField(
                                controller: item.amount,
                                keyboardType: TextInputType.number,
                                decoration: const InputDecoration(
                                    labelText: '가격 (원) *'),
                                onChanged: (_) => setState(() {}),
                                validator: (value) {
                                  final parsed = int.tryParse(
                                      (value ?? '').replaceAll(',', '').trim());
                                  return parsed == null || parsed < 0
                                      ? '금액을 입력해 주세요.'
                                      : null;
                                },
                              ),
                            ),
                            if (receiptItems.length > 1)
                              IconButton(
                                tooltip: '항목 삭제',
                                onPressed: busy
                                    ? null
                                    : () => removeReceiptItem(index),
                                icon: const Icon(Icons.remove_circle_outline),
                              ),
                          ]),
                    );
                  }),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            _ReceiptDetailRow(
                                label: '정비 합계',
                                value: '₩${formatKilometers(receiptTotalKrw)}'),
                            if (widget.pointRedemptionId != null) ...[
                              _ReceiptDetailRow(
                                  label: '사용 포인트',
                                  value:
                                      '−${formatKilometers(widget.initialPointsUsed ?? 0)} P'),
                              _ReceiptDetailRow(
                                label: '실결제 금액',
                                value:
                                    '₩${formatKilometers((receiptTotalKrw - (widget.initialPointsUsed ?? 0)).clamp(0, receiptTotalKrw))}',
                                emphasized: true,
                              ),
                            ],
                          ]),
                    ),
                  ),
                  TextFormField(
                      controller: odometer,
                      keyboardType: TextInputType.number,
                      decoration:
                          const InputDecoration(labelText: '작업 당시 주행거리 km *'),
                      validator: (value) => int.tryParse(value ?? '') == null
                          ? '주행거리를 숫자로 입력해 주세요.'
                          : null),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('기존 정비기록 정정'),
                    subtitle: const Text('기존 기록을 수정 등록할 때만 선택하세요.'),
                    value: isCorrection,
                    onChanged: busy
                        ? null
                        : (value) => setState(() {
                              isCorrection = value;
                              if (!value) {
                                corrects.clear();
                                correctionReason.clear();
                              }
                            }),
                  ),
                  if (isCorrection) ...[
                    TextFormField(
                        controller: corrects,
                        keyboardType: TextInputType.number,
                        decoration:
                            const InputDecoration(labelText: '정정 대상 기록 번호 *'),
                        validator: (value) => !isCorrection ||
                                (value != null &&
                                    int.tryParse(value.trim()) != null)
                            ? null
                            : '정정 대상 기록 번호를 숫자로 입력해 주세요.'),
                    TextFormField(
                        controller: correctionReason,
                        decoration: const InputDecoration(labelText: '정정 사유 *'),
                        validator: (value) =>
                            !isCorrection || (value?.trim().isNotEmpty ?? false)
                                ? null
                                : '정정 사유를 입력해 주세요.'),
                  ],
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Row(children: [
                              const Expanded(
                                  child: Text('영수증·작업사진',
                                      style: TextStyle(
                                          fontWeight: FontWeight.w800))),
                              TextButton.icon(
                                  onPressed: busy || evidencePhotos.length >= 5
                                      ? null
                                      : addEvidencePhoto,
                                  icon: const Icon(Icons.add_a_photo_outlined),
                                  label: Text(
                                      '사진 추가 (${evidencePhotos.length}/5)')),
                            ]),
                            if (evidencePhotos.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children:
                                    evidencePhotos.asMap().entries.map((entry) {
                                  final index = entry.key;
                                  final photo = entry.value;
                                  return SizedBox(
                                    width: 96,
                                    height: 96,
                                    child: Stack(
                                      fit: StackFit.expand,
                                      children: [
                                        FutureBuilder<Uint8List>(
                                          future: photo.readAsBytes(),
                                          builder: (context, snapshot) =>
                                              snapshot.hasData
                                                  ? ClipRRect(
                                                      borderRadius: BorderRadius
                                                          .circular(10),
                                                      child: Image.memory(
                                                          snapshot.data!,
                                                          fit: BoxFit.cover))
                                                  : const Center(
                                                      child: MiniDriveLoader(
                                                          compact: true)),
                                        ),
                                        Positioned(
                                          right: 2,
                                          top: 2,
                                          child: IconButton.filledTonal(
                                            visualDensity:
                                                VisualDensity.compact,
                                            onPressed: busy
                                                ? null
                                                : () => setState(() =>
                                                    evidencePhotos
                                                        .removeAt(index)),
                                            icon: const Icon(Icons.close,
                                                size: 16),
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                }).toList(),
                              ),
                              const SizedBox(height: 6),
                              Text('사진은 긴 변 1,600px·품질 68%로 압축해 저장합니다.',
                                  style: TextStyle(
                                      color: Theme.of(context)
                                          .colorScheme
                                          .onSurfaceVariant,
                                      fontSize: 12)),
                            ] else
                              Text(
                                  '영수증·작업사진을 최대 5장까지 첨부할 수 있습니다. 선택한 사진은 업로드 전에 자동 압축됩니다.',
                                  style: TextStyle(
                                      color: Theme.of(context)
                                          .colorScheme
                                          .onSurfaceVariant,
                                      fontSize: 12)),
                          ]),
                    ),
                  ),
                  if (error != null)
                    Padding(
                        padding: const EdgeInsets.only(top: 10),
                        child: Text(error!,
                            style: const TextStyle(color: Colors.red))),
                  const SizedBox(height: 18),
                  FilledButton.icon(
                      onPressed: busy ? null : submit,
                      icon: const Icon(Icons.verified),
                      label: Text(busy ? '등록 중…' : '업체 인증기록 등록')),
                ]));
          },
        ),
      );

  @override
  void dispose() {
    vehiclePublicId.dispose();
    plateNumber.dispose();
    odometer.dispose();
    for (final item in receiptItems) {
      item.dispose();
    }
    corrects.dispose();
    correctionReason.dispose();
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
              if (uri != null &&
                  uri.scheme == 'ilovemini' &&
                  uri.host == 'vehicle' &&
                  uri.pathSegments.length == 1) {
                handled = true;
                Navigator.of(context).pop(uri.pathSegments.single);
                return;
              }
            }
          }),
          const Positioned(
              left: 24,
              right: 24,
              bottom: 32,
              child: Card(
                  child: Padding(
                      padding: EdgeInsets.all(14),
                      child: Text('아이러브미니 Vehicle Passport QR을 화면 안에 맞춰 주세요.',
                          textAlign: TextAlign.center)))),
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
  final reviewUsernameController = TextEditingController();
  final reviewPasswordController = TextEditingController();
  StreamSubscription<Uri>? subscription;
  bool busy = false;
  bool termsAccepted = false, privacyAccepted = false;
  bool get canUseSignIn => termsAccepted && privacyAccepted;
  String? error;
  @override
  void initState() {
    super.initState();
    subscription = appLinks.uriLinkStream.listen(_handleLink);
    appLinks.getInitialLink().then((uri) {
      if (uri != null) _handleLink(uri);
    });
  }

  Future<void> _handleLink(Uri uri) async {
    final ticket = uri.queryParameters['ticket'];
    if (uri.scheme != 'ilovemini' ||
        uri.host != 'auth' ||
        ticket == null ||
        !mounted) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.completeNaverLogin(ticket,
          termsAccepted: termsAccepted, privacyAccepted: privacyAccepted);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = '로그인 확인에 실패했습니다. 다시 시도해 주세요.');
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> _startLogin() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final uri = await widget.api.startNaverLogin();
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication))
        throw Exception('로그인 화면을 열지 못했습니다.');
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> _startAppleLogin() async {
    if (!termsAccepted || !privacyAccepted) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final nonce = generateNonce();
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [AppleIDAuthorizationScopes.email],
        nonce: nonce,
      );
      final identityToken = credential.identityToken;
      if (identityToken == null || identityToken.isEmpty) {
        throw Exception('Apple 인증 정보를 받지 못했습니다. 다시 시도해 주세요.');
      }
      await widget.api.loginWithApple(identityToken, nonce,
          termsAccepted: termsAccepted, privacyAccepted: privacyAccepted);
      if (mounted) Navigator.pop(context, true);
    } on SignInWithAppleAuthorizationException catch (e) {
      if (mounted && e.code != AuthorizationErrorCode.canceled) {
        setState(() => error = 'Apple 로그인을 완료하지 못했습니다. 다시 시도해 주세요.');
      }
    } catch (e) {
      if (mounted) {
        setState(() => error = e.toString().replaceFirst('Exception: ', ''));
      }
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> _openLegalPage(String path) async {
    final uri = Uri.https('ilovemini.onrender.com', path);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication) &&
        mounted) {
      setState(() => error = '문서를 열지 못했습니다. 잠시 후 다시 시도해 주세요.');
    }
  }

  Future<void> _startReviewLogin() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.loginForAppReview(
          reviewUsernameController.text, reviewPasswordController.text);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted)
        setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    }
    if (mounted) setState(() => busy = false);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('아이러브미니 시작하기')),
        body: ListView(padding: const EdgeInsets.all(24), children: [
          const SizedBox(height: 18),
          const Center(child: BrandLogo(height: 205)),
          const SizedBox(height: 24),
          const Text('네이버 또는 Apple로\n간편하게 시작하세요',
              style: TextStyle(
                  fontSize: 27, fontWeight: FontWeight.w900, height: 1.25)),
          const SizedBox(height: 12),
          Text(
              '첫 로그인 시 아이러브미니 회원 계정이 자동으로 만들어집니다. 네이버와 Apple 비밀번호는 아이러브미니에 전달되지 않습니다.',
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  height: 1.5)),
          const SizedBox(height: 28),
          CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: termsAccepted,
              onChanged: (value) =>
                  setState(() => termsAccepted = value ?? false),
              title: const Text('(필수) 이용약관 동의')),
          CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: privacyAccepted,
              onChanged: (value) =>
                  setState(() => privacyAccepted = value ?? false),
              title: const Text('(필수) 개인정보 처리방침 동의')),
          Wrap(spacing: 4, children: [
            TextButton(
                onPressed: () => _openLegalPage('/terms/'),
                child: const Text('이용약관 보기')),
            TextButton(
                onPressed: () => _openLegalPage('/privacy/'),
                child: const Text('개인정보 처리방침 보기')),
          ]),
          SizedBox(
              height: 54,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF03A94D),
                    foregroundColor: Colors.white),
                onPressed: (busy || !termsAccepted || !privacyAccepted)
                    ? null
                    : _startLogin,
                icon: const Text('N',
                    style:
                        TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
                label: Text(busy ? '네이버 로그인 진행 중…' : '네이버 아이디로 시작하기',
                    style: const TextStyle(fontWeight: FontWeight.w800)),
              )),
          if (Platform.isIOS) ...[
            const SizedBox(height: 10),
            SizedBox(
              height: 54,
              child: SignInWithAppleButton(
                text: 'Apple로 계속하기',
                // Keep Apple's standard button styles, while making the
                // consent-gated disabled state visibly different.
                style: canUseSignIn
                    ? SignInWithAppleButtonStyle.black
                    : SignInWithAppleButtonStyle.whiteOutlined,
                borderRadius: BorderRadius.circular(12),
                onPressed: (busy || !canUseSignIn) ? null : _startAppleLogin,
              ),
            ),
            if (!canUseSignIn)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  '이용약관과 개인정보 처리방침에 모두 동의하면 Apple 버튼이 검정색으로 활성화됩니다.',
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
          ],
          if (error != null)
            Padding(
                padding: const EdgeInsets.only(top: 14),
                child: Text(error!, style: const TextStyle(color: Colors.red))),
          const SizedBox(height: 16),
          Text(
              '회원가입과 로그인을 진행하려면 이용약관과 개인정보 처리방침에 동의해 주세요. Apple 로그인은 이메일 비공개를 선택할 수 있습니다.',
              style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).colorScheme.onSurfaceVariant)),
          const SizedBox(height: 30),
          const Divider(),
          const SizedBox(height: 12),
          Text('심사용 데모 로그인',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text('앱 심사를 위한 계정입니다. 실제 회원 정보와 분리된 샘플 차량만 표시됩니다.',
              style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  height: 1.4)),
          const SizedBox(height: 12),
          TextField(
            controller: reviewUsernameController,
            enabled: !busy,
            onChanged: (_) => setState(() {}),
            autocorrect: false,
            decoration: const InputDecoration(
                labelText: '심사용 아이디', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: reviewPasswordController,
            enabled: !busy,
            onChanged: (_) => setState(() {}),
            obscureText: true,
            decoration: const InputDecoration(
                labelText: '심사용 비밀번호', border: OutlineInputBorder()),
            onSubmitted: (_) => busy ||
                    reviewUsernameController.text.trim().isEmpty ||
                    reviewPasswordController.text.isEmpty
                ? null
                : _startReviewLogin(),
          ),
          const SizedBox(height: 12),
          SizedBox(
              height: 50,
              child: OutlinedButton(
                onPressed: busy ||
                        reviewUsernameController.text.trim().isEmpty ||
                        reviewPasswordController.text.isEmpty
                    ? null
                    : _startReviewLogin,
                child: Text(busy ? '로그인 중…' : '심사용 데모 계정으로 로그인'),
              )),
          const SizedBox(height: 24),
        ]),
      );
  @override
  void dispose() {
    subscription?.cancel();
    reviewUsernameController.dispose();
    reviewPasswordController.dispose();
    super.dispose();
  }
}

class BrandLogo extends StatelessWidget {
  const BrandLogo({required this.height, super.key});
  final double height;
  @override
  Widget build(BuildContext context) {
    final width = height * (1346 / 1603);
    return Image.asset('assets/images/ilovemini_logo.png',
        width: width, height: height, fit: BoxFit.contain);
  }
}

class SectionHeading extends StatelessWidget {
  const SectionHeading(
      {required this.title, required this.subtitle, super.key});
  final String title, subtitle;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(title,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
        Text(subtitle,
            style: TextStyle(
                fontSize: 12,
                color: Theme.of(context).colorScheme.onSurfaceVariant)),
      ]));
}

class InfoCard extends StatelessWidget {
  const InfoCard({required this.text, super.key});
  final String text;
  @override
  Widget build(BuildContext context) => Card(
      child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(children: [
            Icon(Icons.info_outline,
                color: Theme.of(context).colorScheme.onSurfaceVariant),
            const SizedBox(width: 12),
            Expanded(
                child: Text(text,
                    style: TextStyle(
                        color:
                            Theme.of(context).colorScheme.onSurfaceVariant))),
          ])));
}
