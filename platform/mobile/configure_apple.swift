import Foundation

// Persist restored Apple Sign In/APNs capabilities without rewriting the Xcode project.
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
for path in ["ios/Runner/Assets.xcassets", "ios/Runner/Base.lproj/LaunchScreen.storyboard", "android/app/src/main/res"] {
    let archived = root.appendingPathComponent("native_resources/" + path)
    let destination = root.appendingPathComponent(path)
    if FileManager.default.fileExists(atPath: archived.path) {
        if FileManager.default.fileExists(atPath: destination.path) { try FileManager.default.removeItem(at: destination) }
        try FileManager.default.copyItem(at: archived, to: destination)
    }
}
let entitlements: [String: Any] = [
    "com.apple.developer.applesignin": ["Default"],
    "aps-environment": "development"
]
let data = try PropertyListSerialization.data(fromPropertyList: entitlements, format: .xml, options: 0)
try data.write(to: root.appendingPathComponent("ios/Runner/Runner.entitlements"))
for name in ["Debug", "Release"] {
    let file = root.appendingPathComponent("ios/Flutter/\(name).xcconfig")
    var content = try String(contentsOf: file, encoding: .utf8)
    let setting = "CODE_SIGN_ENTITLEMENTS = Runner/Runner.entitlements"
    if !content.contains(setting) {
        content += "\n\(setting)\n"
        try content.write(to: file, atomically: true, encoding: .utf8)
    }
}
