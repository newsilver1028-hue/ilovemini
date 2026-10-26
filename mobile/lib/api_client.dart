import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class ApiClient {
  ApiClient({http.Client? client, Duration requestTimeout = const Duration(seconds: 90)}) : _client = _SessionClient(
    client ?? http.Client(), const FlutterSecureStorage(),
    () => sessionExpired.value++, requestTimeout,
  );
  static final sessionExpired = ValueNotifier<int>(0);
  final http.Client _client;
  final _storage = const FlutterSecureStorage();
  static const _baseUrl = String.fromEnvironment('ILOVEMINI_API_URL', defaultValue: 'https://ilovemini.onrender.com/api');
  static const demoMode = bool.fromEnvironment('ILOVEMINI_DEMO', defaultValue: false);
  static final List<Map<String, dynamic>> _demoVehicles = [
    {'id': 1, 'public_id': '00000000-0000-4000-8000-000000000001', 'model_name': 'MINI Cooper S', 'trim': 'Favoured', 'nickname': '미리보기 MINI', 'generation': '4세대 F66', 'model_year': 2025, 'current_odometer_km': 27487},
    {'id': 2, 'public_id': '00000000-0000-4000-8000-000000000002', 'model_name': 'Mercedes-Maybach S 580 4MATIC', 'trim': 'S 580 4MATIC', 'nickname': '마이바흐', 'generation': 'S-Class Z223', 'model_year': 2026, 'current_odometer_km': 1240, 'sample_data': true},
  ];
  static final List<Map<String, dynamic>> _demoLedger = [
    {'id': 101, 'vehicle': 1, 'kind': 'fuel', 'entry_date': '2026-09-21', 'description': '고급휘발유', 'amount_krw': 86000, 'odometer_km': 27310, 'source': 'owner'},
    {'id': 102, 'vehicle': 1, 'kind': 'service', 'entry_date': '2026-09-18', 'description': '엔진오일 및 필터 교환', 'amount_krw': 180000, 'odometer_km': 27120, 'source': 'partner', 'partner_name': '크란츠모터스 구리'},
    {'id': 103, 'vehicle': 1, 'kind': 'service', 'entry_date': '2026-05-12', 'description': '앞 브레이크 패드 교환', 'amount_krw': 420000, 'odometer_km': 25840, 'source': 'partner', 'partner_name': '아라바서비스'},
    {'id': 104, 'vehicle': 1, 'kind': 'part', 'entry_date': '2026-02-03', 'description': '배터리 교체', 'amount_krw': 390000, 'odometer_km': 23500, 'source': 'partner', 'partner_name': '수리아 용인'},
    {'id': 105, 'vehicle': 1, 'kind': 'part', 'entry_date': '2025-12-20', 'description': '겨울용 타이어 교체', 'amount_krw': 0, 'odometer_km': 22110, 'source': 'partner', 'partner_name': '티스테이션 종암'},
    {'id': 106, 'vehicle': 2, 'kind': 'fuel', 'entry_date': '2026-09-24', 'description': '프리미엄 휘발유', 'amount_krw': 140000, 'odometer_km': 1120, 'source': 'owner'},
  ];
  static final List<Map<String, dynamic>> _demoReminders = [];
  static int _demoNextId = 106;
  Uri _uri(String path) => Uri.parse('$_baseUrl/$path/');

  Future<Uri> startNaverLogin() async {
    final response = await _client.post(_uri('auth/naver/start'), headers: {'Content-Type': 'application/json'});
    if (response.statusCode != 200) throw Exception(_message(response));
    return Uri.parse(jsonDecode(response.body)['authorization_url'] as String);
  }

  Future<void> completeNaverLogin(String ticket, {required bool termsAccepted, required bool privacyAccepted}) async {
    final response = await _client.post(_uri('auth/naver/complete'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'ticket': ticket, 'terms_accepted': termsAccepted, 'privacy_accepted': privacyAccepted}));
    if (response.statusCode != 200) throw Exception(_message(response));
    final tokens = jsonDecode(response.body);
    await _storage.write(key: 'access_token', value: tokens['access'] as String);
    await _storage.write(key: 'refresh_token', value: tokens['refresh'] as String);
  }

  Future<void> logout() => _storage.deleteAll();
  Future<bool> get isSignedIn async => (await _storage.read(key: 'access_token')) != null;
  Future<bool> get pushNotificationsEnabled async => (await _storage.read(key: 'push_notifications_enabled')) == 'true';
  Future<void> setPushNotificationsEnabled(bool enabled) => _storage.write(key: 'push_notifications_enabled', value: enabled.toString());

  Future<Map<String, dynamic>> attendanceSummary() async {
    if (demoMode) return _demoAttendancePayload();
    final token = await _storage.read(key: 'access_token');
    final response = await _client.get(_uri('attendance'), headers: {if (token != null) 'Authorization': 'Bearer $token'});
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> memberGrade() async {
    if (demoMode) return {'grade': 'general', 'grade_label': '일반회원'};
    final token = await _storage.read(key: 'access_token');
    if (token == null) throw Exception('로그인이 필요합니다.');
    final response = await _client.get(_uri('me/grade'), headers: {'Authorization': 'Bearer $token'});
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createPartnerBooking(Map<String, dynamic> data) async {
    if (demoMode) throw Exception('예약을 서버에 저장하려면 정식 API에 로그인해야 합니다.');
    final token = await _storage.read(key: 'access_token');
    if (token == null) throw Exception('로그인 후 예약을 요청할 수 있습니다.');
    final response = await _client.post(_uri('bookings'), headers: {
      'Content-Type': 'application/json', 'Authorization': 'Bearer $token',
    }, body: jsonEncode(data));
    if (response.statusCode != 201) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> partnerBookingSlots(int partnerId, DateTime date, String serviceType) async {
    final day = '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
    final uri = _uri('partners/$partnerId/booking-slots').replace(queryParameters: {'date': day, 'service_type': serviceType});
    final response = await _client.get(uri);
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> cancelPartnerBooking(int bookingId) async {
    final token = await _storage.read(key: 'access_token');
    if (token == null) throw Exception('로그인이 필요합니다.');
    final response = await _client.post(_uri('bookings/$bookingId/cancel'), headers: {
      'Content-Type': 'application/json', 'Authorization': 'Bearer $token',
    }, body: jsonEncode({}));
    if (response.statusCode != 200) throw Exception(_message(response));
  }

  Future<void> respondToPartnerBooking(int bookingId, {required String status, String note = ''}) async {
    final token = await _storage.read(key: 'access_token');
    if (token == null) throw Exception('로그인이 필요합니다.');
    final response = await _client.post(_uri('bookings/$bookingId/respond'), headers: {
      'Content-Type': 'application/json', 'Authorization': 'Bearer $token',
    }, body: jsonEncode({'status': status, 'partner_note': note}));
    if (response.statusCode != 200) throw Exception(_message(response));
  }

  Future<Map<String, dynamic>> scanVehiclePassport(String publicId) async {
    final token = await _storage.read(key: 'access_token');
    if (token == null) throw Exception('협력업체 로그인 후 사용할 수 있습니다.');
    final response = await _client.post(_uri('vehicles/scan-passport'), headers: {
      'Content-Type': 'application/json', 'Authorization': 'Bearer $token',
    }, body: jsonEncode({'vehicle_public_id': publicId}));
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> searchCafePosts(String query) async {
    final uri = _uri('cafe/search').replace(queryParameters: {'q': query});
    final response = await _client.get(uri);
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> latestCafePosts() async {
    final response = await _client.get(_uri('cafe/latest'));
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> checkIn() async {
    if (demoMode) {
      final rows = await _readDemoCheckins();
      final today = _demoKstDate();
      if (rows.any((row) => row['date'] == today)) return _demoAttendancePayload(earned: 0);
      final yesterday = DateTime.parse(today).subtract(const Duration(days: 1)).toIso8601String().substring(0, 10);
      final prior = rows.where((row) => row['date'] == yesterday).firstOrNull;
      final streak = prior == null ? 1 : (prior['streak_days'] as int? ?? 0) + 1;
      final points = 1000 + (streak % 7 == 0 ? 3000 : 0);
      rows.insert(0, {'date': today, 'points': points, 'streak_days': streak});
      await _storage.write(key: 'demo_attendance_checkins', value: jsonEncode(rows));
      return _demoAttendancePayload(earned: points);
    }
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(_uri('attendance'), headers: {
      'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token',
    }, body: jsonEncode({}));
    if (response.statusCode != 200 && response.statusCode != 201) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  String _demoKstDate() {
    final now = DateTime.now().toUtc().add(const Duration(hours: 9));
    return '${now.year.toString().padLeft(4, '0')}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
  }

  Future<List<Map<String, 