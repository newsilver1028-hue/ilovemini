import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/painting.dart';
import 'api_client.dart';

final appDataChanges = ValueNotifier<int>(0);
final appSyncChecks = ValueNotifier<int>(0);

class AppRefreshController {
  AppRefreshController(this.api, this.onChange, this.onTick);
  final ApiClient api;
  final VoidCallback onChange;
  final VoidCallback onTick;
  Timer? _timer;
  int _epoch = 0;
  bool _running = false;
  String? _revision;
  String? _publicRevision;
  int _interval = 15;
  void start() {
    stop();
    _running = true;
    final epoch = _epoch;
    check(epoch);
  }

  void stop() {
    _running = false;
    _epoch++;
    _timer?.cancel();
    _timer = null;
  }

  Future<void> check(int epoch) async {
    try {
      final data = await api.syncStatus();
      if (!_running || epoch != _epoch) return;
      final config = data['configuration'] as Map? ?? {};
      _interval = ((config['refresh_interval_seconds'] as num?)?.toInt() ?? 15)
          .clamp(10, 120);
      final revision = '${data['public_revision']}-${data['member_revision']}';
      final publicRevision = '${data['public_revision']}';
      if (_publicRevision != publicRevision) {
        _publicRevision = publicRevision;
        PaintingBinding.instance.imageCache.clear();
        PaintingBinding.instance.imageCache.clearLiveImages();
      }
      if (revision != _revision) {
        _revision = revision;
        appDataChanges.value++;
        onChange();
      }
      appSyncChecks.value++;
    } catch (_) {
      /* Keep current data during temporary network failures. */
    } finally {
      if (_running && epoch == _epoch) {
        onTick();
        _timer = Timer(Duration(seconds: _interval), () => check(epoch));
      }
    }
  }
}
