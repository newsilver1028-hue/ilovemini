import 'dart:async';
import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:io';
import 'api_client.dart';
import 'app_refresh.dart';

bool secureLink(String value) {
  final uri = Uri.tryParse(value);
  return uri != null && uri.scheme == 'https' && uri.host.isNotEmpty;
}

const managedAssets = {
  'mini-october': 'assets/images/season/mini-october.png',
  'phone-holder':
      'assets/images/mini-recommended-items/item-01-phone-holder.png',
  'grille-parts':
      'assets/images/mini-recommended-items/item-03-grille-parts.png',
  'shift-knob': 'assets/images/mini-recommended-items/item-04-shift-knob.png',
};
Widget managedImage(Map item, {BoxFit fit = BoxFit.contain}) {
  final url = '${item['image_url'] ?? ''}';
  final asset = managedAssets[item['asset_key']];
  Widget fallback() => asset == null
      ? const Center(child: Icon(Icons.image_outlined, size: 42))
      : Image.asset(asset, fit: fit);
  return secureLink(url)
      ? Image.network(url, fit: fit, errorBuilder: (_, __, ___) => fallback())
      : fallback();
}

class ManagedSeasonLaunch extends StatefulWidget {
  const ManagedSeasonLaunch({required this.home, super.key});
  final Widget home;
  @override
  State<ManagedSeasonLaunch> createState() => _ManagedSeasonLaunchState();
}

class _ManagedSeasonLaunchState extends State<ManagedSeasonLaunch> {
  Map? banner;
  bool done = false;
  Timer? timer;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final data =
          await ApiClient().seasonBanner().timeout(const Duration(seconds: 3));
      if (!mounted) return;
      final next = data['banner'] as Map?;
      if (next == null) {
        setState(() => done = true);
        return;
      }
      setState(() => banner = next);
      final seconds =
          ((next['duration_seconds'] as num?)?.toInt() ?? 2).clamp(1, 5);
      timer = Timer(Duration(seconds: seconds), () {
        if (mounted) setState(() => done = true);
      });
    } catch (_) {
      if (mounted) setState(() => done = true);
    }
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (done) return widget.home;
    return Scaffold(
        body: banner == null
            ? const Center(child: CircularProgressIndicator())
            : Stack(fit: StackFit.expand, children: [
                managedImage(banner!, fit: BoxFit.cover),
                Positioned(
                    right: 12,
                    top: MediaQuery.paddingOf(context).top + 8,
                    child: TextButton(
                        onPressed: () => setState(() => done = true),
                        child: const Text('건너뛰기'))),
              ]));
  }
}

class ManagedBanners extends StatefulWidget {
  const ManagedBanners({required this.api, super.key});
  final ApiClient api;
  @override
  State<ManagedBanners> createState() => _ManagedBannersState();
}

class _ManagedBannersState extends State<ManagedBanners> {
  final controller = PageController();
  Timer? timer;
  int count = 0, page = 0;
  late final content = widget.api.appContent().then((data) {
    count = (data['banners'] as List? ?? []).length;
    return data;
  });
  @override
  void initState() {
    super.initState();
    timer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (mounted &&
          count > 1 &&
          controller.hasClients &&
          !MediaQuery.disableAnimationsOf(context))
        controller.animateToPage((page + 1) % count,
            duration: const Duration(milliseconds: 360),
            curve: Curves.easeOutCubic);
    });
  }

  @override
  void dispose() {
    timer?.cancel();
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
      future: content,
      builder: (context, snapshot) {
        final rows = (snapshot.data?['banners'] as List? ?? [])
            .whereType<Map>()
            .toList();
        if (rows.isEmpty) return const SizedBox.shrink();
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('제휴 배너',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 10),
          AspectRatio(
              aspectRatio: 1,
              child: PageView(
                  controller: controller,
                  onPageChanged: (value) => page = value,
                  children: rows
                      .map((row) => InkWell(
                            onTap: secureLink('${row['action_url'] ?? ''}')
                                ? () => launchUrl(Uri.parse(row['action_url']),
                                    mode: LaunchMode.externalApplication)
                                : null,
                            child: ClipRRect(
                                borderRadius: BorderRadius.circular(14),
                                child: managedImage(row, fit: BoxFit.cover)),
                          ))
                      .toList())),
          if (rows.length > 1)
            Center(child: Text('좌우로 넘겨 보기 · ${rows.length}개')),
        ]);
      });
}

