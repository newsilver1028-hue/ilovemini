import 'package:flutter/material.dart';
import 'api_client.dart';

class MaintenanceRequests extends StatefulWidget {
  const MaintenanceRequests({required this.api, super.key});
  final ApiClient api;
  @override
  State<MaintenanceRequests> createState() => _MaintenanceRequestsState();
}

class _MaintenanceRequestsState extends State<MaintenanceRequests> {
  late Future<List<List<Map<String, dynamic>>>> requests;
  bool busy = false;
  @override
  void initState() { super.initState(); reload(); }
  void reload() {
    requests = Future.wait([widget.api.list('maintenance-recommendations'), widget.api.list('service-estimates')]);
  }
  Future<void> respond(String resource, int id, String decision) async {
    final confirmed = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: Text(decision == 'accepted' ? '내용을 확인하고 동의할까요?' : '거절할까요?'),
      content: Text(resource == 'service-estimates' ? '표시된 견적 항목과 총액을 확인해 주세요. 동의 이력이 업체에 전달됩니다.' : '수락하면 권장 날짜 또는 주행거리로 정비 알림이 등록됩니다.'),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('돌아가기')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('확인'))],
    ));
    if (confirmed != true || !mounted) return;
    setState(() => busy = true);
    try {
      await widget.api.create('$resource/$id/respond', {'decision': decision});
      if (mounted) setState(reload);
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
    } finally { if (mounted) setState(() => busy = false); }
  }
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Row(children: [const Expanded(child: Text('정비 안내 · 견적', style: TextStyle(fontWeight: FontWeight.bold))), IconButton(onPressed: busy ? null : () => setState(reload), tooltip: '새로고침', icon: const Icon(Icons.refresh))]),
    FutureBuilder<List<List<Map<String, dynamic>>>>(future: requests, builder: (context, snapshot) {
      if (snapshot.hasError) return const Text('정비 안내를 불러오지 못했습니다. 새로고침해 주세요.');
      if (!snapshot.hasData) return const LinearProgressIndicator();
      final recommendations = snapshot.data![0];
      final estimates = snapshot.data![1];
      if (recommendations.isEmpty && estimates.isEmpty) return const Text('받은 교체 권장이나 견적이 없습니다.');
      return Column(children: [
        for (final row in recommendations) ListTile(contentPadding: EdgeInsets.zero, title: Text('${row['title']}'), subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${row['due_date'] ?? '날짜 미지정'} · ${row['due_odometer_km'] ?? '-'}km'),
          if (row['status'] == 'pending') Row(children: [TextButton(onPressed: busy ? null : () => respond('maintenance-recommendations', row['id'], 'accepted'), child: const Text('알림 등록')), TextButton(onPressed: busy ? null : () => respond('maintenance-recommendations', row['id'], 'declined'), child: const Text('거절'))]) else Text(row['status'] == 'accepted' ? '알림 등록 완료' : '거절됨'),
        ])),
        for (final row in estimates) ExpansionTile(tilePadding: EdgeInsets.zero, title: Text('견적 ${row['revision']}차 · ${row['total_krw']}원'), subtitle: Text({'sent':'동의 대기','accepted':'동의 완료','declined':'거절됨','superseded':'새 견적으로 대체','draft':'작성 중'}[row['status']] ?? ''), children: [
          for (final item in (row['items'] as List)) ListTile(title: Text('${item['title']}'), trailing: Text('${item['amount_krw']}원')),
          if ('${row['note']}'.isNotEmpty) Text('${row['note']}'),
          if (row['status'] == 'sent') Row(children: [TextButton(onPressed: busy ? null : () => respond('service-estimates', row['id'], 'accepted'), child: const Text('견적 동의')), TextButton(onPressed: busy ? null : () => respond('service-estimates', row['id'], 'declined'), child: const Text('거절'))]),
        ]),
      ]);
    }),
  ])));
}
