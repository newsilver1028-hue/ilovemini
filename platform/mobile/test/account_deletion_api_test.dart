import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => FlutterSecureStorage.setMockInitialValues({
        'access_token': 'access-token',
        'refresh_token': 'refresh-token',
      }));

  test('account deletion calls the authenticated endpoint and clears tokens',
      () async {
    const storage = FlutterSecureStorage();
    Uri? requestedUri;
    String? authorization;
    final api = ApiClient(
      client: MockClient((request) async {
        requestedUri = request.url;
        authorization = request.headers['Authorization'];
        expect(request.method, 'DELETE');
        return http.Response('', 204);
      }),
    );

    await api.deleteAccount();

    expect(requestedUri!.path, '/api/me/account/');
    expect(authorization, 'Bearer access-token');
    expect(await storage.read(key: 'access_token'), isNull);
    expect(await storage.read(key: 'refresh_token'), isNull);
  });

  test('failed deletion keeps the current login session', () async {
    final api = ApiClient(client: MockClient((request) async => http.Response(
      jsonEncode({'detail': 'Apple 연결 해제를 완료하지 못했습니다.'}), 503,
      headers: {'content-type': 'application/json; charset=utf-8'})));
    await expectLater(api.deleteAccount(), throwsException);
    expect(await const FlutterSecureStorage().read(key: 'access_token'), 'access-token');
  });

  test('Apple reauthentication credentials are sent only for account deletion', () async {
    final api = ApiClient(client: MockClient((request) async {
      expect(request.url.path, '/api/me/account/');
      expect(jsonDecode(request.body), {
        'apple_identity_token': 'id-token', 'apple_nonce': 'nonce',
        'apple_authorization_code': 'one-time-code',
      });
      return http.Response('', 204);
    }));
    await api.deleteAccount(appleIdentityToken: 'id-token', appleNonce: 'nonce',
        appleAuthorizationCode: 'one-time-code');
  });
}

