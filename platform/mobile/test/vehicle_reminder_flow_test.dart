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

  Future<void> openGarage(WidgetTester tester, {bool withVehicle = false}) async {
    final api = ApiClient(client: MockClient((request) async {
      if (request.url.path.endsWith('/vehicles/')) {
        return http.Response.bytes(utf8.encode(jsonEncode(withVehicle ? [
          {
            'id': 1,
            'model_name': 'MINI Cooper S',
            'generation': 'F56',
            'plate_number': '12가3456',
            'current_odometer_km': 15000,
            'ownership_relationship': 'owned',
          }
        ] : [])), 200,
            headers: {'content-type': 'application/json; charset=utf-8'});
      }
      if (request.url.path.contains('/maintenance-summary/')) {
        return http.Response(jsonEncode({
          'verified_record_count': 0,
          'correction_count': 0,
          'pending_reminder_count': 0,
          'overdue_reminder_count': 0,
          'next_due_date': null,
          'next_due_odometer_km': null,
          'last_verified_entry': null,
          'next_management_items': [],
        }), 200);
      }
      return http.Response('[]', 200);
    }));
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(body: GaragePage(api: api, signedIn: true, onLogin: () {})),
    ));
    await tester.pumpAndSettle();
  }

  testWidgets('vehicle catalog selection keeps parent form stable', (tester) async {
    await openGarage(tester);
    await tester.tap(find.text('차량 등록'));
    await tester.pumpAndSettle();
    expect(find.text('내 차량 등록'), findsOneWidget);
    await tester.tap(find.text('차종 선택 *'));
    await tester.pumpAndSettle();
    expect(find.text('차종 선택'), findsOneWidget);
    final brandDropdown = find.ancestor(of: find.text('브랜드'), matching: find.byType(DropdownButtonFormField<String>));
    await tester.tap(brandDropdown);
    await tester.pumpAndSettle();
    expect(find.text('MINI'), findsWidgets);
    await tester.tap(find.text('MINI').last);
    await tester.pumpAndSettle();
    final modelDropdown = find.ancestor(of: find.text('차종'), matching: find.byType(DropdownButtonFormField<String>));
    await tester.tap(modelDropdown);
    await tester.pumpAndSettle();
    await tester.tap(find.text('쿠퍼 3도어').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('차종 선택 완료'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.text('내 차량 등록'), findsOneWidget);
    await tester.enterText(find.byType(TextFormField).at(0), '12가3456');
    await tester.enterText(find.byType(TextFormField).at(1), '15000');
    await tester.tap(find.text('등록'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('reminder form validates and cancels without lifecycle errors', (tester) async {
    await openGarage(tester, withVehicle: true);
    await tester.drag(find.byType(ListView).last, const Offset(0, -900));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('알림 추가'));
    await tester.tap(find.text('알림 추가'));
    await tester.pumpAndSettle();
    expect(find.text('정비 알림 추가'), findsAtLeastNWidgets(1));
    await tester.tap(find.text('알림 저장'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.text('취소'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('garage exposes delete action with confirmation', (tester) async {
    await openGarage(tester, withVehicle: true);
    expect(find.byTooltip('차량 삭제'), findsOneWidget);
    await tester.tap(find.byTooltip('차량 삭제'));
    await tester.pumpAndSettle();
    expect(find.textContaining('연결된 차계부와 정비 알림도 함께 삭제됩니다.'), findsOneWidget);
    await tester.tap(find.text('취소').last);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  test('vehicle delete request preserves server protection response', () async {
    final api = ApiClient(client: MockClient((request) async {
      expect(request.method, 'DELETE');
      expect(request.url.path, '/api/vehicles/3/');
      return http.Response.bytes(
          utf8.encode(jsonEncode(
              {'detail': '협력업체 인증기록이 있는 차량은 삭제할 수 없습니다.'})),
          409,
          headers: {'content-type': 'application/json; charset=utf-8'});
    }));

    await expectLater(
      api.deleteVehicle(3),
      throwsA(isA<Exception>().having(
        (error) => error.toString(),
        'message',
        contains('협력업체 인증기록이 있는 차량은 삭제할 수 없습니다.'),
      )),
    );
  });
}
