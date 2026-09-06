# -*- coding: utf-8 -*-
"""push_doc_text.py - replace a Google Doc's whole body with a marked-up text file (S#327, 5 Sept 2026).

Markup (one paragraph per line):
  "# text"   -> HEADING_1        "## text" -> HEADING_2        **bold** spans anywhere
Everything else -> NORMAL_TEXT. Blank lines become empty paragraphs.

Usage:  python push_doc_text.py DOC_ID FILE [--live]
Without --live it only parses, prints the plan (paragraph/heading/bold counts, chunk sizes) and exits.
With --live: delete body -> insert text in ~6K UTF-16 chunks (reverse order, always at index 1) -> reset styles
-> apply headings and bold -> re-fetch the doc and diff its text against the file (exit 1 on any mismatch).
"""
import io, json, os, re, subprocess, sys

NODE = "node"
RUNGWS = r"C:\Users\silas\AppData\Roaming\npm\node_modules\@googleworkspace\cli\run-gws.js"
CHUNK = 6000  # UTF-16 code units per insertText

def u16(s):
    return len(s.encode("utf-16-le")) // 2

def gws(args, body=None):
    cmd = [NODE, RUNGWS] + args
    if body is not None:
        cmd += ["--json", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("gws FAILED:", " ".join(args[:3]), "\n", r.stderr[-2000:])
        sys.exit(2)
    return r.stdout

def parse(path):
    lines = io.open(path, encoding="utf-8").read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    paras = []  # (plain, style, [(bold_start, bold_end) relative])
    for ln in lines:
        style = "NORMAL_TEXT"
        if ln.startswith("## "):
            style, ln = "HEADING_2", ln[3:]
        elif ln.startswith("# "):
            style, ln = "HEADING_1", ln[2:]
        spans, out, pos = [], "", 0
        for m in re.finditer(r"\*\*(.+?)\*\*", ln):
            out += ln[pos:m.start()]
            s = u16(out)
            out += m.group(1)
            spans.append((s, u16(out)))
            pos = m.end()
        out += ln[pos:]
        if "**" in out:
            print("WARN stray ** in:", out[:80])
        paras.append((out, style, spans))
    return paras

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    doc_id, path = sys.argv[1], sys.argv[2]
    live = "--live" in sys.argv
    paras = parse(path)
    text = "\n".join(p[0] for p in paras)
    # chunks on paragraph boundaries
    chunks, cur = [], ""
    for i, (p, _, _) in enumerate(paras):
        piece = p + ("\n" if i < len(paras) - 1 else "")
        if cur and u16(cur) + u16(piece) > CHUNK:
            chunks.append(cur); cur = ""
        cur += piece
    if cur:
        chunks.append(cur)
    assert "".join(chunks) == text
    heads = [(i, s) for i, (_, s, _) in enumerate(paras) if s != "NORMAL_TEXT"]
    nbold = sum(len(sp) for _, _, sp in paras)
    print("paragraphs=%d  headings=%d  bold spans=%d  chunks=%d (%s utf16)  total=%d utf16" % (
        len(paras), len(heads), nbold, len(chunks), "/".join(str(u16(c)) for c in chunks), u16(text)))
    for i, s in heads:
        print("  ", s, repr(paras[i][0][:60]))
    if not live:
        print("DRY - nothing pushed"); return
    # 1. delete the body
    doc = json.loads(gws(["docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}), "--format", "json"]))
    end = doc["body"]["content"][-1]["endIndex"]
    if end - 1 > 1:
        gws(["docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id})],
            {"requests": [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}}]})
    print("deleted 1..%d" % (end - 1))
    # 2. insert chunks, last first, always at index 1
    for n, c in enumerate(reversed(chunks)):
        gws(["docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id})],
            {"requests": [{"insertText": {"location": {"index": 1}, "text": c}}]})
        print("inserted chunk %d/%d (%d)" % (n + 1, len(chunks), u16(c)))
    # 3. styles
    total = u16(text)
    reqs = [
        {"updateParagraphStyle": {"range": {"startIndex": 1, "endIndex": 1 + total}, "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"}, "fields": "namedStyleType"}},
        {"updateTextStyle": {"range": {"startIndex": 1, "endIndex": 1 + total}, "textStyle": {"bold": False}, "fields": "bold"}},
    ]
    off = 1
    for i, (p, style, spans) in enumerate(paras):
        L = u16(p)
        if style != "NORMAL_TEXT":
            reqs.append({"updateParagraphStyle": {"range": {"startIndex": off, "endIndex": off + L + (1 if i < len(paras) - 1 else 0)}, "paragraphStyle": {"namedStyleType": style}, "fields": "namedStyleType"}})
        for a, b in spans:
            reqs.append({"updateTextStyle": {"range": {"startIndex": off + a, "endIndex": off + b}, "textStyle": {"bold": True}, "fields": "bold"}})
        off += L + 1
    gws(["docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id})], {"requests": reqs})
    print("styled: %d requests" % len(reqs))
    # 4. verify
    doc = json.loads(gws(["docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}), "--format", "json"]))
    got, styles, bolds = [], [], 0
    for el in doc["body"]["content"]:
        pg = el.get("paragraph")
        if not pg:
            continue
        t = "".join(e.get("textRun", {}).get("content", "") for e in pg.get("elements", []))
        got.append(t.rstrip("\n"))
        styles.append(pg.get("paragraphStyle", {}).get("namedStyleType"))
        bolds += sum(1 for e in pg.get("elements", []) if e.get("textRun", {}).get("textStyle", {}).get("bold") and e["textRun"].get("content", "").strip())
    want = [p[0] for p in paras]
    ok = got == want
    if not ok:
        print("TEXT MISMATCH: doc has %d paragraphs, file %d" % (len(got), len(want)))
        for i, (g, w) in enumerate(zip(got, want)):
            if g != w:
                print("  first diff at paragraph %d:\n   DOC : %r\n   FILE: %r" % (i, g[:120], w[:120])); break
    sok = all(styles[i] == paras[i][1] for i in range(min(len(styles), len(paras))))
    print("VERIFY text=%s styles=%s bold-runs=%d (spans wanted %d)" % ("OK" if ok else "FAIL", "OK" if sok else "FAIL", bolds, nbold))
    sys.exit(0 if ok and sok else 1)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