class ManagedNotices extends StatefulWidget {
  const ManagedNotices({required this.api, required this.onOpen, super.key});
  final ApiClient api;
  final ValueChanged<Map<String, dynamic>> onOpen;
  @override
  State<ManagedNotices> createState() => _ManagedNoticesState();
}

class _ManagedNoticesState extends State<ManagedNotices> {
  late final rows = widget.api.list('notices');
  @override
  Widget build(BuildContext context) =>
      FutureBuilder<List<Map<String, dynamic>>>(
          future: rows,
          builder: (context, snapshot) {
            final data = snapshot.data ?? [];
            if (data.isEmpty) return const SizedBox.shrink();
            return Card(
                child: ExpansionTile(
                    initiallyExpanded: true,
                    title: Text('공지사항 · ${data.length}건'),
                    children: data
                        .map((row) => ListTile(
                              leading: Icon(row['is_pinned'] == true
                                  ? Icons.push_pin_outlined
                                  : Icons.campaign_outlined),
                              title: Text('${row['title']}'),
                              subtitle: Text('${row['summary'] ?? ''}',
                                  maxLines: 2, overflow: TextOverflow.ellipsis),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => widget.onOpen(row),
                            ))
                        .toList()));
          });
}

class ManagedUpdateNotice extends StatefulWidget {
  const ManagedUpdateNotice({required this.api, super.key});
  final ApiClient api;
  @override
  State<ManagedUpdateNotice> createState() => _ManagedUpdateNoticeState();
}

class _ManagedUpdateNoticeState extends State<ManagedUpdateNotice> {
  late final future = Future.wait<dynamic>(
      [PackageInfo.fromPlatform(), widget.api.appContent()]);
  @override
  Widget build(BuildContext context) => FutureBuilder<List<dynamic>>(
      future: future,
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const SizedBox.shrink();
        final info = snapshot.data![0] as PackageInfo;
        final content = snapshot.data![1] as Map;
        final platform = Platform.isIOS ? 'ios' : 'android';
        final releases = (content['releases'] as List? ?? [])
            .whereType<Map>()
            .where((row) => row['platform'] == platform);
        final latest = releases.firstOrNull;
        if (latest == null ||
            ((latest['build_number'] as num?)?.toInt() ?? 0) <=
                (int.tryParse(info.buildNumber) ?? 0))
          return const SizedBox.shrink();
        return Card(
            child: ListTile(
                leading: const Icon(Icons.system_update_outlined),
                title: Text('새 버전 ${latest['version']} 안내'),
                subtitle: Text('${latest['notes'] ?? ''}'),
                trailing: const Icon(Icons.open_in_new),
                onTap: secureLink('${latest['download_url'] ?? ''}')
                    ? () => launchUrl(Uri.parse(latest['download_url']),
                        mode: LaunchMode.externalApplication)
                    : null));
      });
}

class PartnerExtraInformation extends StatelessWidget {
  const PartnerExtraInformation({required this.partner, super.key});
  final Map partner;
  @override
  Widget build(BuildContext context) {
    final business = '${partner['business_info'] ?? ''}'.trim();
    final name = '${partner['representative_name'] ?? ''}'.trim();
    final title = '${partner['representative_title'] ?? ''}'.trim();
    final photo = '${partner['representative_photo_url'] ?? ''}';
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      if (business.isNotEmpty)
        Card(
            child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('방문·이용 안내',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text(business)
                    ]))),
      if (name.isNotEmpty)
        Card(
            child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('대표 정비사',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      if (secureLink(photo))
                        SizedBox(
                            height: 150,
                            child: Image.network(photo,
                                fit: BoxFit.contain,
                                errorBuilder: (_, __, ___) =>
                                    const Icon(Icons.person_outline))),
                      Text([
                        name,
                        if (title.isNotEmpty) title,
                        if (partner['representative_experience_years'] != null)
                          '경력 ${partner['representative_experience_years']}년'
                      ].join(' · ')),
                    ]))),
    ]);
  }
}

