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

  test('loads every partner page', () async {
    var calls = 0;
    final api = ApiClient(client: MockClient((request) async {
      calls++;
      return http.Response(jsonEncode({
        'results': [{'id': calls}],
        'next': calls == 1 ? 'http://10.0.2.2:8000/api/partners/?page=2' : null,
      }), 200);
    }));
    expect((await api.list('partners')).map((row) => row['id']), [1, 2]);
    expect(calls, 2);
  });

  test('rejects foreign pagination before making a request', () async {
    var calls = 0;
    final api = ApiClient(client: MockClient((request) async {
      calls++;
      return http.Response('{"results":[],"next":"https://foreign.example/api/partners/"}', 200);
    }));
    await expectLater(api.list('partners'), throwsException);
    expect(calls, 1);
  });

  test('concurrent expired requests share one refresh and retry', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'old', 'refresh_token': 'refresh'});
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
    final results = await Future.wait([api.list('vehicles'), api.list('ledger')]);
    expect(results.every((rows) => rows.length == 1), isTrue);
    expect(refreshes, 1);
  });

  test('rejected refresh clears session and signals login', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'old', 'refresh_token': 'bad'});
    final before = ApiClient.sessionExpired.value;
    final api = ApiClient(client: MockClient((request) async => http.Response('{}', 401)));
    await expectLater(api.list('vehicles'), throwsException);
    expect(await api.isSignedIn, isFalse);
    expect(ApiClient.sessionExpired.value, before + 1);
  });

  test('temporary refresh failure preserves credentials', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'old', 'refresh_token': 'refresh'});
    final api = ApiClient(client: MockClient((request) async =>
      http.Response('{}', request.url.path.endsWith('/token/refresh/') ? 503 : 401)));
    await expectLater(api.list('vehicles'), throwsException);
    expect(await api.isSignedIn, isTrue);
  });

  testWidgets('23 partners scroll to the last vendor and search works', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final rows = List.generate(23, (i) => {'id': i, 'name': '업체 $i', 'region': '경기', 'service_categories': ['정비']});
    final api = ApiClient(client: MockClient((_) async => http.Response(jsonEncode(rows), 200, headers: {'content-type': 'application/json; charset=utf-8'})));
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: CatalogPage(api: api, path: 'partners', title: '업체'))));
    await tester.pumpAndSettle();
    expect(find.text('등록된 협력업체 23곳 · 표시 23곳'), findsOneWidget);
    await tester.drag(find.byType(ListView), const Offset(0, -4000));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('업체 22'));
    await tester.tap(find.text('업체 22'));
    await tester.pumpAndSettle();
    expect(find.byType(PartnerDetailPage), findsOneWidget);
    Navigator.of(tester.element(find.byType(PartnerDetailPage))).pop();
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byType(TextField));
    await tester.enterText(find.byType(TextField), '업체 22');
    await tester.pumpAndSettle();
    expect(find.text('등록된 협력업체 23곳 · 표시 1곳'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('notice opens the complete body', (tester) async {
    final api = ApiClient(client: MockClient((_) async => http.Response(jsonEncode([
      {'id': 1, 'title': '공지 제목', 'summary': '요약', 'body': '공지 전체 본문'}
    ]), 200, headers: {'content-type': 'application/json; charset=utf-8'})));
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: CatalogPage(api: api, path: 'notices', title: '공지'))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('공지 제목'));
    await tester.pumpAndSettle();
    expect(find.text('공지 전체 본문'), findsOneWidget);
  });
}
