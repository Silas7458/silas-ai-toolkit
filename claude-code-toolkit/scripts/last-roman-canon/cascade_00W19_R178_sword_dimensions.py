# -*- coding: utf-8 -*-
# cascade_00W19_R178_sword_dimensions.py - S#328 (6 Sept 2026, afternoon): the author's ruling on Mardin's Sasanian sword
# - 39 in overall; 33-in blade, 2 in wide, double-edged, very slight taper; 6-in handle + pommel; crucible pulad / wootz
# steel with the supplied watered pattern; scabbard just over 34 in - written as 00W R-178 and cascaded to every object
# site: the Mardin CHARACTER FILE (s9, s11, changelog), 00T R-151's Mardin exception, the VISUAL REFERENCE INDEX #4, the
# CHARACTER BIBLE entry, and the morning's 00W record line ("pattern-welded" -> crucible steel).
#   python cascade_00W19_R178_sword_dimensions.py dry | all
import sys, os, io, json, re, importlib.util
spec = importlib.util.spec_from_file_location("w2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cascade_00W2.py"))
src = open(spec.origin, encoding="utf-8").read().split("# ------------------------------------------------------------------ ids")[0]
ns = {}; exec(compile(src, spec.origin, "exec"), ns)
replace_all = ns["replace_all"]; find = ns["find"]; TOTAL = ns["TOTAL"]; EM = ns["EM"]; LQ = ns["LQ"]; RQQ = ns["RQQ"]; RQ = ns["RQ"]; SEC = ns["SEC"]
mirror_text = ns["mirror_text"]

D6s = "6 Sept 2026"
MARDIN = "1PRYYFAD6ewSUKsYzljP8G6LYJ10vcYwhDPunG0XRq9o"
W00 = "1PW6x_Yx4jBuALpjIJquDGeSyP6NOVqRG4eBV-xnPkEI"
BIBLE = "1SaArCJb2HbI8baLQNE2EA3prThQyZUkAjLCkd1EowqM"
PATTERN_IMG = "MARDIN " + EM + " the blade steel " + EM + " pulad-wootz crucible pattern reference (author, 6 Sept 2026).webp"
SPEC_TITLE = "MARDIN" + RQ + "S SASANIAN SWORD " + EM + " THE OBJECT"

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
    return (anchor, "v%d.%d %s %s %s %s\n" % (maj, mi + 1, EM, D6s, EM, note) + anchor)

R178 = ("R-178 " + EM + " MARDIN" + RQ + "S SASANIAN SWORD " + EM + " DIMENSIONS AND STEEL. [A " + EM + " 6 Sept 2026, afternoon]\n"
"Author, in his own numbers: the sword" + RQ + "s total length is 39 inches; the blade is 33 inches; the handle and pommel are 6 inches together; the blade is 2 inches wide, double-edged, with a very slight taper to the point; it is made of crucible pulad " + EM + " wootz steel " + EM + " with the watered pattern of the reference image he supplied (" + LQ + PATTERN_IMG + RQQ + ", in his folder: tight flowing bands curling into whorls and eyes, ladder-like ripples where the bands stack, no straight lines); the scabbard is just over 34 inches, to cover and protect the blade. He re-supplied the three sword references (sheathed, unsheathed, handle only) " + EM + " byte-identical to the copies in his folder. CONSEQUENCES: the blade length equals the Weyland spatha" + RQ + "s 33 inches (00T R-151) by ruling, not by borrowing " + EM + " the two swords are told apart by the hilt (no cross-guard; gold scale-work), the steel (a crucible wootz figure, never a twisted core in a fuller) and the green scabbard, never by length; the morning" + RQ + "s open item (" + LQ + "LENGTH not ruled" + RQQ + ") is CLOSED; " + LQ + "pattern-welded" + RQQ + " is retired for HIS blade (it is crucible steel " + EM + " the Weyland spatha is the pattern-welded one); the object Doc " + LQ + SPEC_TITLE + RQQ + " in his folder and the character file " + SEC + "9 carry the numbers. AUTHOR" + RQ + "S STANDING INSTRUCTION, recorded: every render, prompt, storyboard, caption or scene of this sword is built from the object Doc and the reference images, never from memory " + EM + " no reader of the series is ever to be unclear about his sword.")

replace_all(W00, [
    ("END OF 00W.", R178 + "\nEND OF 00W."),
    ("STRAIGHT, double-edged, pattern-welded, a spear point; NO cross-guard (a flat gold collar only);", "STRAIGHT, double-edged, crucible pulad (wootz) steel, a spear point; NO cross-guard (a flat gold collar only);"),
    ("OPEN FOR THE AUTHOR [?]: THE SWORD" + RQ + "S LENGTH " + EM + " no blade length or overall length for it exists anywhere in the corpus; the 33 inches of 00T R-151 is the Weyland spatha" + RQ + "s and is not to be borrowed.",
     "[The length item was CLOSED the same afternoon by R-178 below: 39 inches overall, a 33-inch blade.]"),
], "00W")