Future<String?> askBookingCancellationReason(BuildContext context) async {
  return showDialog<String>(
      context: context, builder: (_) => const _CancellationReasonDialog());
}

class _CancellationReasonDialog extends StatefulWidget {
  const _CancellationReasonDialog();
  @override
  State<_CancellationReasonDialog> createState() =>
      _CancellationReasonDialogState();
}

class _CancellationReasonDialogState extends State<_CancellationReasonDialog> {
  final controller = TextEditingController();
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
          title: const Text('예약 취소 사유'),
          content: TextField(
              controller: controller,
              maxLength: 500,
              maxLines: 3,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(labelText: '취소 사유를 입력해 주세요')),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('돌아가기')),
            FilledButton(
                onPressed: controller.text.trim().isEmpty
                    ? null
                    : () => Navigator.pop(context, controller.text.trim()),
                child: const Text('예약 취소'))
          ]);
}

class LivePartnerView extends StatefulWidget {
  const LivePartnerView(
      {required this.api,
      required this.initial,
      required this.builder,
      super.key});
  final ApiClient api;
  final Map<String, dynamic> initial;
  final Widget Function(Map<String, dynamic>) builder;
  @override
  State<LivePartnerView> createState() => _LivePartnerViewState();
}

class _LivePartnerViewState extends State<LivePartnerView> {
  late Map<String, dynamic> partner = widget.initial;
  int revision = -1;
  bool busy = false;
  @override
  void initState() {
    super.initState();
    appSyncChecks.addListener(check);
    reload();
  }

  void check() {
    if (mounted &&
        ModalRoute.of(context)?.isCurrent != false &&
        revision != appDataChanges.value) reload();
  }

  Future<void> reload() async {
    if (busy || widget.initial['id'] == null) return;
    busy = true;
    final requestedRevision = appDataChanges.value;
    try {
      final fresh = await widget.api.getMap('partners/${widget.initial['id']}');
      if (mounted)
        setState(() {
          partner = fresh;
          revision = requestedRevision;
        });
    } catch (_) {
      /* Preserve visible vendor data when connectivity drops. */
    } finally {
      busy = false;
    }
  }

  @override
  void dispose() {
    appSyncChecks.removeListener(check);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.builder(partner);
}

class MemberPointHistoryPage extends StatefulWidget {
  const MemberPointHistoryPage({required this.api, super.key});
  final ApiClient api;
  @override
  State<MemberPointHistoryPage> createState() => _MemberPointHistoryPageState();
}

class _MemberPointHistoryPageState extends State<MemberPointHistoryPage> {
  late Future<List<Map<String, dynamic>>> future =
      widget.api.list('points/history');
  Future<void> reload() async {
    final next = widget.api.list('points/history');
    setState(() => future = next);
    await next;
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('포인트 적립·사용 내역')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
          future: future,
          builder: (context, snapshot) {
            if (snapshot.hasError)
              return Center(
                  child: TextButton(
                      onPressed: reload, child: const Text('다시 불러오기')));
            if (!snapshot.hasData)
              return const Center(child: CircularProgressIndicator());
            final rows = snapshot.data!;
            return RefreshIndicator(
                onRefresh: reload,
                child: ListView(
                    padding: const EdgeInsets.all(16),
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      if (rows.isEmpty)
                        const Padding(
                            padding: EdgeInsets.all(24),
                            child: Text('아직 포인트 거래 내역이 없습니다.')),
                      ...rows.map((row) {
                        final delta =
                            (row['points_delta'] as num?)?.toInt() ?? 0;
                        final date = DateTime.tryParse('${row['created_at']}')
                            ?.toLocal();
                        final dateLabel = date == null
                            ? ''
                            : '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
                        return Card(
                            child: ListTile(
                                title: Text('${row['transaction_label']}'),
                                subtitle: Text([
                                  dateLabel,
                                  '${row['partner_name'] ?? '아이러브미니'}',
                                  '${row['memo'] ?? ''}'
                                ].where((e) => e.isNotEmpty).join('\n')),
                                trailing: Text(
                                    '${delta > 0 ? '+' : ''}$delta P',
                                    style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        color: delta < 0
                                            ? Colors.red
                                            : Colors.green))));
                      }),
                    ]));
          }));
}
