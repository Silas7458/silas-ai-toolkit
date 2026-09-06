# -*- coding: utf-8 -*-
# cascade_00W17_mardin_sword.py - S#328 (6 Sept 2026): the MARDIN CHARACTER FILE called the raised sword in the 1 Sept
# moorland shots and the standing shot a "spatha" (entered with the 00T cascade on 2 Sept; re-bracketed NON-CANON under
# R-174 on 5 Sept without anyone re-reading the image). Read against the sword folder on 6 Sept: every Mardin picture
# shows HIS SASANIAN SWORD (gold scale grip, small flat gold guard, green scabbard with gold locket / P-mounts / chape),
# the scabbard hanging EMPTY when the sword is drawn. The pictures are canon on the sword; the text was wrong.
# Also corrects two stale file names in s11 to the names in the folder.
#   python cascade_00W17_mardin_sword.py dry | all
import sys, os, io, json, importlib.util
spec = importlib.util.spec_from_file_location("w2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cascade_00W2.py"))
src = open(spec.origin, encoding="utf-8").read().split("# ------------------------------------------------------------------ ids")[0]
ns = {}; exec(compile(src, spec.origin, "exec"), ns)
replace_all = ns["replace_all"]; TOTAL = ns["TOTAL"]; EM = ns["EM"]; LQ = ns["LQ"]; RQQ = ns["RQQ"]; RQ = ns["RQ"]; SEC = ns["SEC"]
mirror_text = ns["mirror_text"]

MARDIN = "1PRYYFAD6ewSUKsYzljP8G6LYJ10vcYwhDPunG0XRq9o"
D6 = "6 Sept 2026"

def bump_pair_dated(doc_id, note):
    """Prepend a new changelog line above the current top version line, dated 6 Sept (the helper's bump_pair is hard-wired to 5 Sept)."""
    import re
    t = mirror_text(doc_id)
    best = None
    for line in t.split("\n"):
        m = re.match(r"^v(\d+)\.(\d+)\b", line)
        if m:
            key = (int(m.group(1)), int(m.group(2)))
            if best is None or key > best[0]:
                best = (key, line)
    (maj, mi), line = best
    anchor = line.rstrip("\r")
    if t.count(anchor) != 1:
        anchor = anchor[:120]
    new = "v%d.%d %s %s %s %s\n" % (maj, mi + 1, EM, D6, EM, note)
    return (anchor, new + anchor)

NC = " [NON-CANON on the sword " + EM + " 00W R-174: his sword is the Sasanian one; no Weyland spatha]"
SAS = "HIS SASANIAN SWORD raised (the gold scale grip and small flat gold guard of " + LQ + "Mardin Sassanian sword unsheathed" + RQQ + "; the green scabbard with its gold locket hangs empty at the hip)"

replace_all(MARDIN, [
    # s8 - the standing shot and the moorland set
    ("bow and quiver at the hip, the spatha raised" + NC + ", white trousers",
     "bow and quiver at the hip, " + SAS + ", white trousers"),
    ("(" + LQ + "mardin-gallop-uk-c2-FINAL" + RQQ + " with the bow drawn, " + LQ + "mardin riding with-sword-FINAL" + RQQ + ", " + LQ + "mardin-arch2-FINAL" + RQQ + " with two riders behind, " + LQ + "mardin-solo-c2-1" + RQQ + " and " + LQ + "mardin-solo2-c2-1-handle-only-removed" + RQQ + ")",
     "(" + LQ + "mardin-gallop-uk-c2-FINAL" + RQQ + " with the bow drawn and the sword sheathed, " + LQ + "mardin riding with-sword-FINAL" + RQQ + " with the Sasanian sword raised, " + LQ + "mardin-arch2-FINAL" + RQQ + " with the Sasanian sword across the saddle and two riders behind, " + LQ + "mardin-on horse solo-sword in" + RQQ + " and " + LQ + "mardin-solo on horse handle-only-removed" + RQQ + " on the black " + EM + " the sword sheathed in the first, the Sasanian sword raised in the second)"),
    # s9 - the sword paragraph
    ("The 1 Sept moorland shots that show a spatha raised are look references for the man and NON-CANON on the sword; his sword folder is the authority. [Was: R-151 puts the standard Weyland spatha in every rider" + RQ + "s hand but Ambrosius" + RQ + "s " + EM + " his included " + EM + " and the 1 Sept shots show it raised (bone grip, redwood pommel).]",
     "Every 1 Sept moorland shot and the standing shot show HIS SASANIAN SWORD " + EM + " the gold scale grip, the small flat gold guard, the green scabbard with the gold locket and P-mounts (his sword folder: " + LQ + "Mardin Sassanian sword unsheathed / sheathed / handle only" + RQQ + ") " + EM + " so the pictures are CANON on the sword; the sword folder is the authority. [Record, corrected " + D6 + " (S#328): an earlier note in this file called the raised blade a Weyland spatha " + LQ + "(bone grip, redwood pommel)" + RQQ + " and, under R-174, marked the shots NON-CANON on the sword " + EM + " that was a misreading of the images (entered with the 00T cascade 2 Sept, re-bracketed 5 Sept), never the author" + RQ + "s ruling; no render needs redoing for the sword. Was, before that: R-151 puts the standard Weyland spatha in every rider" + RQ + "s hand but Ambrosius" + RQ + "s " + EM + " his included.]"),
    # s11 - the image log
    (LQ + "mardin-sword-FINAL.jpg" + RQQ + " (the gallop, spatha raised" + NC + ")",
     LQ + "mardin riding with-sword-FINAL.jpg" + RQQ + " (the gallop, his Sasanian sword raised, the green scabbard empty at the hip)"),
    (LQ + "mardin-arch2-FINAL.jpg" + RQQ + " (standing horse, two riders with dracos behind), " + LQ + "mardin-solo-c2-1.jpg" + RQQ + " and " + LQ + "mardin-solo2-c2-1-handle-only-removed.png" + RQQ + " (solo on the black, at rest and with the spatha raised " + EM + " the second carries one disclosed surgical edit, a phantom belt-grip removed)",
     LQ + "mardin-arch2-FINAL.jpg" + RQQ + " (standing horse, the Sasanian sword drawn across the saddle, two riders with dracos behind), " + LQ + "mardin-on horse solo-sword in.jpg" + RQQ + " and " + LQ + "mardin-solo on horse handle-only-removed.png" + RQQ + " (solo on the black " + EM + " the Sasanian sword sheathed in the first, raised in the second, the green scabbard empty at the hip; the second carries one disclosed surgical edit, a phantom belt-grip removed)"),
    ("bow and quiver, spatha raised" + NC + ". Read in " + SEC + "8. [A]",
     "bow and quiver, his Sasanian sword raised, the green scabbard empty at the hip " + EM + " CANON on the sword (read against the sword folder " + D6 + "). Read in " + SEC + "8. [A]"),
    # changelog
    bump_pair_dated(MARDIN, "S#328: the sword in every 1 Sept render and the standing shot is HIS SASANIAN SWORD (read against the sword folder) " + EM + " the " + LQ + "spatha raised / NON-CANON on the sword" + RQQ + " wording of v2.3 and v2.6 was a misreading of the images, corrected in " + SEC + "8, " + SEC + "9, " + SEC + "11; two stale file names in " + SEC + "11 corrected to the folder" + RQ + "s names. No render needs redoing for the sword."),
], "MARDIN CHARACTER FILE")

print("TOTAL pairs=%d changed=%d zeros=%d" % (TOTAL["pairs"], TOTAL["changed"], len(TOTAL["zeros"])))
for z in TOTAL["zeros"]:
    print("  ", z)
