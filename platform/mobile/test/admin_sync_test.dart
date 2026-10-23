import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';
import 'package:ilovemini/app_refresh.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() =>
      FlutterSecureStorage.setMockInitialValues({'access_token': 'token'}));
  test('admin primary vehicle is first without dropping other vehicles',
      () async {
    final api = ApiClient(
        client: MockClient((request) async => http.Response(
            jsonEncode(request.url.path.endsWith('/vehicles/')
                ? [
                    {'id': 1},
                    {'id': 2}
                  ]
                : {'primary_vehicle_id': 2}),
            200)));
    expect((await api.list('vehicles')).map((r) => r['id']), [2, 1]);
  });
  test('booking cancellation submits reason to server', () async {
    final api = ApiClient(client: MockClient((request) async {
      expect(request.url.path, '/api/bookings/7/cancel/');
      expect(jsonDecode(request.body)['cancellation_reason'], '일정 변경');
      return http.Response('{}', 200);
    }));
    await api.cancelPartnerBooking(7, reason: '일정 변경');
  });
  testWidgets(
      'poll only refreshes changes, survives failures and stops in background',
      (tester) async {
    var revision = 1;
    var fail = false;
    var calls = 0;
    var changes = 0;
    final api = ApiClient(client: MockClient((request) async {
      calls++;
      return http.Response(
          fail
              ? '{}'
              : jsonEncode({
                  'public_revision': revision,
                  'member_revision': 1,
                  'service_categories': ['PPF', '경정비'],
                  'configuration': {'refresh_interval_seconds': 10}
                }),
          fail ? 503 : 200,
          headers: {"content-type": "application/json; charset=utf-8"});
    }));
    final controller = AppRefreshController(api, () => changes++, () {});
    controller.start();
    await tester.pumpAndSettle();
    expect(changes, 1);
    expect(api.serviceCategories, ['PPF', '경정비']);
    await tester.pump(const Duration(seconds: 10));
    await tester.pumpAndSettle();
    expect(changes, 1);
    revision++;
    await tester.pump(const Duration(seconds: 10));
    await tester.pumpAndSettle();
    expect(changes, 2);
    fail = true;
    await tester.pump(const Duration(seconds: 10));
    await tester.pumpAndSettle();
    expect(changes, 2);
    controller.stop();
    final stopped = calls;
    await tester.pump(const Duration(seconds: 30));
    expect(calls, stopped);
  });
}
