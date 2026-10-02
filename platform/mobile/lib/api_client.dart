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

  Future<Map<String, dynamic>> lookupVehicleByPlate(String plateNumber) async {
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(_uri('vehicles/lookup-plate'), headers: {
      'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token',
    }, body: jsonEncode({'plate_number': plateNumber}));
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> scanVehiclePassport(String publicId, String plateNumber) async {
    final token = await _storage.read(key: 'access_token');
    if (token == null) throw Exception('협력업체 로그인 후 사용할 수 있습니다.');
    final response = await _client.post(_uri('vehicles/scan-passport'), headers: {
      'Content-Type': 'application/json', 'Authorization': 'Bearer $token',
    }, body: jsonEncode({'vehicle_public_id': publicId, 'plate_number': plateNumber}));
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

  Future<List<Map<String, dynamic>>> _readDemoCheckins() async {
    final raw = await _storage.read(key: 'demo_attendance_checkins');
    if (raw == null) return [];
    try {
      final rows = (jsonDecode(raw) as List).cast<Map<String, dynamic>>();
      var changed = false;
      for (final row in rows) {
        final oldPoints = (row['points'] as num?)?.toInt();
        if (oldPoints == 10) { row['points'] = 1000; changed = true; }
        if (oldPoints == 40) { row['points'] = 4000; changed = true; }
      }
      if (changed) await _storage.write(key: 'demo_attendance_checkins', value: jsonEncode(rows));
      return rows;
    } catch (_) { return []; }
  }

  Future<Map<String, dynamic>> _demoAttendancePayload({int? earned}) async {
    final rows = await _readDemoCheckins();
    final today = _demoKstDate();
    final todayRow = rows.where((row) => row['date'] == today).firstOrNull;
    var expected = DateTime.parse(todayRow == null
      ? DateTime.parse(today).subtract(const Duration(days: 1)).toIso8601String().substring(0, 10)
      : today);
    var streak = 0;
    final dates = rows.map((row) => row['date'] as String).toSet();
    while (dates.contains(expected.toIso8601String().substring(0, 10))) {
      streak++;
      expected = expected.subtract(const Duration(days: 1));
    }
    final balance = rows.fold<int>(0, (sum, row) => sum + ((row['points'] as num?)?.toInt() ?? 0));
    return {
      'balance_points': balance, 'checked_in_today': todayRow != null,
      'today_points': (todayRow?['points'] as num?)?.toInt() ?? 0,
      'streak_days': streak, 'next_bonus_in_days': streak == 0 ? 7 : 7 - streak % 7,
      'checkins': rows.take(30).toList(), if (earned != null) 'earned_points': earned,
    };
  }

  Future<List<Map<String, dynamic>>> list(String path) async {
    if (demoMode) return _demoRows(path);
    final parts = path.split('?');
    final query = parts.length > 1 ? Uri.splitQueryString(parts[1]) : <String, String>{};
    Uri? next = _uri(parts.first).replace(queryParameters: query.isEmpty ? null : query);
    final rows = <Map<String, dynamic>>[];
    final visited = <String>{};
    final base = Uri.parse(_baseUrl);
    while (next != null) {
      final uri = next;
      if (uri.origin != base.origin || !uri.path.startsWith('${base.path}/') ||
          !visited.add(uri.toString())) {
        throw Exception('목록 페이지 주소가 올바르지 않습니다.');
      }
      final token = await _storage.read(key: 'access_token');
      final response = await _client.get(uri, headers: {if (token != null) 'Authorization': 'Bearer $token'});
      if (response.statusCode != 200) throw Exception(_message(response));
      final decoded = jsonDecode(response.body);
      if (decoded is List) {
        rows.addAll(decoded.cast<Map<String, dynamic>>());
        break;
      }
      rows.addAll((decoded['results'] as List).cast<Map<String, dynamic>>());
      final nextLink = decoded['next'] as String?;
      next = nextLink == null ? null : uri.resolve(nextLink);
    }
    return rows;
  }

  List<Map<String, dynamic>> _demoRows(String path) {
    final resource = path.split('?').first;
    if (resource == 'vehicles') return List.of(_demoVehicles);
    final query = path.contains('?') ? Uri.splitQueryString(path.split('?').last) : <String, String>{};
    if (resource == 'ledger') return _forDemoVehicle(_demoLedger, query['vehicle']);
    if (resource == 'reminders') return _forDemoVehicle(_demoReminders, query['vehicle']);
    const partners = [
      {'id': 1, 'name': '아이모터스랩', 'region': '서울 성수 · 경기 분당', 'service_categories': ['판금·도색', '사고수리'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/347', 'icon': '🚘', 'is_sponsored': false},
      {'id': 2, 'name': '리본모터스 분당', 'region': '경기 분당', 'service_categories': ['판금·도색', '사고수리'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/399', 'icon': '🛠️', 'is_sponsored': false},
      {'id': 3, 'name': '랩스타모터스', 'region': '서울/경기', 'service_categories': ['사고수리'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/286', 'icon': '🔧', 'is_sponsored': false},
      {'id': 4, 'name': '성남 한국자동차유리', 'region': '경기 성남', 'service_categories': ['유리 교환·복원'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/412', 'icon': '🪟', 'is_sponsored': false},
      {'id': 5, 'name': '글라스히어로즈', 'region': '서울/경기', 'service_categories': ['유리 교환·복원'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/509', 'icon': '🪟', 'is_sponsored': false},
      {'id': 6, 'name': '용자팩토리', 'region': '서울/경기', 'service_categories': ['전장', '튜닝'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/461', 'icon': '⚡', 'is_sponsored': false},
      {'id': 7, 'name': '말자동차', 'region': '서울/경기', 'service_categories': ['전장·튜닝'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/478', 'icon': '🚗', 'is_sponsored': false},
      {'id': 8, 'name': '에스튠 수원', 'region': '경기 수원', 'service_categories': ['튜닝·전장'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/580', 'icon': '🎛️', 'is_sponsored': false},
      {'id': 9, 'name': '카카오파츠 서초', 'region': '서울 서초', 'service_categories': ['자동차 부품', '튜닝'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/240', 'icon': '⚙️', 'is_sponsored': false},
      {'id': 28, 'name': '인치업매니아 송파점', 'branch_label': '송파점', 'region': '서울 송파구', 'service_categories': ['휠', '타이어'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': '', 'icon': '🛞', 'is_sponsored': false},
      {'id': 10, 'name': '휘스토리 강북', 'region': '서울 강북', 'service_categories': ['휠', '타이어'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/380', 'icon': '🛞', 'is_sponsored': false},
      {'id': 11, 'name': '군팩토리', 'region': '경기 하남', 'service_categories': ['오디오', '전장', 'MINI 전문'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/660', 'icon': '🔊', 'is_sponsored': false},
      {'id': 12, 'name': '인천 포텐(휠수리)', 'region': '인천', 'service_categories': ['휠 복원·수리'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/518', 'icon': '🛞', 'is_sponsored': false},
      {'id': 13, 'name': '티스테이션 종암', 'region': '서울 종암', 'service_categories': ['타이어'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/236', 'icon': '🛞', 'is_sponsored': false},
      {'id': 14, 'name': '힐링휠복원 남양주', 'region': '경기 남양주', 'service_categories': ['휠 복원'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/540', 'icon': '✨', 'is_sponsored': false},
      {'id': 15, 'name': '아라바서비스', 'region': '서울/경기', 'service_categories': ['정비', '수입차'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/349', 'icon': '🔩', 'is_sponsored': false},
      {'id': 16, 'name': '수리아 용인', 'region': '경기 용인', 'service_categories': ['정비'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/642', 'icon': '🧰', 'is_sponsored': false},
      {'id': 17, 'name': '가람모터스 별내', 'region': '경기 별내', 'service_categories': ['정비', '수입차'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/625', 'icon': '🔧', 'is_sponsored': false},
      {'id': 18, 'name': '크란츠모터스 구리', 'region': '경기 구리', 'service_categories': ['MINI 정비', '수입차 수리'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/425', 'icon': '🛠️', 'is_sponsored': false},
      {'id': 19, 'name': '모터스힐 구리', 'region': '경기 구리', 'service_categories': ['정비'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/623', 'icon': '🚙', 'is_sponsored': false},
      {'id': 20, 'name': 'DH모터스 부천', 'region': '경기 부천', 'service_categories': ['정비'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/557', 'icon': '🔧', 'is_sponsored': false},
      {'id': 21, 'name': '한국디젤카연구소 논산', 'region': '충남 논산', 'service_categories': ['디젤 정비'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/543', 'icon': '🛠️', 'is_sponsored': false},
      {'id': 22, 'name': '에이블모터스 부산', 'region': '부산', 'service_categories': ['수입차 정비'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/288', 'icon': '🚘', 'is_sponsored': false},
      {'id': 23, 'name': '제틀리시 부산', 'region': '부산', 'service_categories': ['정비'], 'description': '아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.', 'cafe_url': 'https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/636', 'icon': '🔩', 'is_sponsored': false},
      {'id': 24, 'name': '모터스킨', 'region': '지역 확인 필요', 'region_group': '신차패키지', 'category': '신차패키지', 'service_categories': ['신차패키지'], 'description': '아이러브미니 협력업체 목록의 신차패키지 분야에 등록된 업체입니다. 지역과 작업 범위는 업체에 확인해 주세요.', 'icon': '🚘', 'is_sponsored': false},
      {'id': 25, 'name': '렌트리스 얼마면탈까', 'region': '지역 확인 필요', 'region_group': '신차패키지', 'category': '신차패키지', 'service_categories': ['신차패키지'], 'description': '아이러브미니 협력업체 목록의 신차패키지 분야에 등록된 업체입니다. 지역과 상담 범위는 업체에 확인해 주세요.', 'icon': '🚘', 'is_sponsored': false},
      {'id': 26, 'name': '수입차부품 프린트랩', 'region': '지역 확인 필요', 'region_group': '신차패키지', 'category': '신차패키지', 'service_categories': ['신차패키지', '수입차 부품'], 'description': '아이러브미니 협력업체 목록의 신차패키지 분야에 등록된 업체입니다. 지역과 취급 품목은 업체에 확인해 주세요.', 'icon': '⚙️', 'is_sponsored': false},
      {'id': 27, 'name': '대한민국대표 금호타이어', 'region': '지역 확인 필요', 'region_group': '신차패키지', 'category': '신차패키지', 'service_categories': ['신차패키지', '타이어'], 'description': '아이러브미니 협력업체 목록의 신차패키지 분야에 등록된 업체입니다. 지역과 취급 품목은 업체에 확인해 주세요.', 'icon': '🛞', 'is_sponsored': false},
    ];
    switch (resource) {
      case 'notices':
        return [
          {'id': 1, 'title': '아이러브미니 앱 미리보기', 'summary': '공지와 카페 소식을 앱에서 모아보는 화면입니다.', 'is_sponsored': false},
          {'id': 2, 'title': '오너 혜택을 한곳에서 확인하세요', 'summary': '운영자가 등록한 공지와 이벤트가 이곳에 표시됩니다.', 'is_sponsored': false},
        ];
      case 'partners':
        return partners;
      case 'offers':
        return [
          {'id': 1, 'partner': 11, 'title': '군팩토리 MINI 오디오 패키지', 'description': '블라우펑트 1402 CM4 + 8인치 우퍼\nA · 포칼 ISUB BMW 4: 정상 190만원 / 안내가 130만원\nB · 오디슨 APBMW S8-4.2: 정상 210만원 / 안내가 140만원\nC · AVI BM204: 정상 228만원 / 안내가 150만원', 'redemption_instructions': '운영자 제공 안내 기준입니다. 현재 구성·가격·재고는 방문 전 업체에 확인해 주세요.'},
          {'id': 2, 'partner': 18, 'title': '크란츠모터스 제휴 이벤트 예시', 'description': '협력업체 프로모션을 보여주는 미리보기입니다.', 'redemption_instructions': '앱 정식 오픈 후 상세 안내 예정'},
        ];
      default:
        return [];
    }
  }

  List<Map<String, dynamic>> _forDemoVehicle(List<Map<String, dynamic>> rows, String? vehicleId) =>
      List.of(vehicleId == null ? rows : rows.where((row) => row['vehicle'].toString() == vehicleId));

  Future<void> create(String path, Map<String, dynamic> data) async {
    if (demoMode) {
      final id = ++_demoNextId;
      switch (path) {
        case 'vehicles':
          _demoVehicles.add({'id': id, ...data});
          break;
        case 'ledger':
          _demoLedger.insert(0, {'id': id, ...data});
          final vehicleIndex = _demoVehicles.indexWhere((vehicle) => vehicle['id'] == data['vehicle']);
          final newOdometer = data['odometer_km'] as int?;
          if (vehicleIndex >= 0 && newOdometer != null) {
            final oldOdometer = _demoVehicles[vehicleIndex]['current_odometer_km'] as int? ?? 0;
            if (newOdometer > oldOdometer) _demoVehicles[vehicleIndex]['current_odometer_km'] = newOdometer;
          }
          break;
        case 'reminders':
          _demoReminders.insert(0, {'id': id, 'is_complete': false, ...data});
          break;
      }
      return;
    }
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(_uri(path), headers: {'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token'}, body: jsonEncode(data));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception(_message(response));
  }

  Future<Map<String, dynamic>> createVehicleTransferCode(int vehicleId) async {
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(
      _uri('vehicles/$vehicleId/transfer-code'),
      headers: {'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token'},
    );
    if (response.statusCode != 201) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getVehicleMaintenanceSummary(int vehicleId) async {
    if (demoMode) {
      final ledger = _forDemoVehicle(_demoLedger, vehicleId.toString());
      final maintenance = ledger.where((row) => row['kind'] == 'service' || row['kind'] == 'part').toList()
        ..sort((a, b) => (b['entry_date'] ?? '').toString().compareTo((a['entry_date'] ?? '').toString()));
      final reminders = _forDemoVehicle(_demoReminders, vehicleId.toString())
          .where((row) => row['is_complete'] != true && row['completed_at'] == null).toList();
      final dueDates = reminders.map((row) => row['due_date']).whereType<String>().toList()..sort();
      final dueKm = reminders.map((row) => row['due_odometer_km']).whereType<int>().toList()..sort();
      final matchingVehicles = _demoVehicles.where((row) => row['id'] == vehicleId).toList();
      final vehicle = matchingVehicles.isEmpty ? null : matchingVehicles.first;
      final currentKm = vehicle?['current_odometer_km'] as int?;
      final today = DateTime.now();
      final overdue = reminders.where((row) {
        final date = DateTime.tryParse((row['due_date'] ?? '').toString());
        final km = row['due_odometer_km'] as int?;
        return (date != null && !date.isAfter(DateTime(today.year, today.month, today.day))) ||
            (km != null && currentKm != null && km <= currentKm);
      }).length;
      return {
        'vehicle_id': vehicleId,
        'ledger_count': ledger.length,
        'verified_record_count': ledger.where((row) => row['source'] == 'partner').length,
        'correction_count': ledger.where((row) => row['corrects'] != null).length,
        'last_maintenance': maintenance.isEmpty ? null : maintenance.first,
        'pending_reminder_count': reminders.length,
        'overdue_reminder_count': overdue,
        'next_due_date': dueDates.isEmpty ? null : dueDates.first,
        'next_due_odometer_km': dueKm.isEmpty ? null : dueKm.first,
      };
    }
    final token = await _storage.read(key: 'access_token');
    final response = await _client.get(_uri('vehicles/$vehicleId/maintenance-summary'), headers: {
      if (token != null) 'Authorization': 'Bearer $token',
    });
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> cancelVehicleTransfer(int vehicleId) async {
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(
      _uri('vehicles/$vehicleId/cancel-transfer'),
      headers: {'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token'},
    );
    if (response.statusCode != 200) throw Exception(_message(response));
  }

  Future<void> updateVehiclePlate(int vehicleId, String plateNumber, String useRelationship) async {
    if (demoMode) {
      final index = _demoVehicles.indexWhere((vehicle) => vehicle['id'] == vehicleId);
      if (index >= 0) {
        _demoVehicles[index]['plate_number'] = plateNumber.trim();
        _demoVehicles[index]['ownership_relationship'] = useRelationship;
      }
      return;
    }
    final token = await _storage.read(key: 'access_token');
    final response = await _client.patch(_uri('vehicles/$vehicleId'), headers: {
      'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token',
    }, body: jsonEncode({'plate_number': plateNumber, 'use_relationship': useRelationship}));
    if (response.statusCode != 200) throw Exception(_message(response));
  }

  Future<Map<String, dynamic>> previewVehicleTransfer(String code) async {
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(
      _uri('vehicles/preview-transfer'),
      headers: {'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token'},
      body: jsonEncode({'code': code.trim().toUpperCase()}),
    );
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> acceptVehicleTransfer(String code, String useRelationship) async {
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(
      _uri('vehicles/accept-transfer'),
      headers: {'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token'},
      body: jsonEncode({'code': code.trim().toUpperCase(), 'use_relationship': useRelationship}),
    );
    if (response.statusCode != 200) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createPartnerVerifiedRecord(Map<String, dynamic> data) async {
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(
      _uri('ledger/partner-verified'),
      headers: {'Content-Type': 'application/json', if (token != null) 'Authorization': 'Bearer $token'},
      body: jsonEncode(data),
    );
    if (response.statusCode != 201) throw Exception(_message(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> completeReminder(int reminderId) async {
    if (demoMode) {
      final index = _demoReminders.indexWhere((reminder) => reminder['id'] == reminderId);
      if (index >= 0) _demoReminders[index]['is_complete'] = true;
      return;
    }
    final token = await _storage.read(key: 'access_token');
    final response = await _client.post(_uri('reminders/$reminderId/complete'), headers: {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    });
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception(_message(response));
  }

  Future<void> registerPushInstallation(String installationId, String platform) async {
    final accessToken = await _storage.read(key: 'access_token');
    final response = await _client.post(_uri('push/devices'), headers: {
      'Content-Type': 'application/json',
      if (accessToken != null) 'Authorization': 'Bearer $accessToken',
    }, body: jsonEncode({'installation_id': installationId, 'platform': platform}));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception(_message(response));
  }

  Future<void> unregisterPushInstallation(String installationId) async {
    final accessToken = await _storage.read(key: 'access_token');
    final response = await _client.delete(_uri('push/devices'), headers: {
      'Content-Type': 'application/json',
      if (accessToken != null) 'Authorization': 'Bearer $accessToken',
    }, body: jsonEncode({'installation_id': installationId}));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception(_message(response));
  }

  String _message(http.Response response) {
    try { return jsonDecode(response.body).toString(); } catch (_) { return '서버 응답 오류 (${response.statusCode})'; }
  }
}

// A single refresh is shared by concurrent requests. Only a rejected refresh
// clears credentials; temporary network failures keep the existing session.
class _SessionClient extends http.BaseClient {
  _SessionClient(this.inner, this.storage, this.onExpired, this.requestTimeout);
  final Duration requestTimeout;
  final http.Client inner;
  final FlutterSecureStorage storage;
  final VoidCallback onExpired;
  Future<bool>? refreshing;

  Future<bool> refresh() async {
    final pending = refreshing;
    if (pending != null) return pending;
    final task = _refresh();
    refreshing = task;
    try { return await task; } finally { refreshing = null; }
  }

  Future<bool> _refresh() async {
    final token = await storage.read(key: 'refresh_token');
    if (token == null) { await expire(); return false; }
    final request = http.Request('POST', Uri.parse('${ApiClient._baseUrl}/auth/token/refresh/'))
      ..headers['Content-Type'] = 'application/json'
      ..body = jsonEncode({'refresh': token})
      ..followRedirects = false;
    final response = await inner.send(request).then(http.Response.fromStream)
        .timeout(requestTimeout);
    if (await storage.read(key: 'refresh_token') != token) return false;
    if (response.statusCode == 400 || response.statusCode == 401) {
      await expire(); return false;
    }
    if (response.statusCode != 200) throw Exception('로그인 갱신을 잠시 후 다시 시도해 주세요.');
    // Do not restore a session that was logged out while refresh was in flight.
    if (await storage.read(key: 'refresh_token') != token) return false;
    final data = jsonDecode(response.body);
    await storage.write(key: 'access_token', value: data['access'] as String);
    if (data['refresh'] != null) await storage.write(key: 'refresh_token', value: data['refresh'] as String);
    return true;
  }

  Future<void> expire() async {
    await storage.delete(key: 'access_token');
    await storage.delete(key: 'refresh_token');
    onExpired();
  }

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    if (request is! http.Request) throw UnsupportedError('Unsupported request body');
    final base = Uri.parse(ApiClient._baseUrl);
    if (request.url.origin != base.origin || !request.url.path.startsWith('${base.path}/')) {
      throw Exception('허용되지 않은 API 주소입니다.');
    }
    final isAuth = request.url.path.contains('/auth/');
    final isPublic = {'${base.path}/partners/', '${base.path}/notices/', '${base.path}/offers/', '${base.path}/cafe/search/'}.contains(request.url.path) && request.method == 'GET';
    final token = isAuth || isPublic ? null : await storage.read(key: 'access_token');
    Future<http.Response> attempt(String? access) async {
      final copy = http.Request(request.method, request.url)
        ..headers.addAll(request.headers)
        ..bodyBytes = request.bodyBytes
        ..followRedirects = false;
      copy.headers.remove('Authorization');
      if (access != null) copy.headers['Authorization'] = 'Bearer $access';
      return await inner.send(copy).then(http.Response.fromStream)
          .timeout(requestTimeout);
    }
    var response = await attempt(token);
    if (!isAuth && token != null && response.statusCode == 401) {
      final current = await storage.read(key: 'access_token');
      if ((current != null && current != token) || await refresh()) {
        response = await attempt(await storage.read(key: 'access_token'));
        if (response.statusCode == 401) await expire();
      }
    }
    return http.StreamedResponse(Stream.value(response.bodyBytes), response.statusCode,
      headers: response.headers, reasonPhrase: response.reasonPhrase, request: request);
  }
  @override
  void close() => inner.close();
}
