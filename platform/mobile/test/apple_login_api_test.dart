import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('Apple login sends the verified-token payload and stores session tokens',
      () async {
    final api = ApiClient(
      client: MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/auth/apple/');
        expect(jsonDecode(request.body), {
          'identity_token': 'apple-id-token',
          'nonce': 'secure-nonce',
          'terms_accepted': true,
          'privacy_accepted': true,
        });
        return http.Response(
          jsonEncode({'access': 'apple-access', 'refresh': 'apple-refresh'}),
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );

    await api.loginWithApple('apple-id-token', 'secure-nonce',
        termsAccepted: true, privacyAccepted: true);

    const storage = FlutterSecureStorage();
    expect(await storage.read(key: 'access_token'), 'apple-access');
    expect(await storage.read(key: 'refresh_token'), 'apple-refresh');
  });
}
