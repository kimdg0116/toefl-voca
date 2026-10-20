// 토플 단어.app — 폰 앱(GitHub Pages)을 그대로 여는 맥 앱. 창 한 개, Dock 을 다시 누르면 있던 창이 앞으로 온다.
// 진도는 폰과 '기기 연동'(sync/Code.js)으로 맞춘다. 단어 파일·연결 코드는 make_app.sh 가 앱 안(Resources)에 넣어 두고,
// 이 맥의 웹 저장소에 없을 때만 넣는다 (교재 단어는 인터넷에 올리지 않는다)
import Cocoa
import WebKit

let HOME_URL = URL(string: "https://kimdg0116.github.io/toefl-voca/")!

class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate {
    var window: NSWindow!
    var web: WKWebView!
    var saved: URL?

    func applicationDidFinishLaunching(_ n: Notification) {
        buildMenu()
        let cfg = WKWebViewConfiguration()
        cfg.mediaTypesRequiringUserActionForPlayback = []                // 카드가 넘어갈 때 발음 자동 재생
        cfg.userContentController.addUserScript(WKUserScript(source: seedScript(), injectionTime: .atDocumentStart, forMainFrameOnly: true))
        web = WKWebView(frame: .zero, configuration: cfg)
        web.navigationDelegate = self
        web.uiDelegate = self
        web.pageZoom = CGFloat(UserDefaults.standard.object(forKey: "zoom") as? Double ?? 1)
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 500, height: 820),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false  // 닫은 창을 Dock에서 다시 열 때 재사용
        window.title = "TOEFL VOCA"
        window.minSize = NSSize(width: 360, height: 520)
        window.contentView = web
        window.center()
        window.setFrameAutosaveName("main")
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        web.load(URLRequest(url: HOME_URL))
    }

    func seedScript() -> String {
        var js = ""
        if let u = Bundle.main.url(forResource: "toefl-words", withExtension: "json"), let s = try? String(contentsOf: u, encoding: .utf8) {
            js += "if (!(localStorage.getItem('tv.words') || '').startsWith('[')) { const j = \(s); localStorage.setItem('tv.words', JSON.stringify(Array.isArray(j) ? j : j.words)); }\n"
        }
        if let u = Bundle.main.url(forResource: "sync-code", withExtension: "txt"),
           let c = try? String(contentsOf: u, encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines), !c.isEmpty {
            js += "if (!localStorage.getItem('tv.sync')) localStorage.setItem('tv.sync', JSON.stringify({ code: '\(c)', rev: '', dirty: false }));\n"
        }
        return "try {\n\(js)} catch (e) {}"
    }

    // Dock 을 누르면: 창이 닫혀 있으면 다시 보이고, 있으면 앞으로
    func applicationShouldHandleReopen(_ s: NSApplication, hasVisibleWindows f: Bool) -> Bool {
        window.makeKeyAndOrderFront(nil)
        return true
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { false }

    // 진도 백업 내보내기 = 다운로드 폴더에 저장하고 Finder 로 보여 준다
    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        decisionHandler(a.shouldPerformDownload ? .download : .allow)
    }
    func webView(_ w: WKWebView, navigationAction a: WKNavigationAction, didBecome d: WKDownload) { d.delegate = self }
    func download(_ d: WKDownload, decideDestinationUsing r: URLResponse, suggestedFilename name: String, completionHandler: @escaping (URL?) -> Void) {
        let u = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask)[0].appendingPathComponent(name)
        try? FileManager.default.removeItem(at: u)
        saved = u
        completionHandler(u)
    }
    func downloadDidFinish(_ d: WKDownload) { if let u = saved { NSWorkspace.shared.activateFileViewerSelecting([u]) } }

    // 파일 고르기 (단어·음성·백업 불러오기)
    func webView(_ w: WKWebView, runOpenPanelWith p: WKOpenPanelParameters, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let o = NSOpenPanel()
        o.allowsMultipleSelection = p.allowsMultipleSelection
        o.beginSheetModal(for: window) { r in completionHandler(r == .OK ? o.urls : nil) }
    }

    // 자바스크립트 alert / confirm / prompt (연결 코드 입력)
    func webView(_ w: WKWebView, runJavaScriptAlertPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let a = NSAlert(); a.messageText = m; a.addButton(withTitle: "확인")
        a.beginSheetModal(for: window) { _ in completionHandler() }
    }
    func webView(_ w: WKWebView, runJavaScriptConfirmPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let a = NSAlert(); a.messageText = m; a.addButton(withTitle: "확인"); a.addButton(withTitle: "취소")
        a.beginSheetModal(for: window) { r in completionHandler(r == .alertFirstButtonReturn) }
    }
    func webView(_ w: WKWebView, runJavaScriptTextInputPanelWithPrompt p: String, defaultText d: String?, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
        let a = NSAlert(); a.messageText = p; a.addButton(withTitle: "확인"); a.addButton(withTitle: "취소")
        let t = NSTextField(frame: NSRect(x: 0, y: 0, width: 220, height: 24)); t.stringValue = d ?? ""
        a.accessoryView = t; a.window.initialFirstResponder = t
        a.beginSheetModal(for: window) { r in completionHandler(r == .alertFirstButtonReturn ? t.stringValue : nil) }
    }

    @objc func reload() { web.reload() }
    @objc func zoomIn() { setZoom(web.pageZoom + 0.1) }
    @objc func zoomOut() { setZoom(web.pageZoom - 0.1) }
    @objc func zoomReset() { setZoom(1) }
    func setZoom(_ z: CGFloat) {
        web.pageZoom = min(2, max(0.6, (z * 10).rounded() / 10))
        UserDefaults.standard.set(Double(web.pageZoom), forKey: "zoom")
    }

    // 메뉴가 있어야 ⌘C·⌘V·⌘Q 같은 단축키가 먹는다
    func buildMenu() {
        let main = NSMenu()
        func sub(_ title: String, _ items: [NSMenuItem]) {
            let m = NSMenu(title: title); items.forEach { m.addItem($0) }
            let i = NSMenuItem(); i.submenu = m; main.addItem(i)
        }
        func item(_ t: String, _ s: Selector?, _ k: String, _ mods: NSEvent.ModifierFlags = .command) -> NSMenuItem {
            let i = NSMenuItem(title: t, action: s, keyEquivalent: k); i.keyEquivalentModifierMask = mods; return i
        }
        func mine(_ t: String, _ s: Selector, _ k: String) -> NSMenuItem { let i = item(t, s, k); i.target = self; return i }
        sub("토플 단어", [item("토플 단어 가리기", #selector(NSApplication.hide(_:)), "h"), .separator(),
                         item("토플 단어 종료", #selector(NSApplication.terminate(_:)), "q")])
        sub("편집", [item("실행 취소", Selector(("undo:")), "z"), item("실행 복귀", Selector(("redo:")), "z", [.command, .shift]), .separator(),
                    item("오려두기", #selector(NSText.cut(_:)), "x"), item("복사하기", #selector(NSText.copy(_:)), "c"),
                    item("붙여넣기", #selector(NSText.paste(_:)), "v"), item("전체 선택", #selector(NSText.selectAll(_:)), "a")])
        sub("보기", [mine("새로고침", #selector(reload), "r"), .separator(),
                    mine("크게", #selector(zoomIn), "="), mine("작게", #selector(zoomOut), "-"), mine("원래 크기", #selector(zoomReset), "0")])
        sub("윈도우", [item("최소화", #selector(NSWindow.miniaturize(_:)), "m"), item("닫기", #selector(NSWindow.performClose(_:)), "w")])
        NSApp.mainMenu = main
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
// NSApplication.delegate는 앱 대표 객체의 수명을 보장하지 않는다. 이벤트 루프가 끝날 때까지 유지한다.
withExtendedLifetime(delegate) { app.run() }
