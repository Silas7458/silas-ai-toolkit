# -*- coding: utf-8 -*-
# cascade_00W18_sword_straight.py - S#328 (6 Sept 2026): Mardin's Sasanian sword is STRAIGHT (the author's "long Persian
# sword"; his reference images). "curved Sasanian sword" retired from every live season document; the Mardin CHARACTER
# FILE s9 object paragraph replaced by the full spec pointer; the "small flat gold guard" wording harmonized to the ruled
# "no cross-guard"; s11 logs the new spec Doc; 00W gains the record + the open LENGTH item for the author.
#   python cascade_00W18_sword_straight.py dry | all
import sys, os, io, json, re, importlib.util
spec = importlib.util.spec_from_file_location("w2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cascade_00W2.py"))
src = open(spec.origin, encoding="utf-8").read().split("# ------------------------------------------------------------------ ids")[0]
ns = {}; exec(compile(src, spec.origin, "exec"), ns)
replace_all = ns["replace_all"]; find = ns["find"]; TOTAL = ns["TOTAL"]; EM = ns["EM"]; LQ = ns["LQ"]; RQQ = ns["RQQ"]; RQ = ns["RQ"]; SEC = ns["SEC"]
mirror_text = ns["mirror_text"]

D6 = "6 September 2026"; D6s = "6 Sept 2026"
MARDIN = "1PRYYFAD6ewSUKsYzljP8G6LYJ10vcYwhDPunG0XRq9o"
W00 = "1PW6x_Yx4jBuALpjIJquDGeSyP6NOVqRG4eBV-xnPkEI"
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

CURVED_NOTE = "the sword is STRAIGHT " + EM + " " + LQ + "curved" + RQQ + " retired (the author" + RQ + "s long Persian sword; his reference images; see MARDIN" + RQ + "S SASANIAN SWORD " + EM + " THE OBJECT in his folder)"

# ---- the season documents: one "curved" each (two in the S1 State and the S1 Summary)
S1M = find("SEASON ONE " + EM + " THE SANCTUARY " + EM + " MASTER")
replace_all(S1M, [
    ("the curved Sasanian sword (the only Dragon with no spatha) doing quick surgical work", "the straight Sasanian sword (the only Dragon with no spatha) doing quick surgical work"),
    ("Version 3.9 " + EM + " 5 September 2026, night " + "·", "Version 3.10 " + EM + " " + D6 + " " + "·" + " " + CURVED_NOTE + " (110 Act Two). Prior: Version 3.9 " + EM + " 5 September 2026, night " + "·"),
], "S1 MASTER")
S1S = find("SEASON ONE " + EM + " STATE OF THE SEASON")
replace_all(S1S, [
    ("carries the curved Sasanian sword, the only Dragon without a spatha", "carries the straight Sasanian sword, the only Dragon without a spatha"),
    ("the curved Sasanian sword (the only Dragon with no spatha), staff-hand controlling distance", "the straight Sasanian sword (the only Dragon with no spatha), staff-hand controlling distance"),
    ("Version 5.7 " + EM + " 5 September 2026, night " + "·", "Version 5.8 " + EM + " " + D6 + " " + "·" + " " + CURVED_NOTE + " (roster + 110 Act Two). Prior: Version 5.7 " + EM + " 5 September 2026, night " + "·"),
], "S1 STATE")
S1F = find("SEASON ONE " + EM + " THE SANCTUARY " + EM + " FULL SEASON SUMMARY")
replace_all(S1F, [
    ("who keeps the curved Sasanian sword he carried out of Persia", "who keeps the straight Sasanian sword he carried out of Persia"),
    ("the curved Sasanian sword doing quick surgical work", "the straight Sasanian sword doing quick surgical work"),
    ("Version 3.1 " + EM + " 5 September 2026, night", "Version 3.2 " + EM + " " + D6 + " (" + CURVED_NOTE + ", 102 and 110). Prior: Version 3.1 " + EM + " 5 September 2026, night"),
], "S1 SUMMARY")
S2S = find("SEASON TWO " + EM + " STATE OF THE SEASON")
replace_all(S2S, [
    ("braced, riding from this season, the curved Sasanian sword;", "braced, riding from this season, the straight Sasanian sword;"),
    ("Version 2.14 " + EM + " 5 September 2026 " + "·", "Version 2.15 " + EM + " " + D6 + " " + "·" + " " + CURVED_NOTE + " (" + SEC + "3A). Prior: Version 2.14 " + EM + " 5 September 2026 " + "·"),
], "S2 STATE")
S3S = find("SEASON THREE " + EM + " STATE OF THE SEASON")
replace_all(S3S, [
    ("the staff, the brace, the curved sword.", "the staff, the brace, the straight Sasanian sword."),
    ("Version 2.6 " + EM + " 25 August 2026 " + "·", "Version 2.7 " + EM + " " + D6 + " " + "·" + " " + CURVED_NOTE + " (" + SEC + "4A). Prior: Version 2.6 " + EM + " 25 August 2026 " + "·"),
], "S3 STATE")

