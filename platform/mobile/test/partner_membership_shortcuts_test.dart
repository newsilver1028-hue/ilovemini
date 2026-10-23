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

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'test-token'});
  });

  Future<void> pumpMembershipCard(WidgetTester tester, String grade) async {
    final api = ApiClient(
      client: MockClient((request) async {
        const headers = {'content-type': 'application/json; charset=utf-8'};
        if (request.url.path.endsWith('/me/grade/')) {
          return http.Response(
              jsonEncode({'grade': grade, 'grade_label': '협력업체'}), 200,
              headers: headers);
        }
        if (request.url.path.endsWith('/attendance/')) {
          return http.Response(jsonEncode({'balance_points': 0}), 200,
              headers: headers);
        }
        if (request.url.path.endsWith('/partners/my-workplaces/')) {
          return http.Response(
              jsonEncode([
                {'id': 1, 'name': '테스트 업체'}
              ]),
              200,
              headers: headers);
        }
        return http.Response('[]', 200, headers: headers);
      }),
    );

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: MembershipSummaryCard(
            api: api,
            signedIn: true,
            onLogin: () {},
          ),
        ),
      ),
    ));
    await tester.pumpAndSettle();
  }

  testWidgets('partner membership shows booking and vehicle scan shortcuts',
      (tester) async {
    await pumpMembershipCard(tester, 'partner');

    expect(find.text('예약 현황판'), findsOneWidget);
    expect(find.text('회원 차량 QR 스캔'), findsOneWidget);
  });

  testWidgets('general membership does not show partner shortcuts',
      (tester) async {
    await pumpMembershipCard(tester, 'general');

    expect(find.text('예약 현황판'), findsNothing);
    expect(find.text('회원 차량 QR 스캔'), findsNothing);
    expect(find.byTooltip('등급안내'), findsOneWidget);
    await tester.tap(find.byTooltip('등급안내'));
    await tester.pumpAndSettle();
    expect(find.text('회원 등급 안내'), findsOneWidget);
    expect(find.textContaining('아이러브미니에서 승인한 MINI 회원'), findsOneWidget);
    expect(find.textContaining('아이러브미니에서 등록된 협력업체 담당자'), findsOneWidget);
  });
  testWidgets('general account page has no unscoped partner registration button',
      (tester) async {
    final api = ApiClient(client: MockClient((request) async {
      final list = request.url.path.endsWith('/vehicles/') ||
          request.url.path.contains('bookings') || request.url.path.contains('ledger');
      return http.Response(jsonEncode(list ? [] : {'grade': 'general'}), 200,
          headers: {'content-type': 'application/json; charset=utf-8'});
    }));
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: AccountPage(
      api: api, signedIn: true, pushEnabled: false,
      onPushChanged: (_) {}, onLogin: () {}, onLogout: () {},
      onManageVehicles: () {},
    ))));
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView).first, const Offset(0, -1800));
    await tester.pumpAndSettle();
    expect(find.text('회원 계정 삭제'), findsOneWidget);
    expect(find.text('협력업체 정비 인증기록 등록'), findsNothing);
    expect(find.text('회원 차량 QR 스캔'), findsNothing);
  });

}
