import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';
import 'package:ilovemini/main.dart';
import 'package:qr_flutter/qr_flutter.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'test-token'});
  });

  testWidgets(
      'membership expands only after device authentication and can collapse',
      (tester) async {
    final auth = Completer<bool>();
    var authCalls = 0;
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
        const MethodChannel('plugins.flutter.io/local_auth'), (call) async {
      if (call.method == 'isDeviceSupported') return true;
      if (call.method == 'authenticate') {
        authCalls++;
        return auth.future;
      }
      return null;
    });
    final api = ApiClient(client: MockClient((request) async {
      Object payload = [];
      if (request.url.path.endsWith('/vehicles/')) {
        payload = [
          {
            'id': 1,
            'public_id': 'vehicle-one',
            'model_name': 'MINI Cooper',
            'nickname': '첫 차',
            'plate_number': '12가3456'
          },
          {
            'id': 2,
            'public_id': 'vehicle-two',
            'model_name': 'MINI Clubman',
            'nickname': '두 번째 차',
            'plate_number': '34나5678'
          },
        ];
      } else if (request.url.path.endsWith('/app/content/')) {
        payload = {'banners': [], 'products': [], 'releases': []};
      }
      return http.Response.bytes(utf8.encode(jsonEncode(payload)), 200,
          headers: {'content-type': 'application/json'});
    }));
    await tester.pumpWidget(MaterialApp(home: MainShell(api: api)));
    await tester.pumpAndSettle();
    expect(find.text('ILOVEMINI MEMBERSHIP'), findsOneWidget);
    expect(find.byType(QrImageView), findsNothing);
    await tester.tap(find.text('ILOVEMINI MEMBERSHIP'));
    await tester.pumpAndSettle();
    expect(authCalls, 1);
    expect(find.byType(QrImageView), findsNothing);
    auth.complete(true);
    await tester.pumpAndSettle();
    expect(find.byType(QrImageView), findsOneWidget);
    expect(
        tester
            .widget<DropdownButton<Map<String, dynamic>>>(
                find.byType(DropdownButton<Map<String, dynamic>>))
            .value!['id'],
        1);
    await tester.tap(find.byType(DropdownButton<Map<String, dynamic>>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('두 번째 차').last);
    await tester.pumpAndSettle();
    expect(
        tester
            .widget<DropdownButton<Map<String, dynamic>>>(
                find.byType(DropdownButton<Map<String, dynamic>>))
            .value!['id'],
        2);
    await tester.tap(find.text('ILOVEMINI MEMBERSHIP'));
    await tester.pumpAndSettle();
    expect(find.byType(QrImageView), findsNothing);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
