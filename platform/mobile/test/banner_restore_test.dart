import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';
import 'package:ilovemini/admin_managed_widgets.dart';

void main() {
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));
  testWidgets('admin banners retain looping, paging and pause controls',
      (tester) async {
    tester.view.physicalSize = const Size(400, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final api = ApiClient(
        client: MockClient((request) async => http.Response(
            jsonEncode({
              'banners': [
                {'title': 'A'},
                {'title': 'B'},
                {'title': 'C'},
              ]
            }),
            200)));
    await tester.pumpWidget(
        MaterialApp(home: Scaffold(body: ManagedBanners(api: api))));
    await tester.pumpAndSettle();
    expect(find.text('1 / 3'), findsOneWidget);
    await tester.pump(const Duration(seconds: 5));
    await tester.pumpAndSettle();
    expect(find.text('2 / 3'), findsOneWidget);
    await tester.tap(find.byTooltip('자동 넘김 일시정지'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 10));
    expect(find.text('2 / 3'), findsOneWidget);
    await tester.tap(find.byTooltip('다음 배너'));
    await tester.pumpAndSettle();
    expect(find.text('3 / 3'), findsOneWidget);
    await tester.tap(find.byTooltip('다음 배너'));
    await tester.pumpAndSettle();
    expect(find.text('1 / 3'), findsOneWidget);
    await tester.tap(find.byTooltip('이전 배너'));
    await tester.pumpAndSettle();
    expect(find.text('3 / 3'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
}
