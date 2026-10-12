import AppKit
let sc = NSSpellChecker.shared
sc.setLanguage("en_US")
while let line = readLine() {
  let r = sc.checkSpelling(of: line, startingAt: 0)
  if r.location != NSNotFound { print(line) }
}
