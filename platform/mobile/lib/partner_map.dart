import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

class PartnerMap extends StatefulWidget {
  const PartnerMap({required this.query, this.interactive = false, super.key});
  final String query;
  final bool interactive;
  @override
  State<PartnerMap> createState() => _PartnerMapState();
}

class _PartnerMapState extends State<PartnerMap> {
  WebViewController? controller;
  bool loading = true;
  bool failed = false;
  Uri get uri => Uri.https('www.google.com', '/maps', {'q': widget.query, 'output': 'embed'});
  void loadMap() {
    final src = const HtmlEscape().convert(uri.toString());
    controller?.loadHtmlString('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0"><iframe title="Google 업체 지도" src="$src" style="border:0;width:100vw;height:100vh" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe></body></html>');
  }
  @override
  void initState() {
    super.initState();
    if (!kIsWeb && WebViewPlatform.instance != null) {
      controller = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..setNavigationDelegate(NavigationDelegate(
          onPageStarted: (_) { if (mounted) setState(() { loading = true; failed = false; }); },
          onPageFinished: (_) { if (mounted) setState(() => loading = false); },
          onWebResourceError: (error) {
            if (mounted && error.isForMainFrame == true) setState(() { failed = true; loading = false; });
          },
        ))
        ;
      loadMap();
    }
  }
  @override
  void didUpdateWidget(covariant PartnerMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.query != widget.query) loadMap();
  }
  @override
  Widget build(BuildContext context) => Card(
    clipBehavior: Clip.antiAlias,
    child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Padding(padding: const EdgeInsets.all(12), child: Text(widget.query, style: const TextStyle(fontWeight: FontWeight.w700))),
      SizedBox(height: widget.interactive ? MediaQuery.sizeOf(context).height * .65 : 260, child: controller == null
        ? const Center(child: Text('Google 지도는 iOS·Android 앱에서 표시됩니다.'))
        : Stack(children: [
            Positioned.fill(child: IgnorePointer(
              ignoring: !widget.interactive,
              child: WebViewWidget(controller: controller!),
            )),
            if (!widget.interactive) const Positioned(
              left: 10, right: 10, bottom: 10,
              child: IgnorePointer(child: DecoratedBox(
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.all(Radius.circular(8))),
                child: Padding(padding: EdgeInsets.all(8), child: Text('지도 위에서도 위아래로 스크롤하세요', textAlign: TextAlign.center, style: TextStyle(color: Colors.black87, fontSize: 12))),
              )),
            ),
            if (loading) const Align(alignment: Alignment.topCenter, child: LinearProgressIndicator()),
            if (failed) ColoredBox(color: Theme.of(context).colorScheme.surface, child: Center(child: TextButton(
              onPressed: loadMap, child: const Text('지도를 불러오지 못했습니다. 다시 시도')))),
          ])),
      if (!widget.interactive) Padding(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
        child: OutlinedButton.icon(
          icon: const Icon(Icons.fullscreen), label: const Text('지도 확대·이동'),
          onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => Scaffold(
            appBar: AppBar(title: Text(widget.query)),
            body: SafeArea(child: ListView(padding: const EdgeInsets.all(12), children: [PartnerMap(query: widget.query, interactive: true)])),
          ))),
        ),
      ),
      TextButton.icon(onPressed: () async {
        final target = Uri.https('www.google.com', '/maps/search/', {'api': '1', 'query': widget.query});
        try {
          if (!await launchUrl(target, mode: LaunchMode.externalApplication)) throw Exception();
        } catch (_) {
          if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('지도를 열지 못했습니다.')));
        }
      }, icon: const Icon(Icons.open_in_new), label: const Text('지도보기')),
    ]),
  );
}
