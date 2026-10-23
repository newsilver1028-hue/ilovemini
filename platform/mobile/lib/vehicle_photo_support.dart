import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:webview_flutter/webview_flutter.dart';

class VehiclePhotoStorage {
  static String _fileName(String plate) =>
      '${base64Url.encode(utf8.encode(plate.trim())).replaceAll('=', '')}.webp';

  static Future<File?> forPlate(String? plate) async {
    if (plate == null || plate.trim().isEmpty) return null;
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/vehicle_photos/${_fileName(plate)}');
    return await file.exists() ? file : null;
  }

  static Future<void> saveForPlate(String plate, Uint8List bytes) async {
    final directory = await getApplicationDocumentsDirectory();
    final photos = Directory('${directory.path}/vehicle_photos');
    await photos.create(recursive: true);
    await File('${photos.path}/${_fileName(plate)}')
        .writeAsBytes(bytes, flush: true);
  }
}

Future<Uint8List?> removeVehiclePhotoBackground(
        BuildContext context, Uint8List imageBytes) =>
    showDialog<Uint8List>(
      context: context,
      barrierDismissible: false,
      builder: (_) => _VehiclePhotoCutoutDialog(imageBytes: imageBytes),
    );

class _VehiclePhotoCutoutDialog extends StatefulWidget {
  const _VehiclePhotoCutoutDialog({required this.imageBytes});
  final Uint8List imageBytes;

  @override
  State<_VehiclePhotoCutoutDialog> createState() =>
      _VehiclePhotoCutoutDialogState();
}

class _VehiclePhotoCutoutDialogState extends State<_VehiclePhotoCutoutDialog> {
  late final WebViewController _controller;
  Timer? _timeout;
  String _status = '배경 제거 기능을 준비하고 있어요. 첫 실행은 모델 다운로드로 시간이 걸릴 수 있습니다.';
  String? _error;
  bool _started = false;

  static const _html =
      r'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script>
window.cutoutReady = new Promise((resolve,reject)=>{window.resolveCutout=resolve;window.rejectCutout=reject;});
window.startVehicleCutout = async function(encoded){
 try {
  const engine=await window.cutoutReady;
  VehicleCutout.postMessage('차량 배경을 분석하고 있어요…');
  const binary=atob(encoded), bytes=new Uint8Array(binary.length);
  for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
  const file=new File([bytes],'vehicle.jpg',{type:'image/jpeg'});
  const result=await engine.remove(file,{session:engine.session,postProcessMask:true,onProgress:(info)=>VehicleCutout.postMessage(info.message||('배경 제거 중 '+Math.round(info.progress||0)+'%'))});
  const bitmap=await createImageBitmap(result);
  const canvas=document.createElement('canvas');canvas.width=bitmap.width;canvas.height=bitmap.height;
  const ctx=canvas.getContext('2d');ctx.drawImage(bitmap,0,0);bitmap.close();
  const output=await new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('이미지를 저장하지 못했습니다.')),'image/webp',0.86));
  const data=new Uint8Array(await output.arrayBuffer());let out='';
  for(let i=0;i<data.length;i+=0x8000)out+=String.fromCharCode(...data.subarray(i,Math.min(i+0x8000,data.length)));
  VehicleCutout.postMessage('RESULT:'+btoa(out));
 } catch(e) {VehicleCutout.postMessage('ERROR:'+(e&&e.message?e.message:'배경 제거에 실패했습니다.'));}
};
</script><script type="module">
try {
 const ort=await import('https://esm.sh/onnxruntime-web@1.23.0?bundle');
 ort.env.wasm.wasmPaths='https://cdn.jsdelivr.net/npm/onnxruntime-web@1.23.0/dist/';
 const {remove,newSession,rembgConfig}=await import('https://esm.sh/@bunnio/rembg-web@1.0.2?bundle&external=onnxruntime-web');
 rembgConfig.setBaseUrl('https://huggingface.co/bunnio/dis_anime/resolve/main');
 const session=await newSession('silueta');window.resolveCutout({remove,session});
} catch(e) {window.rejectCutout(new Error('누끼 모듈 로딩 실패: '+(e&&e.message?e.message:String(e))));}
</script></head><body></body></html>''';

  @override
  void initState() {
    super.initState();
    _timeout = Timer(const Duration(seconds: 120), () {
      if (mounted && _error == null) {
        setState(() => _error = '처리가 지연되고 있어요. 원본 사진을 저장할 수 있습니다.');
      }
    });
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..addJavaScriptChannel('VehicleCutout', onMessageReceived: (message) {
        final text = message.message;
        if (text.startsWith('RESULT:')) {
          _timeout?.cancel();
          final output = base64Decode(text.substring(7));
          if (mounted) Navigator.of(context).pop(Uint8List.fromList(output));
        } else if (text.startsWith('ERROR:')) {
          _timeout?.cancel();
          if (mounted) setState(() => _error = text.substring(6));
        } else if (mounted) {
          setState(() => _status = text);
        }
      })
      ..setNavigationDelegate(NavigationDelegate(onPageFinished: (_) {
        if (_started) return;
        _started = true;
        final encoded = base64Encode(widget.imageBytes);
        _controller.runJavaScript('window.startVehicleCutout("$encoded")');
      }))
      ..loadHtmlString(_html);
  }

  @override
  void dispose() {
    _timeout?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: const Text('차량 사진 배경 제거'),
        content: SizedBox(
          width: 280,
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            if (_error == null) ...[
              const SizedBox(height: 4),
              const CircularProgressIndicator(),
              const SizedBox(height: 18),
              Text(_status, textAlign: TextAlign.center),
              const SizedBox(height: 6),
              const Text('사진은 이 기기에서 처리됩니다.',
                  style: TextStyle(fontSize: 12), textAlign: TextAlign.center),
              SizedBox(
                height: 2,
                width: 2,
                child: WebViewWidget(controller: _controller),
              ),
            ] else ...[
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 8),
              const Text('원본 사진을 그대로 저장할 수 있습니다.',
                  style: TextStyle(fontSize: 12), textAlign: TextAlign.center),
            ],
          ]),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(_error == null ? '취소' : '원본 사용')),
        ],
      );
}
