import Vision
import AppKit
for path in CommandLine.arguments.dropFirst() {
  let img = NSImage(contentsOfFile: path)!
  var r = CGRect(origin: .zero, size: img.size)
  let cg = img.cgImage(forProposedRect: &r, context: nil, hints: nil)!
  let req = VNRecognizeTextRequest()
  req.recognitionLevel = .accurate
  req.recognitionLanguages = ["ko-KR","en-US"]
  req.usesLanguageCorrection = false
  try! VNImageRequestHandler(cgImage: cg).perform([req])
  var out = ""
  for o in (req.results ?? []) {
    let b = o.boundingBox
    let t = (o.topCandidates(1).first?.string ?? "").replacingOccurrences(of: "\t", with: " ")
    out += String(format: "%.4f\t%.4f\t%.4f\t%.4f\t", b.minX, 1-b.maxY, b.maxX, 1-b.minY) + t + "\n"
  }
  try! out.write(toFile: path.replacingOccurrences(of: ".png", with: ".tsv"), atomically: true, encoding: .utf8)
}