# ---- the Mardin CHARACTER FILE
OBJ_OLD = ("THE SASANIAN SWORD " + EM + " THE OBJECT [A " + EM + " image, 2 Sept 2026; logged in " + SEC + "11]: " + LQ + "Mardin Sassanian sword unsheathed" + RQQ + " / " + LQ + "sheathed" + RQQ + " and " + LQ + "Mardin Sasanian Sword handle only" + RQQ + " (31 Aug, the museum photograph the hilt is drawn from): a long straight double-edged blade, pattern-welded; NO cross-guard " + EM + " a straight hilt of gold scale-work in three bands over dark grip sections, a scale-work pommel cap; a GREEN scabbard with gold scale-work throat, mid-band and chape, two suspension loops. It hangs at his LEFT hip from the belt (" + SEC + "8). This is the eastern blade the Index audited (#4) given its object; the Weyland spatha question below stands as the author left it.")
OBJ_NEW = ("THE SASANIAN SWORD " + EM + " THE OBJECT [A " + EM + " image, 2 Sept 2026; logged in " + SEC + "11; THE FULL SPEC IS THE DOC " + LQ + SPEC_TITLE + RQQ + " IN THIS FOLDER (" + D6s + "), which governs every render, prompt, storyboard, caption and scene of the sword]: " + LQ + "Mardin Sassanian sword unsheathed" + RQQ + " / " + LQ + "sheathed" + RQQ + " and " + LQ + "Mardin Sasanian Sword handle only" + RQQ + " (31 Aug, the museum photograph the hilt is drawn from): a long STRAIGHT double-edged blade, pattern-welded, a faint median line, a spear point " + EM + " never curved; NO cross-guard " + EM + " only a flat gold collar at the blade" + RQ + "s shoulder; a straight hilt of gold scale-work in three bands over dark ribbed grip sections and a scale-work pommel cap; a GREEN scabbard with gold scale-work throat, mid-band and chape and two P-shaped suspension mounts (two loops). It hangs at his LEFT hip from the sun-disc belt on two slings (" + SEC + "8), the bowcase at the right; when drawn the scabbard hangs EMPTY " + EM + " never a second sword. LENGTH: NOT RULED " + EM + " no blade or overall length exists in the corpus; the 33 inches of 00T R-151 is the Weyland spatha" + RQ + "s, not his (open for the author, 00W). This is the eastern blade the Index audited (#4) given its object; his only sword, pilot to Badon (00W R-174).")
replace_all(MARDIN, [
    (OBJ_OLD, OBJ_NEW),
    ("HIS SASANIAN SWORD raised (the gold scale grip and small flat gold guard of " + LQ + "Mardin Sassanian sword unsheathed" + RQQ + ";", "HIS SASANIAN SWORD raised (the gold scale-work hilt with no cross-guard of " + LQ + "Mardin Sassanian sword unsheathed" + RQQ + ";"),
    ("the gold scale grip, the small flat gold guard, the green scabbard with the gold locket and P-mounts", "the gold scale-work hilt with no cross-guard, the green scabbard with the gold locket and P-mounts"),
    ("Carried braced into S3 (\"the staff, the brace, the curved sword\" " + EM + " S3 State " + SEC + "4A). [A] [H " + EM + " a straggler for the author, one word: Sasanian cavalry swords were STRAIGHT (the long sword of the CHARACTER HISTORY); the corpus's \"curved\" is a later-period image. Unruled; left as written.]",
     "Carried braced into S3 (" + LQ + "the staff, the brace, the straight Sasanian sword" + RQQ + " " + EM + " S3 State " + SEC + "4A). [A] [The one-word " + LQ + "curved" + RQQ + " straggler (S1 Master, S1 State, S1 Summary, S2 State, S3 State; flagged 28 Aug) was retired " + D6s + " (S#328): the blade is STRAIGHT " + EM + " the author" + RQ + "s long Persian sword and his reference images; the object spec Doc in this folder governs.]"),
    ("* RENAMED 2 Sept 2026: " + LQ + "mardin-sword-FINAL.jpg" + RQQ,
     "* " + LQ + SPEC_TITLE + RQQ + " (Doc, this folder, " + D6s + "): the single object authority for his sword " + EM + " blade, hilt, scabbard, how it hangs, the rules, the open LENGTH item " + EM + " read before any render, prompt or scene. [A/C]\n* RENAMED 2 Sept 2026: " + LQ + "mardin-sword-FINAL.jpg" + RQQ),
    bump_dated(MARDIN, "S#328 (later): THE SASANIAN SWORD object spec written out in full as the Doc " + LQ + SPEC_TITLE + RQQ + " in this folder; " + SEC + "9 object paragraph points to it (straight, no cross-guard, gold scale-work, green scabbard, empty when drawn, LENGTH not ruled); " + LQ + "small flat gold guard" + RQQ + " wording of v2.7 harmonized to the ruled " + LQ + "no cross-guard" + RQQ + "; the " + LQ + "curved" + RQQ + " straggler retired here and in five season docs."),
], "MARDIN CHARACTER FILE")

