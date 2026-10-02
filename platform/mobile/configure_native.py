from pathlib import Path
import plistlib
import xml.etree.ElementTree as ET
p = Path('ios/Runner/Info.plist')
with p.open('rb') as f: data = plistlib.load(f)
data['NSCameraUsageDescription'] = '차량 QR 코드를 스캔하기 위해 카메라를 사용합니다.'
data['NSFaceIDUsageDescription'] = '아이러브미니 앱에서 QR을 안전하게 표시하기 위해 Face ID를 사용합니다.'
types = data.setdefault('CFBundleURLTypes', [])
if not any('ilovemini' in t.get('CFBundleURLSchemes', []) for t in types):
    types.append({'CFBundleURLName': 'ILOVEMINI 로그인', 'CFBundleURLSchemes': ['ilovemini']})
with p.open('wb') as f: plistlib.dump(data, f)
ns = 'http://schemas.android.com/apk/res/android'
ET.register_namespace('android', ns)
p = Path('android/app/src/main/AndroidManifest.xml')
tree = ET.parse(p); root = tree.getroot()
for permission in ['android.permission.INTERNET', 'android.permission.CAMERA', 'android.permission.USE_BIOMETRIC']:
    if not any(e.get('{'+ns+'}name') == permission for e in root.findall('uses-permission')):
        ET.SubElement(root, 'uses-permission', {'{'+ns+'}name': permission})
activity = root.find('application/activity')
if activity is None: raise RuntimeError('MainActivity를 찾을 수 없습니다.')
if not any(e.get('{'+ns+'}scheme') == 'ilovemini' for e in activity.findall('intent-filter/data')):
    intent = ET.SubElement(activity, 'intent-filter')
    ET.SubElement(intent, 'action', {'{'+ns+'}name': 'android.intent.action.VIEW'})
    for category in ['DEFAULT', 'BROWSABLE']:
        ET.SubElement(intent, 'category', {'{'+ns+'}name': 'android.intent.category.'+category})
    ET.SubElement(intent, 'data', {'{'+ns+'}scheme': 'ilovemini', '{'+ns+'}host': 'auth'})
tree.write(p, encoding='utf-8', xml_declaration=True)

# local_auth uses FragmentActivity on Android.
for p in Path('android/app/src/main').rglob('MainActivity.kt'):
    source = p.read_text()
    source = source.replace('import io.flutter.embedding.android.FlutterActivity',
                            'import io.flutter.embedding.android.FlutterFragmentActivity')
    source = source.replace(': FlutterActivity()', ': FlutterFragmentActivity()')
    p.write_text(source)
for p in Path('android/app/src/main').rglob('MainActivity.java'):
    source = p.read_text()
    source = source.replace('import io.flutter.embedding.android.FlutterActivity;',
                            'import io.flutter.embedding.android.FlutterFragmentActivity;')
    source = source.replace('extends FlutterActivity', 'extends FlutterFragmentActivity')
    p.write_text(source)

# local_auth needs an AppCompat launch theme on older Android releases.
for p in Path('android/app/src/main/res').rglob('styles.xml'):
    tree = ET.parse(p)
    changed = False
    for style in tree.getroot().findall('style'):
        if style.get('name') == 'LaunchTheme':
            style.set('parent', 'Theme.AppCompat.DayNight')
            changed = True
    if changed:
        tree.write(p, encoding='utf-8', xml_declaration=True)
