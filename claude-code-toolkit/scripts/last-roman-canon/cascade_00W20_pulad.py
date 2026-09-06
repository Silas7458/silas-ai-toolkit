# -*- coding: utf-8 -*-
# cascade_00W20_pulad.py - S#328 (6 Sept 2026, later): PULAD named first everywhere the steel is stated - the Persian
# crucible steel, the pulad version of crucible wootz (the author's word); wootz demoted to the Western name for the class.
#   python cascade_00W20_pulad.py dry | all
import sys, os, io, json, re, importlib.util
spec = importlib.util.spec_from_file_location("w2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cascade_00W2.py"))
src = open(spec.origin, encoding="utf-8").read().split("# ------------------------------------------------------------------ ids")[0]
ns = {}; exec(compile(src, spec.origin, "exec"), ns)
replace_all = ns["replace_all"]; find = ns["find"]; TOTAL = ns["TOTAL"]; EM = ns["EM"]; LQ = ns["LQ"]; RQQ = ns["RQQ"]; RQ = ns["RQ"]; SEC = ns["SEC"]
mirror_text = ns["mirror_text"]

MARDIN = "1PRYYFAD6ewSUKsYzljP8G6LYJ10vcYwhDPunG0XRq9o"
W00 = "1PW6x_Yx4jBuALpjIJquDGeSyP6NOVqRG4eBV-xnPkEI"
BIBLE = "1SaArCJb2HbI8baLQNE2EA3prThQyZUkAjLCkd1EowqM"

def bump_dated(doc_id, note):
    t = mirror_text(doc_id); best = None
    for line in t.split("\n"):
        m = re.match(r"^v(\d+)\.(\d+)\b", line)
        if m:
            key = (int(m.group(1)), int(m.group(2)))
            if best is None or key > best[0]: best = (key, line)
    (maj, mi), line = best
    anchor = line.rstrip("\r")
    if t.count(anchor) != 1: anchor = anchor[:120]
    return (anchor, "v%d.%d %s 6 Sept 2026 %s %s\n" % (maj, mi + 1, EM, EM, note) + anchor)

PULAD = "PULAD " + EM + " the Persian crucible steel, the pulad version of crucible wootz (the class the West calls wootz; the Persian and Khorasan workshops made it their own ways, by co-fusion at Merv and by carburizing at Chahak; the precise Persian term for the watered kind is pulad-e jowhardar) " + EM

replace_all(W00, [
    ("it is made of crucible pulad " + EM + " wootz steel " + EM + " with the watered pattern of the reference image he supplied",
     "it is made of " + PULAD + " with the watered pattern (jowhar) of the reference image he supplied"),
    ("STRAIGHT, double-edged, crucible pulad (wootz) steel, a spear point;", "STRAIGHT, double-edged, pulad crucible steel, a spear point;"),
    (LQ + "pattern-welded" + RQQ + " is retired for HIS blade (it is crucible steel " + EM + " the Weyland spatha is the pattern-welded one);",
     LQ + "pattern-welded" + RQQ + " is retired for HIS blade (it is pulad, crucible steel cast in one ingot " + EM + " the Weyland spatha is the pattern-welded one); the pulad / wootz distinction was researched the same afternoon and is written into the object Doc (pulad = the Persian word and the Persian co-fusion tradition; wootz = the Western name for the Indian ingot and the class; jowhar = the watered pattern; a late-Sasanian crucible-steel sword in the British Museum is the historical footing);"),
], "00W")

replace_all(MARDIN, [
    ("a long STRAIGHT double-edged blade of crucible pulad (wootz) steel with a watered figure (never pattern-welded, never a twisted core)",
     "a long STRAIGHT double-edged blade of PULAD " + EM + " Persian crucible steel, the pulad version of crucible wootz " + EM + " with a watered jowhar figure (cast in one ingot; never pattern-welded, never a twisted core)"),
    ("crucible pulad " + EM + " wootz steel " + EM + " with the watered pattern of the reference image in this folder.",
     "pulad, Persian crucible steel (the pulad version of crucible wootz " + EM + " R-178), with the watered pattern of the reference image in this folder."),
    ("the watered crucible-wootz figure of his blade (00W R-178)", "the watered pulad (Persian crucible steel) figure of his blade (00W R-178)"),
    bump_dated(MARDIN, "pulad named first wherever the steel is stated (the author" + RQ + "s word; the pulad / wootz distinction researched and written into the object Doc)."),
], "MARDIN CHARACTER FILE")

replace_all(find("00T "), [("a 33-in crucible-wootz blade, no cross-guard", "a 33-in pulad (Persian crucible steel) blade, no cross-guard")], "00T R-151 exception")
replace_all(find("VISUAL REFERENCE INDEX"), [("33-in crucible-wootz blade, no cross-guard", "33-in pulad (Persian crucible steel) blade, no cross-guard")], "VISUAL REFERENCE INDEX #4")
replace_all(BIBLE, [("a 33-in crucible-wootz blade, no cross-guard", "a 33-in pulad (Persian crucible steel) blade, no cross-guard")], "CHARACTER BIBLE")

print("TOTAL pairs=%d changed=%d zeros=%d" % (TOTAL["pairs"], TOTAL["changed"], len(TOTAL["zeros"])))
for z in TOTAL["zeros"]:
    print("  ", z)
