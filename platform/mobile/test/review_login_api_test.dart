import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('app review login sends credentials and stores issued tokens', () async {
    final api = ApiClient(
      client: MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/auth/review-login/');
        expect(jsonDecode(request.body), {
          'username': 'review-user',
          'password': 'sample-password-123',
        });
        return http.Response(
          jsonEncode({
            'access': 'review-access-token',
            'refresh': 'review-refresh-token'
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );

    await api.loginForAppReview(' review-user ', 'sample-password-123');

    const storage = FlutterSecureStorage();
    expect(await storage.read(key: 'access_token'), 'review-access-token');
    expect(await storage.read(key: 'refresh_token'), 'review-refresh-token');
  });

  test('app review login does not store tokens after a rejected login',
      () async {
    final api = ApiClient(
      client: MockClient((_) async => http.Response(
            jsonEncode({'detail': '로그인 정보를 확인해 주세요.'}),
            400,
            headers: {'content-type': 'application/json'},
          )),
    );

    await expectLater(
      api.loginForAppReview('review-user', 'wrong-password'),
      throwsException,
    );

    const storage = FlutterSecureStorage();
    expect(await storage.read(key: 'access_token'), isNull);
  });
}