# ---- 00W record + the open item for the author
REC = ("MARDIN" + RQ + "S SASANIAN SWORD " + EM + " THE OBJECT (S#328, " + D6s + ", on the author" + RQ + "s instruction that the description of this sword is never again lost or misread). A standalone Doc of that title now sits in the Mardin Afzar folder beside the five sword reference images and governs every render, prompt, storyboard, caption and scene of his sword: STRAIGHT, double-edged, pattern-welded, a spear point; NO cross-guard (a flat gold collar only); a gold scale-work hilt in three bands over dark ribbed grip sections with a scale-work pommel cap; a dark green scabbard with gold scale-work throat, mid-band and chape and two P-shaped suspension mounts; LEFT hip on two slings from the sun-disc belt, the bowcase at the right; the scabbard hangs EMPTY when the sword is drawn; ONE sword from 101 to Badon, never a Weyland spatha (00T R-155 amended; 00W R-174). Also " + D6s + ": the character file" + RQ + "s " + LQ + "spatha raised / non-canon on the sword" + RQQ + " reading of his renders was a Brother misreading and is corrected (every picture shows this sword); " + LQ + "curved Sasanian sword" + RQQ + " retired from the S1 Master, S1 State, S1 Summary, S2 State and S3 State (the author" + RQ + "s " + LQ + "long Persian sword" + RQQ + "; the blade in his references is straight). OPEN FOR THE AUTHOR [?]: THE SWORD" + RQ + "S LENGTH " + EM + " no blade length or overall length for it exists anywhere in the corpus; the 33 inches of 00T R-151 is the Weyland spatha" + RQ + "s and is not to be borrowed.")
replace_all(W00, [("END OF 00W.", REC + "\nEND OF 00W.")], "00W record")

print("TOTAL pairs=%d changed=%d zeros=%d" % (TOTAL["pairs"], TOTAL["changed"], len(TOTAL["zeros"])))
for z in TOTAL["zeros"]:
    print("  ", z)
