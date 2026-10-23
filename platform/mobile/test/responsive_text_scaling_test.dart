import 'package:flutter/painting.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ilovemini/main.dart';

void main() {
  group('responsiveTextScaleForWidth', () {
    test('adapts typography modestly to logical screen width', () {
      expect(responsiveTextScaleForWidth(320), 0.94);
      expect(responsiveTextScaleForWidth(390), 1);
      expect(responsiveTextScaleForWidth(430), closeTo(1.06, 0.001));
      expect(responsiveTextScaleForWidth(600), 1.06);
    });

    test('uses a neutral scale for invalid widths', () {
      expect(responsiveTextScaleForWidth(0), 1);
      expect(responsiveTextScaleForWidth(double.nan), 1);
    });

    test('device width adjustment preserves accessibility scaling', () {
      final scaler = TextScaler.linear(1.5);
      expect(responsiveTextScalerForWidth(scaler, 320).scale(16), 24);
    });

    test('default text scales with width around a phone-sized baseline', () {
      final scaler = responsiveTextScalerForWidth(TextScaler.noScaling, 320);
      expect(scaler.scale(16), closeTo(15.04, 0.001));
    });
  });
}
