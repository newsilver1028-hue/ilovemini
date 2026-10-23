import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ilovemini/api_client.dart';
import 'package:ilovemini/main.dart';
void main() {
 testWidgets('home does not restore removed record and partner shortcuts', (tester) async {
  FlutterSecureStorage.setMockInitialValues({});
  final api=ApiClient(client:MockClient((_) async=>http.Response('[]',200)));
  await tester.pumpWidget(MaterialApp(home:Scaffold(body:HomePage(api:api,signedIn:false,onOpenGarage:(){},onLogin:(){}))));
  expect(find.widgetWithText(OutlinedButton,'업체 찾기'),findsNothing);
  expect(find.widgetWithText(OutlinedButton,'기록 추가'),findsNothing);
  expect(tester.takeException(),isNull);
 });
}
