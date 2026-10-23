import 'package:flutter/material.dart';
import 'api_client.dart';

class CafeShoppingPreview extends StatefulWidget {
  const CafeShoppingPreview({required this.api, super.key});
  final ApiClient api;
  @override
  State<CafeShoppingPreview> createState() => _CafeShoppingPreviewState();
}
class _CafeShoppingPreviewState extends State<CafeShoppingPreview> {
  Widget demoImage() => AspectRatio(aspectRatio: 1, child: Image.asset(
    category == 'recommended'
      ? 'assets/images/mini-recommended-items/demo-recommended.jpg'
      : 'assets/images/mini-recommended-items/demo-groupbuy.jpg',
    fit: BoxFit.contain, semanticLabel: '${category == 'recommended' ? '추천아이템' : '공동구매'} 데모 이미지'));
  late final Future<Map<String,dynamic>> content;
  String category='recommended';
  @override
  void initState(){ super.initState(); content=widget.api.appContent(); }
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
    const Divider(),
    Row(children:[const Icon(Icons.shopping_bag_outlined),const SizedBox(width:12),const Expanded(child:Text('추천 아이템 · 공동구매',style:TextStyle(fontWeight:FontWeight.bold))), const Text('업데이트예정')]),
    const SizedBox(height:12),
    Row(children:[for(final entry in {'recommended':'추천아이템','groupbuy':'공동구매'}.entries) Expanded(child:TextButton(onPressed:()=>setState(()=>category=entry.key),child:Text(entry.value,style:TextStyle(fontWeight:category==entry.key?FontWeight.bold:FontWeight.normal))))]),
    FutureBuilder<Map<String,dynamic>>(future:content,builder:(context,snapshot){
      if(snapshot.hasError)return demoImage();
      if(!snapshot.hasData)return const LinearProgressIndicator();
      final items=(snapshot.data!['products'] as List? ?? []).whereType<Map>().where((row)=>(row['category']??'recommended')==category);
      if(items.isEmpty)return demoImage();
      final item=items.first;
      final raw='${item['image_url']??''}';
      final uri=Uri.parse('https://ilovemini.onrender.com/').resolve(raw);
      const assets={'phone-holder':'assets/images/mini-recommended-items/item-01-phone-holder.png','interior-brackets':'assets/images/mini-recommended-items/item-02-interior-brackets.png','grille-parts':'assets/images/mini-recommended-items/item-03-grille-parts.png','shift-knob':'assets/images/mini-recommended-items/item-04-shift-knob.png'};
      Widget fallback()=>assets.containsKey(item['asset_key'])?Image.asset(assets[item['asset_key']]!,fit:BoxFit.contain):const Center(child:Icon(Icons.image_outlined,size:48));
      return AspectRatio(aspectRatio:1,child:raw.isNotEmpty&&uri.scheme=='https'?Image.network(uri.toString(),fit:BoxFit.contain,errorBuilder:(_,__,___)=>fallback()):fallback());
    }),
  ]);
}
