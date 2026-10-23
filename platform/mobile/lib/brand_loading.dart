import 'dart:math' as math;
import 'package:flutter/material.dart';

/// A bounded, motion-aware loader without a spinning progress wheel.
class MiniDriveLoader extends StatefulWidget {
  const MiniDriveLoader(
      {this.label = '잠시만 기다려 주세요', this.compact = false, super.key});
  final String label;
  final bool compact;
  @override
  State<MiniDriveLoader> createState() => _MiniDriveLoaderState();
}

class _MiniDriveLoaderState extends State<MiniDriveLoader>
    with SingleTickerProviderStateMixin {
  late final AnimationController controller = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1600));
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.of(context).disableAnimations) {
      controller.stop();
    } else {
      controller.repeat();
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.compact) {
      return Semantics(
        liveRegion: true,
        label: widget.label,
        child: SizedBox(
          width: 48,
          height: 42,
          child: AnimatedBuilder(
            animation: controller,
            builder: (context, _) => Transform.translate(
              offset: Offset(0, math.sin(controller.value * math.pi * 4) * 2),
              child: const Icon(Icons.directions_car_rounded,
                  size: 30, color: Color(0xffbd2434)),
            ),
          ),
        ),
      );
    }
    return Semantics(
        liveRegion: true,
        label: widget.label,
        child: SizedBox(
            width: 230,
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              AnimatedBuilder(
                  animation: controller,
                  builder: (context, _) => SizedBox(
                      height: 96,
                      child: Stack(alignment: Alignment.center, children: [
                        Container(
                            width: 86,
                            height: 86,
                            decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: const LinearGradient(colors: [
                                  Color(0xffbd2434),
                                  Color(0xff761428)
                                ]))),
                        Transform.translate(
                            offset: Offset(0,
                                math.sin(controller.value * math.pi * 4) * 2),
                            child: const Icon(Icons.directions_car_rounded,
                                size: 52, color: Colors.white)),
                        Positioned(
                            bottom: 8,
                            child: SizedBox(
                                width: 92,
                                height: 3,
                                child: ClipRect(
                                    child: CustomPaint(
                                        painter: _RoadPainter(controller.value),
                                        size: const Size(92, 3))))),
                      ]))),
              const SizedBox(height: 10),
              const Text('ILOVEMINI',
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 2)),
              const SizedBox(height: 8),
              Text(widget.label,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12)),
            ])));
  }
}

class _RoadPainter extends CustomPainter {
  _RoadPainter(this.progress);
  final double progress;
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = Colors.white.withValues(alpha: .65);
    for (int i = -1; i < 5; i++) {
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 28 - progress * 28, 0, 16, 3),
              const Radius.circular(2)),
          paint);
    }
  }

  @override
  bool shouldRepaint(_RoadPainter oldDelegate) =>
      oldDelegate.progress != progress;
}

class BrandBusyOverlay extends StatelessWidget {
  const BrandBusyOverlay(
      {required this.busy,
      required this.child,
      this.label = '잠시만 기다려 주세요',
      super.key});
  final bool busy;
  final Widget child;
  final String label;
  @override
  Widget build(BuildContext context) => Stack(children: [
        child,
        if (busy) ...[
          const Positioned.fill(
              child:
                  ModalBarrier(dismissible: false, color: Color(0x88000000))),
          Positioned.fill(
              child: Center(
                  child: Card(
                      child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: MiniDriveLoader(label: label))))),
        ],
      ]);
}
