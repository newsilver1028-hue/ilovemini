import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
      'multiple compressed partner record photos are sent as authenticated multipart data',
      () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'test-token'});
    var sawMultipart = false;
    final api = ApiClient(
      client: MockClient((request) async {
        expect(request.headers['authorization'], 'Bearer test-token');
        expect(request.headers['content-type'],
            startsWith('multipart/form-data;'));
        final body = utf8.decode(request.bodyBytes);
        expect(RegExp('name=\"evidence_images\"').allMatches(body).length, 2);
        expect(body, contains('wheel_tire'));
        expect(body, contains('compressed-receipt'));
        expect(body, contains('compressed-work-photo'));
        sawMultipart = true;
        return http.Response(jsonEncode({'id': 17}), 201,
            headers: {'content-type': 'application/json'});
      }),
    );

    final result = await api.createPartnerVerifiedRecord({
      'partner': 4,
      'kind': 'wheel_tire',
      'description': '휠 타이어 교체',
    }, evidenceImages: [
      Uint8List.fromList(utf8.encode('compressed-receipt')),
      Uint8List.fromList(utf8.encode('compressed-work-photo')),
    ], evidenceImageNames: [
      'receipt.jpg',
      'work.jpg'
    ]);

    expect(sawMultipart, isTrue);
    expect(result['id'], 17);
  });
}
