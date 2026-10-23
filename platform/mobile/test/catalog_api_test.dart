import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';
import 'package:ilovemini/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('loads active shopping products with their three-tab categories',
      () async {
    final api = ApiClient(client: MockClient((request) async {
      expect(request.url.path, '/api/app/content/');
      return http.Response.bytes(
          utf8.encode(jsonEncode({
            'banners': [],
            'products': [
              {'id': 1, 'title': '추천 상품', 'category': 'recommended'},
              {'id': 2, 'title': '공동구매 상품', 'category': 'groupbuy'},
              {'id': 3, 'title': '제휴 혜택', 'category': 'benefits'},
            ],
            'releases': [],
          })),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'});
    }));

    final content = await api.appContent();
    final products = content['products'] as List;
    expect(products.map((item) => item['category']),
        ['recommended', 'groupbuy', 'benefits']);
  });

  testWidgets('cafe tab shows shopping recommendations and groupbuys',
      (tester) async {
    expect(malautoRecommendedProducts, hasLength(4));
    expect(malautoGroupbuyProducts, hasLength(2));
    expect(
        [...malautoRecommendedProducts, ...malautoGroupbuyProducts].every(
            (item) =>
                '${item['action_url']}'.startsWith('https://horsecar.co.kr/')),
        isTrue);
    final api = ApiClient(client: MockClient((request) async {
      if (request.url.path.endsWith('/api/notices/')) {
        return http.Response('[]', 200,
            headers: {'content-type': 'application/json'});
      }
      return http.Response(
          jsonEncode({
            'banners': [],
            'products': [
              {
                'id': 11,
                'title': '핸드폰 거치대 집게 미니쿠퍼 악세사리',
                'description': '호환 안내',
                'category': 'recommended',
                'asset_key': 'phone-holder',
                'action_url': 'https://horsecar.co.kr/item/11'
              },
              {
                'id': 12,
                'title': 'MINI 컵홀더 공동구매',
                'description': '공동구매 상품',
                'category': 'groupbuy',
                'asset_key': 'grille-parts',
                'action_url': 'https://horsecar.co.kr/item/12'
              },
            ],
            'releases': []
          }),
          200,
          headers: {'content-type': 'application/json'});
    }));
    await tester
        .pumpWidget(MaterialApp(home: Scaffold(body: CafePage(api: api))));
    await tester.pumpAndSettle();

    expect(find.text('MINI 쇼핑'), findsNothing);
    expect(find.text('추천아이템'), findsOneWidget);
    expect(find.text('아이러브미니 네이버 카페'), findsOneWidget);
    expect(find.text('검색어 입력'), findsNothing);
    expect(find.text('AI 검색'), findsNothing);
    expect(find.text('카페 검색'), findsNothing);
    expect(find.textContaining('핸드폰 거치대'), findsOneWidget);
    expect(find.text('말자동차에서 보기'), findsNothing);
    expect(find.text('업데이트 예정'), findsOneWidget);
    expect(find.textContaining('최대 거치 사이즈'), findsNothing);
    expect(find.byType(GridView), findsNothing);
    expect(find.byType(ListView), findsOneWidget);

    await tester.tap(find.text('공동구매'));
    await tester.pumpAndSettle();
    expect(find.textContaining('컵홀더'), findsOneWidget);
    expect(find.textContaining('아이스티 머그'), findsNothing);
    expect(find.text('말자동차에서 보기'), findsNothing);
    expect(find.text('업데이트 예정'), findsOneWidget);

    expect(find.text('제휴혜택'), findsNothing);
  });

  testWidgets('cafe nickname editor is grouped inside the membership card',
      (tester) async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'test-token'});
    final api = ApiClient(client: MockClient((request) async {
      if (request.url.path.endsWith('/api/me/overview/')) {
        return http.Response(jsonEncode({'cafe_nickname': 'MINI오너'}), 200,
            headers: {'content-type': 'application/json'});
      }
      if (request.url.path.endsWith('/api/me/grade/')) {
        return http.Response(
            jsonEncode({'grade': 'mini', 'grade_label': '미니회원'}), 200,
            headers: {'content-type': 'application/json'});
      }
      if (request.url.path.endsWith('/api/attendance/')) {
        return http.Response(
            jsonEncode({
              'balance_points': 0,
              'available_points': 0,
              'checked_in_today': true,
            }),
            200,
            headers: {'content-type': 'application/json'});
      }
      fail('Unexpected request: ${request.url}');
    }));

    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: MembershipSummaryCard(
      api: api,
      signedIn: true,
      onLogin: () {},
      nicknameSection: CafeNicknameSection(api: api),
    ))));
    await tester.pumpAndSettle();

    expect(find.text('MINI오너'), findsOneWidget);
    expect(find.ancestor(of: find.text('카페 닉네임'), matching: find.byType(Card)),
        findsOneWidget);
  });

  test('resolves relative product image URLs against the secure API host', () {
    final api =
        ApiClient(client: MockClient((_) async => http.Response('', 200)));
    expect(api.resolvePublicImageUrl('/media/item.png'),
        'https://ilovemini.onrender.com/media/item.png');
    expect(
        api.resolvePublicImageUrl(
            'http://ilovemini.onrender.com/media/item.png'),
        'https://ilovemini.onrender.com/media/item.png');
    expect(
        api.resolvePublicImageUrl('http://insecure.example/item.png'), isNull);
  });

  testWidgets('MY hides completed and elapsed partner bookings',
      (tester) async {
    final api = ApiClient(client: MockClient((request) async {
      expect(request.url.path, '/api/bookings/');
      return http.Response(
          jsonEncode([
            {
              'id': 1,
              'partner_name': '예정 업체',
              'service_type': '엔진오일 교환',
              'status': 'confirmed',
              'status_label': '예약 확정',
              'scheduled_at': '2099-01-01T10:00:00Z',
            },
            {
              'id': 2,
              'partner_name': '완료 업체',
              'service_type': '수리 완료',
              'status': 'completed',
              'status_label': '완료',
              'scheduled_at': '2099-01-01T10:00:00Z',
            },
            {
              'id': 3,
              'partner_name': '지난 업체',
              'service_type': '지난 정비',
              'status': 'confirmed',
              'status_label': '예약 확정',
              'scheduled_at': '2020-01-01T10:00:00Z',
            },
          ]),
          200,
          headers: {'content-type': 'application/json'});
    }));

    await tester.pumpWidget(
        MaterialApp(home: Scaffold(body: BookingListSection(api: api))));
    await tester.pumpAndSettle();

    expect(find.textContaining('예정 업체'), findsOneWidget);
    expect(find.textContaining('완료 업체'), findsNothing);
    expect(find.textContaining('지난 업체'), findsNothing);
  });

  testWidgets('attendance button becomes disabled after successful check-in',
      (tester) async {
    var postCount = 0;
    final api = ApiClient(client: MockClient((request) async {
      final checkingIn = request.method == 'POST';
      final payload = {
        'balance_points': checkingIn || postCount > 0 ? 1000 : 0,
        'streak_days': 1,
        'checked_in_today': checkingIn || postCount > 0,
        'checkins': [],
        'earned_points': checkingIn && postCount == 0 ? 1000 : 0,
        'message': checkingIn && postCount == 0
            ? '출석 완료! 1,000P를 적립했어요.'
            : '오늘은 이미 출석했어요.',
      };
      if (request.method == 'POST') postCount++;
      return http.Response(
          jsonEncode(payload), request.method == 'POST' ? 201 : 200,
          headers: {'content-type': 'application/json'});
    }));

    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: AttendanceCheckinCard(
                api: api, signedIn: true, onLogin: () {}))));
    await tester.pumpAndSettle();

    final button = find.byType(FilledButton);
    expect(tester.widget<FilledButton>(button).onPressed, isNotNull);
    await tester.tap(button);
    await tester.pump();
    await tester.pumpAndSettle();

    expect(postCount, 1);
    expect(find.text('오늘 출석 완료'), findsOneWidget);
    expect(tester.widget<FilledButton>(button).onPressed, isNull);
    await tester.tap(button);
    await tester.pump();
    expect(postCount, 1);
  });

  test('public partners do not send an expired login token', () async {
    FlutterSecureStorage.setMockInitialValues(
        {'access_token': 'expired', 'refresh_token': 'expired'});
    final api = ApiClient(client: MockClient((request) async {
      expect(request.headers.containsKey('Authorization'), isFalse);
      return http.Response('[{"id":1}]', 200);
    }));
    expect((await api.list('partners')).length, 1);
    expect(await api.isSignedIn, isTrue);
  });

  test('request timeout is bounded and preserves credentials', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'old'});
    final api = ApiClient(
        requestTimeout: const Duration(milliseconds: 1),
        client: MockClient((request) async {
          await Future<void>.delayed(const Duration(milliseconds: 10));
          return http.Response('[]', 200);
        }));
    await expectLater(api.list('partners'), throwsA(isA<TimeoutException>()));
    expect(await api.isSignedIn, isTrue);
  });

  test('loads every partner page', () async {
    var calls = 0;
    final api = ApiClient(client: MockClient((request) async {
      calls++;
      return http.Response(
          jsonEncode({
            'results': [
              {'id': calls}
            ],
            'next': calls == 1
                ? request.url.replace(queryParameters: {'page': '2'}).toString()
                : null,
          }),
          200);
    }));
    expect((await api.list('partners')).map((row) => row['id']), [1, 2]);
    expect(calls, 2);
  });

  test('rejects foreign pagination before making a request', () async {
    var calls = 0;
    final api = ApiClient(client: MockClient((request) async {
      calls++;
      return http.Response(
          '{"results":[],"next":"https://foreign.example/api/partners/"}', 200);
    }));
    await expectLater(api.list('partners'), throwsException);
    expect(calls, 1);
  });

  test('concurrent expired requests share one refresh and retry', () async {
    FlutterSecureStorage.setMockInitialValues(
        {'access_token': 'old', 'refresh_token': 'refresh'});
    var refreshes = 0;
    final barrier = Completer<void>();
    var oldRequests = 0;
    final api = ApiClient(client: MockClient((request) async {
      if (request.url.path.endsWith('/token/refresh/')) {
        refreshes++;
        await Future<void>.delayed(const Duration(milliseconds: 10));
        return http.Response('{"access":"new"}', 200);
      }
      if (request.headers['Authorization'] == 'Bearer old') {
        oldRequests++;
        if (oldRequests == 2) barrier.complete();
        await barrier.future;
        return http.Response('{}', 401);
      }
      expect(request.headers['Authorization'], 'Bearer new');
      return http.Response('[{"id":1}]', 200);
    }));
    final results =
        await Future.wait([api.list('vehicles'), api.list('ledger')]);
    expect(results.every((rows) => rows.length == 1), isTrue);
    expect(refreshes, 1);
  });

  test('rejected refresh clears session and signals login', () async {
    FlutterSecureStorage.setMockInitialValues(
        {'access_token': 'old', 'refresh_token': 'bad'});
    final before = ApiClient.sessionExpired.value;
    final api = ApiClient(
        client: MockClient((request) async => http.Response('{}', 401)));
    await expectLater(api.list('vehicles'), throwsException);
    expect(await api.isSignedIn, isFalse);
    expect(ApiClient.sessionExpired.value, before + 1);
  });

  test('temporary refresh failure preserves credentials', () async {
    FlutterSecureStorage.setMockInitialValues(
        {'access_token': 'old', 'refresh_token': 'refresh'});
    final api = ApiClient(
        client: MockClient((request) async => http.Response(
            '{}', request.url.path.endsWith('/token/refresh/') ? 503 : 401)));
    await expectLater(api.list('vehicles'), throwsException);
    expect(await api.isSignedIn, isTrue);
  });

  testWidgets('23 partners scroll to the last vendor and search works',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final rows = List.generate(
        23,
        (i) => {
              'id': i,
              'name': '업체 $i',
              'region': '경기',
              'service_categories': ['정비']
            });
    final api = ApiClient(
        client: MockClient((_) async => http.Response(jsonEncode(rows), 200,
            headers: {'content-type': 'application/json; charset=utf-8'})));
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: CatalogPage(api: api, path: 'partners', title: '업체'))));
    await tester.pumpAndSettle();
    expect(find.text('23곳'), findsWidgets);
    await tester.scrollUntilVisible(find.text('정비 전문').first, 200,
        scrollable: find.byType(Scrollable).first);
    await tester.pumpAndSettle();
    await Scrollable.ensureVisible(tester.element(find.text('정비 전문').first),
        alignment: 0.5, duration: Duration.zero);
    await tester.pumpAndSettle();
    expect(find.text('정비 전문').first.hitTestable(), findsOneWidget);
    await tester.tap(find.text('정비 전문').first);
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('업체 22'), 300,
        scrollable: find.byType(Scrollable).first);
    await tester.pumpAndSettle();
    await Scrollable.ensureVisible(tester.element(find.text('업체 22')),
        alignment: 0.5, duration: Duration.zero);
    await tester.pumpAndSettle();
    expect(find.text('업체 22').hitTestable(), findsOneWidget);
    await tester.tap(find.text('업체 22'));
    await tester.pumpAndSettle();
    expect(find.byType(PartnerDetailPage), findsOneWidget);
    Navigator.of(tester.element(find.byType(PartnerDetailPage))).pop();
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byType(TextField));
    await tester.enterText(find.byType(TextField), '업체 22');
    await tester.pumpAndSettle();
    expect(find.text('1곳'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('notice opens the complete body', (tester) async {
    final api = ApiClient(
        client: MockClient((_) async => http.Response(
            jsonEncode([
              {'id': 1, 'title': '공지 제목', 'summary': '요약', 'body': '공지 전체 본문'}
            ]),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'})));
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: CatalogPage(api: api, path: 'notices', title: '공지'))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('공지 제목'));
    await tester.pumpAndSettle();
    expect(find.text('공지 전체 본문'), findsOneWidget);
  });
}
