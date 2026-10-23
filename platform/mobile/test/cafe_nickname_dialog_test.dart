import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';
import 'package:ilovemini/main.dart';

void main() {
  setUp(() => FlutterSecureStorage.setMockInitialValues({'access_token': 'test'}));
  testWidgets('nickname dialog can cancel with focused input and reopen safely', (tester) async {
    var writes = 0;
    final api = ApiClient(client: MockClient((request) async {
      if (request.method != 'GET') writes++;
      return http.Response(jsonEncode({'cafe_nickname': ''}), 200,
          headers: {'content-type': 'application/json; charset=utf-8'});
    }));
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('ko', 'KR'),
      supportedLocales: const [Locale('ko', 'KR')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      home: Scaffold(body: CafeNicknameSection(api: api)),
    ));
    await tester.pumpAndSettle();
    for (var i = 0; i < 2; i++) {
      await tester.tap(find.text('등록'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextFormField), '테스트닉네임');
      await tester.tap(find.text('취소'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(find.text('카페 닉네임 설정'), findsNothing);
    }
    expect(writes, 0);
  });
}