replace_all(MARDIN, [
    ("a long STRAIGHT double-edged blade, pattern-welded, a faint median line, a spear point " + EM + " never curved;",
     "a long STRAIGHT double-edged blade of crucible pulad (wootz) steel with a watered figure (never pattern-welded, never a twisted core), a raised median ridge, a spear point " + EM + " never curved;"),
    ("LENGTH: NOT RULED " + EM + " no blade or overall length exists in the corpus; the 33 inches of 00T R-151 is the Weyland spatha" + RQ + "s, not his (open for the author, 00W).",
     "DIMENSIONS AND STEEL (00W R-178, " + D6s + "): 39 inches overall; a 33-inch blade, 2 inches wide, double-edged with a very slight taper; a 6-inch handle and pommel; a scabbard just over 34 inches; crucible pulad " + EM + " wootz steel " + EM + " with the watered pattern of the reference image in this folder. The blade length equals the Weyland spatha" + RQ + "s by ruling; the two are told apart by hilt, guard, steel and scabbard, never by length."),
    ("the single object authority for his sword " + EM + " blade, hilt, scabbard, how it hangs, the rules, the open LENGTH item " + EM + " read before any render, prompt or scene. [A/C]",
     "the single object authority for his sword " + EM + " blade, hilt, scabbard, how it hangs, the rules, the ruled dimensions and steel (00W R-178) " + EM + " read before any render, prompt or scene. [A/C]\n" + LQ + PATTERN_IMG + RQQ + " (this folder, author, " + D6s + ") " + EM + " the watered crucible-wootz figure of his blade (00W R-178): whorls and contour-bands, ladder ripples, no straight lines, no twisted core. [A " + EM + " image]"),
    bump_dated(MARDIN, "00W R-178 (the author, S#328 afternoon): the sword" + RQ + "s dimensions and steel " + EM + " 39 in overall, 33-in blade 2 in wide with a very slight taper, 6-in handle + pommel, scabbard just over 34 in, crucible pulad / wootz with the supplied watered pattern " + EM + " in " + SEC + "9; the pattern reference logged in " + SEC + "11; " + LQ + "pattern-welded" + RQQ + " retired for his blade."),
], "MARDIN CHARACTER FILE")

replace_all(find("00T "), [
    ("[and except MARDIN, who carries his own Sasanian sword and no Weyland spatha " + EM + " 00W R-174, 5 Sept 2026]",
     "[and except MARDIN, who carries his own Sasanian sword and no Weyland spatha " + EM + " 00W R-174, 5 Sept 2026; its object " + EM + " 39 in overall, a 33-in crucible-wootz blade, no cross-guard, green scabbard " + EM + " is 00W R-178, 6 Sept 2026, and the spec Doc in his folder]"),
], "00T R-151 exception")

replace_all(find("VISUAL REFERENCE INDEX"), [
    ("Mardin AFZAR; period-perfect. [pre-18-July; content-vetted]",
     "Mardin AFZAR; period-perfect. [pre-18-July; content-vetted] [THE OBJECT, 6 Sept 2026: the Doc " + LQ + SPEC_TITLE + RQQ + " in his folder " + EM + " 00W R-178: 39 in overall, 33-in crucible-wootz blade, no cross-guard, green scabbard just over 34 in]"),
], "VISUAL REFERENCE INDEX #4")

replace_all(BIBLE, [
    ("carries his OWN Sasanian sword, no Weyland spatha, and holds the GREEN seat from 108 (00W R-174);",
     "carries his OWN Sasanian sword (39 in overall, a 33-in crucible-wootz blade, no cross-guard, green scabbard " + EM + " the object Doc in his folder, 00W R-178), no Weyland spatha, and holds the GREEN seat from 108 (00W R-174);"),
    ("Version 0.8 " + EM + " 6 September 2026 " + EM + " the Weyland entry re-hilts the memorial",
     "Version 0.9 " + EM + " 6 September 2026, later " + EM + " Mardin" + RQ + "s sword object (00W R-178) in his entry. Prior: Version 0.8 " + EM + " 6 September 2026 " + EM + " the Weyland entry re-hilts the memorial"),
], "CHARACTER BIBLE")

print("TOTAL pairs=%d changed=%d zeros=%d" % (TOTAL["pairs"], TOTAL["changed"], len(TOTAL["zeros"])))
for z in TOTAL["zeros"]:
    print("  ", z)
