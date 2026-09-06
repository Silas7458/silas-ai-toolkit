# -*- coding: utf-8 -*-
# cascade_00W2.py - S#327 (5 Sept 2026), second wave. Appends R-174 (Mardin: the green seat, his own sword) and
# R-175 (Gallus's Weyland spatha IS the memorial, re-hilted gold; the inscription stands) to 00W, then cascades.
#   python cascade_00W2.py dry | all
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RUN = r"C:\Users\silas\AppData\Roaming\npm\node_modules\@googleworkspace\cli\run-gws.js"
MAN = r"C:\Users\silas\Documents\last-roman\canon-mirror\_manifest.json"
CANON = r"C:\Users\silas\Documents\last-roman\canon-mirror\canon"
EM = "\u2014"; RQ = "\u2019"; SEC = "\u00a7"; MID = "\u00b7"; EN = "\u2013"; LQ = "\u201c"; RQQ = "\u201d"
MODE = (sys.argv[1] if len(sys.argv) > 1 else "dry").lower()
DRY = MODE == "dry"
D5 = "5 Sept 2026"; W = "00W"

man = json.load(open(MAN, encoding="utf-8"))["files"]
by_id = {f["id"]: f for f in man}


def gws(args):
    r = subprocess.run(["node", RUN] + args + ["--format", "json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("gws failed: " + (r.stderr or r.stdout)[:800])
    return json.loads(r.stdout) if r.stdout.strip() else {}


def find(substr):
    hits = [f for f in man if f["live"] and f["mime"].endswith("document") and substr in f["name"]]
    if len(hits) != 1:
        raise SystemExit("expected 1 doc for %r, got %d: %s" % (substr, len(hits), [h["name"][:60] for h in hits]))
    return hits[0]["id"]


def mirror_text(doc_id):
    f = by_id.get(doc_id)
    if not f:
        return ""
    for lf in f.get("local_files", []):
        if lf.endswith(".txt"):
            try:
                return open(os.path.join(CANON, lf), encoding="utf-8").read()
            except OSError:
                return ""
    return ""


TOTAL = {"pairs": 0, "changed": 0, "zeros": []}


def replace_all(doc_id, pairs, label):
    TOTAL["pairs"] += len(pairs)
    if DRY:
        t = mirror_text(doc_id)
        counts = [t.count(a) for a, b in pairs]
        print("%-30s DRY %s" % (label, counts))
        for (a, b), c in zip(pairs, counts):
            if c != 1:
                print("   %s x%d for anchor: %s" % ("MISSING" if c == 0 else "MULTI", c, a[:100]))
                TOTAL["zeros"].append((label, a[:100], c))
        return counts
    reqs = [{"replaceAllText": {"containsText": {"text": a, "matchCase": True}, "replaceText": b}} for a, b in pairs]
    res = gws(["docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id}), "--json", json.dumps({"requests": reqs}, ensure_ascii=False)])
    counts = [r.get("replaceAllText", {}).get("occurrencesChanged", 0) for r in res.get("replies", [])]
    TOTAL["changed"] += sum(counts)
    print("%-30s %s" % (label, counts))
    for (a, b), c in zip(pairs, counts):
        if c == 0:
            print("   ZERO for anchor: " + a[:100])
            TOTAL["zeros"].append((label, a[:100], 0))
    return counts


def bump_pair(doc_id, note):
    """Prepend a new s14 changelog line above the current top version line (newest-first lists)."""
    t = mirror_text(doc_id)
    best = None
    for line in t.split("\n"):
        m = re.match(r"^v(\d+)\.(\d+)\b", line)
        if m:
            key = (int(m.group(1)), int(m.group(2)))
            if best is None or key > best[0]:
                best = (key, line)
    if not best:
        raise SystemExit("no version line in " + doc_id)
    (maj, mi), line = best
    anchor = line.rstrip("\r")
    if t.count(anchor) != 1:
        anchor = anchor[:120]
    new = "v%d.%d %s %s %s %s\n" % (maj, mi + 1, EM, D5, EM, note)
    return (anchor, new + anchor)


# ------------------------------------------------------------------ ids
DOC_00W = "1PW6x_Yx4jBuALpjIJquDGeSyP6NOVqRG4eBV-xnPkEI"
DOC_00E = find("00E ")
DOC_00G = find("00G ")
DOC_00K = "1ZJ4FEfZUmwgubJRQ-ZQ1x69t1tOLFSn3goa0K13Kwf0"
DOC_00M = find("00M ")
DOC_00T = "1-fcYnOY4yxT3zeH_Ufas6e2yWAwyliVc3SuVbj731rE"
DOC_00U = "17PJDDKAfrtQ7bNUXYrWImE_RJdolmSliimC0YqCEsb0"
COLORS = find("THE DRAGONS" + RQ + " COLORS") if any(("THE DRAGONS" + RQ + " COLORS") in f["name"] for f in man) else find("THE DRAGONS' COLORS")
VRI = find("VISUAL REFERENCE INDEX")
FINAL_EP = "10GEgLzXUHCN0JJVBLmZ3iTYX4xVF3jFyTqHiqdW4zMY"
S1_STATE = "1KL-x9Wi5KFgxUOocL39BTRoXXAj-XrIr2e7zytcjLaI"
S2_MASTER = "1pu5Qx78pLylAGfgtg2reGJ6rYsxqEENkdrMIT4Eaqsw"
S2_STATE = "1NiHz3DJ9CSzs_Sm_x6X-fKxDfVdbms4AymxNNVHukcU"
S3_STATE = "1Xq4WfvWyBFYhjw-gvl8jmzUtEQlopRzgrY_oTB5yG_o"
S3_LIST = "1Z6XpsPnXO9Msy9vHQUyDKlC2m0FNy3_6MO6dTORC1cg"
EP_MAP = "1RjPbhpWwDliekXVYlFzXI1CNMal4Skey5xGaalm0z8Q"
CHAR_BIBLE = "1SaArCJb2HbI8baLQNE2EA3prThQyZUkAjLCkd1EowqM"
SHOW_BIBLE = "1FlguQomgE2_a0Rp-7eC7Nr_e5wFNtdGgusoY2rNJc0Y"
ROSTER = "1CCrqxs1fTylYwdb-XDct_97zWaGw8mbELvkNLn4BwVI"
RUNBOOK = "13kZn_jj_IlYN4W6kNGKaYicEH-q-1nnaRnWRSTqMH3Y"
F_MARDIN = find("MARDIN AFZAR " + EM + " CHARACTER FILE")
F_GALLUS = find("GALLUS " + EM + " CHARACTER FILE")
F_WEYLAND = "1N7eyV3a78XibjLpR8_GYgPnHTaVtwdSTDvfCetPDcv8"
F_VALERIUS = "1gQ2rtpFXsADa2KETUP5uolHu6RF2kaFLTJ5ydsavEdo"
SK_VALERIUS = find("VALERIUS FLAVIUS " + EM + " CHARACTER SKETCH")
F_LUCIUS = "1MmChZDJ7177HqitvmGkDZ90mwKaKvxzN2xdKptrKlhc"
F_AMBROSIUS = find("AMBROSIUS (UTHR PENDRAGON) " + EM + " CHARACTER FILE")
F_AFRICANUS = find("AFRICANUS " + EM + " CHARACTER FILE")
F_GALAAD = find("GALAAD CASTUS " + EM + " CHARACTER FILE")
F_PERCENNIUS = find("PERCENNIUS VALA " + EM + " CHARACTER FILE")
F_DRUSTAN = find("DRUSTAN CUNOMARI " + EM + " CHARACTER FILE")

R4 = W + " R-174"; R5 = W + " R-175"

# ------------------------------------------------------------------ 00W: the two new rulings
NEW_RULINGS = (
"R-174 " + EM + " MARDIN: THE GREEN SEAT, THE GREEN PAULDRON, AND HIS OWN SWORD. [A " + EM + " " + D5 + ", later the same day]\n"
"Author, in substance: Mardin is not a cavalry Dragon of the Manus per se, but he is a primary warrior in the offensives " + EM + " mounted, with his own kit and an open sword " + EM + " so he needs a place at the table; Gallus" + RQ + "s death (the green dragon, the green pauldron) inadvertently created a natural opening, literarily and circumstantially, for him to occupy that vacated spot; his Sasanian cavalry kit was green, so it made sense for him to occupy the green dragon" + RQ + "s seat. "
"(a) SEAT 3 IS THE GREEN SEAT from 108. The green PAULDRON is his (00T R-153 stands); the seat carries the color; the green DRACO stays UNFIELDED " + EM + " he rides as the second overwatch with the bow, not in the column " + EM + " so the riding Manus stays SEVEN (00M R-119 re-grounded: the seat is filled, the column slot is not). ELEN alone is colorless. The 2 Sept " + LQ + "pauldron only, Seat 3 stays colorless" + RQQ + " closure (R-153 amended) is SUPERSEDED. "
"(b) HIS SWORD IS HIS OWN. He carries the SASANIAN SWORD he carried out of the empire after the poisoned cup (00P; the object in his folder " + EM + " " + LQ + "Mardin Sassanian sword unsheathed / sheathed / handle only" + RQQ + ") and NO Weyland spatha, ever. 00T R-151" + RQ + "s " + LQ + "every rider but Ambrosius" + RQQ + " now reads " + LQ + "every rider but Ambrosius and Mardin" + RQQ + "; 00H R-76" + RQ + "s " + LQ + "every Dragon carries Weyland steel" + RQQ + " reads with this one exception; the 110 " + LQ + "the only Dragon with no spatha" + RQQ + " line was right all along. The 1 Sept moorland renders that show a spatha raised are look references for the man and NON-CANON on the sword; his sword folder is the authority. "
"(c) GALLUS" + RQ + "S WEYLAND SPATHA IS NOT HIS " + EM + " see R-175. (d) The kit is unchanged: when captured he had only his Sasanian kit; at the Sanctuary he puts on the available Roman Dragon leather cuirass over tunic and mail, under his signature chest harness (00T R-155 amended 2), and after 108 the green pauldron.\n\n"
"R-175 " + EM + " GALLUS" + RQ + "S WEYLAND SPATHA IS THE MEMORIAL " + LQ + "EXCALIBUR" + RQQ + " " + EM + " RE-HILTED TO THE COMMANDER" + RQ + "S GOLD AT 310; THE INSCRIPTION STANDS. [A " + EM + " " + D5 + "]\n"
"Author, in substance: the Gallus spatha is not given to Mardin; it stayed in the Sanctuary as a memorial sword until 310, when they go back to the Sanctuary and make Valerius" + RQ + "s posthumous memorial sword " + EM + " they update the Gallus Weyland spatha, the hilt and the handle, to the gold like Ambrosius" + RQ + "s Commander" + RQ + "s Sword, and place it into the stone cairn of Valerius. On the inscription, verbatim: " + LQ + "Keep the inscription!! It" + RQ + "s also what they put on the sword. This is what will become the memorial " + RQ + "Valerius" + RQ + "s steel" + RQ + ". EX" + MID + "CHALYBE" + MID + "VALERII." + RQQ + " "
"WHAT IT SETTLES: (1) After 108 Gallus" + RQ + "s blade passes to nobody (00I R-82 stands " + EM + " the custom does not exist yet) and HANGS IN THE SANCTUARY AS THE MEMORIAL SWORD through Seasons Two and Three; 00I Open Item 4 (" + LQ + "where does his blade physically go?" + RQQ + ") is CLOSED. (2) At 310 Weyland fires the forge one last time NOT to forge a new blade but to RE-HILT THIS ONE: Gallus" + RQ + "s Castra steel takes the gold guard and grip of the Commander" + RQ + "s Sword " + EM + " its twin in appearance " + EM + " and is set in Valerius" + RQ + "s cairn. " + LQ + "New steel / a new blade / the last of the special steel" + RQQ + " is DEAD wherever it stands; " + LQ + "the forge" + RQ + "s last firing" + RQQ + " stands as the re-hilting. (3) THE INSCRIPTION IS UNCHANGED, verbatim, with the interpuncts: EX" + MID + "CHALYBE" + MID + "VALERII " + EM + " DVX" + MID + "VLTIMVS" + MID + "DRACONVM " + EM + " it is what they put on the sword, and " + LQ + "the steel of Valerius" + RQQ + " is the steel of his Dragons; the memorial IS " + LQ + "Valerius" + RQ + "s steel" + RQQ + " from that night on. (4) Gallus, the only honored dead with no heir carrying his blade, is carried after all " + EM + " by the ground: the first Dragon to die and the man who led them share one object under the willow, and the sword William pulls in 1066 is Castra steel, twenty years older than the pilot. (5) " + LQ + "Reforged from Valerius" + RQ + "s own blade" + RQQ + " stays REJECTED (his blade is lost at 207, 00G R-66); the Commander" + RQ + "s Sword is untouched (Uthr" + RQ + "s, to Afallon).\n"
"CASCADED " + D5 + " (S#327, second wave): 00E/00G/00K/00M/00T/00U bracketed; the Colors spec; Manus Roster; Series Episode Map; S1 State; S2 Master + State; S3 State + Episode List; the Final Episode doc; Character Bible; Showrunner" + RQ + "s Bible; Visual Reference Index; the Mardin, Gallus, Weyland, Valerius (file + sketch), Lucius, Ambrosius, Africanus, Galaad, Percennius and Drustan files; the RUNBOOK.\n"
"END OF 00W.")

# ------------------------------------------------------------------ cascade
def run():
    replace_all(DOC_00W, [
        ("END OF 00W.", NEW_RULINGS),
        (LQ + "MARDIN (no color)" + RQQ + " in the Masters' riding-order lines is true of the draco and the seat (00T R-153 puts Gallus's green on his pauldron only; the Colors spec, 00T and his file carry it);",
         LQ + "MARDIN (no color)" + RQQ + " " + EM + " SUPERSEDED the same day by R-174 below (Seat 3 is the green seat; the Masters' riding-order lines now patched);"),
    ], "00W")
    replace_all(DOC_00T, [
        ("WHO CARRIES IT: every Dragon rider " + EM + " except Ambrosius (R-152).",
         "WHO CARRIES IT: every Dragon rider " + EM + " except Ambrosius (R-152) [and except MARDIN, who carries his own Sasanian sword and no Weyland spatha " + EM + " " + R4 + ", " + D5 + "]."),
        ("is unchanged for the DRACO; the PAULDRON is now his.", "is unchanged for the DRACO; the PAULDRON is now his. [" + R4 + ", " + D5 + ": the SEAT is now green too.]"),
        ("R-153 AMENDED " + EM + " THE GREEN IS THE PAULDRON ONLY.",
         "R-153 AMENDED [SUPERSEDED " + R4 + ", " + D5 + ": Seat 3 IS the green seat " + EM + " pauldron green, draco unfielded, his own Sasanian sword] " + EM + " THE GREEN IS THE PAULDRON ONLY."),
    ], "00T")
    replace_all(DOC_00U, [
        ("in new steel, inscribed EX", "[AMENDED " + R5 + ", " + D5 + ": by RE-HILTING GALLUS" + RQ + "S Weyland spatha to the gold, not in new steel] inscribed EX"),
    ], "00U")
    replace_all(DOC_00G, [
        ("2. THE MEMORIAL \"EXCALIBUR\": forged at the END OF SEASON THREE, as",
         "2. THE MEMORIAL \"EXCALIBUR\" [AMENDED " + R5 + ", " + D5 + ": it is GALLUS'S Weyland spatha, kept as the Sanctuary's memorial sword from 108, RE-HILTED to the Commander's gold at 310 " + EM + " not new steel; the inscription stands]: forged at the END OF SEASON THREE, as"),
    ], "00G")
    replace_all(DOC_00E, [
        ("exact twin in appearance. \"Excalibur\" refers SOLELY to the memorial",
         "exact twin in appearance [" + R5 + ", " + D5 + ": Gallus's Weyland spatha re-hilted to the gold, not new steel]. \"Excalibur\" refers SOLELY to the memorial"),
    ], "00E")
    replace_all(DOC_00K, [
        ("Mardin and Elen: NO color " + EM + " not cavalry; the juxtaposition.",
         "Mardin and Elen: NO color " + EM + " not cavalry; the juxtaposition [" + R4 + ", " + D5 + ": Mardin holds the GREEN seat from 108 " + EM + " pauldron green, draco unfielded; Elen alone colorless]."),
    ], "00K")
    replace_all(DOC_00M, [
        ("Because Gallus's GREEN seat was never refilled (he died S1E08, no pass)",
         "Because Gallus's GREEN seat was never refilled in the COLUMN (he died S1E08, no pass; Mardin holds the green at the table from 108 but rides overwatch with the bow " + EM + " " + R4 + ")"),
    ], "00M")
    replace_all(COLORS, [
        ("the green is a door left open (if a nine-Manus is ever needed on screen, MARDIN can field the green draco).",
         "the green passes to MARDIN'S SEAT (" + R4 + ", " + D5 + "): pauldron green, Seat 3 the green seat; the draco stays unfielded (he rides overwatch with the bow) " + EM + " a door left open (if a nine-Manus is ever needed on screen, MARDIN can field the green draco)."),
        ("WHO HAS NO COLOR: MARDIN and ELEN. They hold seats (3 and 4) but they are not classically trained cavalry " + EM + " Mardin the physician-engineer on the crest with the bow, Elen the archer in the treeline " + EM + " and the show needs the juxtaposition. No draco, no windsock, no colored brand.",
         "WHO HAS NO COLOR: ELEN alone (" + R4 + ", " + D5 + " " + EM + " MARDIN holds the GREEN: Seat 3 is the green seat and his LEFT pauldron carries Gallus's brand; no draco, no windsock for him either " + EM + " he rides overwatch with the bow; his own Sasanian sword, no Weyland spatha). Elen holds Seat 4 but is not classically trained cavalry " + EM + " the archer in the treeline " + EM + " and the show needs the juxtaposition. No draco, no windsock, no colored brand."),
    ], "COLORS spec")
    replace_all(ROSTER, [
        ("SEAT 3 " + EM + " MARDIN (Merlin analog; scholar-physician). NO color, no draco " + EM + " not cavalry [00K R-111b].",
         "SEAT 3 " + EM + " MARDIN (Merlin analog; scholar-physician) " + EM + " THE GREEN SEAT from 108 (Gallus's green on his pauldron; the seat carries the color; NO draco " + EM + " he rides overwatch with the bow; his OWN Sasanian sword, no Weyland spatha) [" + R4 + ", " + D5 + "; was: NO color, 00K R-111b]."),
        ("the memorial \"Excalibur\" (NEW steel, Weyland's masterwork)", "the memorial \"Excalibur\" (GALLUS'S Weyland spatha re-hilted to the Commander's gold " + EM + " " + R5 + "; not new steel)"),
        ("is NEW steel, the forge's one last firing " + EM + " Weyland's masterwork.",
         "is GALLUS'S Weyland spatha, kept as the Sanctuary's memorial sword from 108 and RE-HILTED to the Commander's gold in the forge's one last firing (" + R5 + ", " + D5 + ") " + EM + " Weyland's last work."),
        ("the memorial NEW steel later set in his cairn", "the memorial " + EM + " Gallus's blade re-hilted gold, " + R5 + " " + EM + " later set in his cairn"),
        ("Version 5.4 " + EM + " 5 September 2026 (" + W + ":", "Version 5.5 " + EM + " 5 September 2026, later (" + R4 + " Seat 3 the green seat " + MID + " " + R5 + " the memorial is Gallus's spatha re-hilted). Prior: Version 5.4 " + EM + " 5 September 2026 (" + W + ":"),
    ], "MANUS ROSTER")
    replace_all(EP_MAP, [
        ("GALLUS green " + EM + " dies at 108 before the seat system exists; the green is left unassigned (later \"green\" = untried; the Green Manus rides under no dracos, no color) " + MID + " MARDIN and ELEN none (not cavalry " + EM + " the juxtaposition).",
         "GALLUS green " + EM + " dies at 108 before the seat system exists; the green passes to MARDIN'S seat (" + R4 + ": Seat 3 the green seat, pauldron green, draco unfielded) (later \"green\" = untried; the Green Manus rides under no dracos, no color) " + MID + " ELEN none (not cavalry " + EM + " the juxtaposition)."),
        ("Mardin (no color; braced; the second overwatch; the physician)", "Mardin (the green seat, pauldron only " + EM + " no draco; his own Sasanian sword; braced; the second overwatch; the physician)"),
        ("Version 15 " + EM + " 5 September 2026 " + MID + " " + W + ":", "Version 16 " + EM + " 5 September 2026, later " + MID + " " + R4 + " (Mardin's green seat, his own sword) in the colors block and the S2 curtain-up. Prior: Version 15 " + EM + " 5 September 2026 " + MID + " " + W + ":"),
    ], "EPISODE MAP")
    replace_all(S1_STATE, [
        ("at S3's end: NEW steel, the master forge's ONE", "at S3's end: GALLUS'S Weyland spatha re-hilted to the gold [" + R5 + ", " + D5 + " " + EM + " not new steel], the master forge's ONE"),
        ("S2E07; the memorial is NEW steel)", "S2E07; the memorial is Gallus's blade re-hilted " + EM + " " + R5 + ")"),
        ("Version 5.5 " + EM + " 5 September 2026 " + MID + " " + W + " R-163", "Version 5.6 " + EM + " 5 September 2026, later " + MID + " " + R5 + " (the memorial is Gallus's spatha re-hilted; " + SEC + "1 and " + SEC + "7). Prior: Version 5.5 " + EM + " 5 September 2026 " + MID + " " + W + " R-163"),
    ], "S1 STATE")
    replace_all(S2_MASTER, [
        ("the memorial \"Excalibur\" is NEW steel, forged at S3's end in the master forge's ONE LAST FIRING from the last of the special steel;",
         "the memorial \"Excalibur\" is Gallus's Weyland spatha re-hilted to the gold at S3's end in the master forge's ONE LAST FIRING (" + R5 + " " + EM + " not new steel);"),
        ("MARDIN (no color)", "MARDIN (the green " + EM + " pauldron only, no draco; " + R4 + ")"),
        ("Version 4.13 " + EM + " 25 August 2026 " + MID + " 205", "Version 4.14 " + EM + " 5 September 2026 " + MID + " " + R4 + " (Mardin's green in WHO RIDES) " + MID + " " + R5 + " (the memorial is Gallus's spatha re-hilted). Prior: Version 4.13 " + EM + " 25 August 2026 " + MID + " 205"),
    ], "S2 MASTER")
    replace_all(S2_STATE, [
        ("NEW steel: the Commander's Sword's exact twin but for the inscription, forged at S3's end in the master forge's ONE LAST FIRING from the LAST of the special steel [00G R-66]",
         "GALLUS'S Weyland spatha re-hilted to the Commander's gold (" + R5 + " " + EM + " not new steel): the Commander's Sword's exact twin but for the inscription, re-hilted at S3's end in the master forge's ONE LAST FIRING [00G R-66]"),
        ("Version 2.13 " + EM + " 25 August 2026 " + MID + " 205", "Version 2.14 " + EM + " 5 September 2026 " + MID + " " + R5 + " (the memorial is Gallus's spatha re-hilted). Prior: Version 2.13 " + EM + " 25 August 2026 " + MID + " 205"),
    ], "S2 STATE")
    replace_all(S3_STATE, [
        ("makes the memorial \"Excalibur\" from the last of the special steel;", "makes the memorial \"Excalibur\" by re-hilting Gallus's Weyland spatha to the Commander's gold (" + R5 + " " + EM + " not new steel);"),
        ("NEW steel, the master forge's ONE LAST FIRING, the LAST of the special steel [00G R-66;", "GALLUS'S Weyland spatha re-hilted gold in the master forge's ONE LAST FIRING (" + R5 + " " + EM + " not new steel) [00G R-66;"),
    ], "S3 STATE")
    replace_all(S3_LIST, [
        ("the memorial \"Excalibur\" is NEW steel " + EM + " the master forge's ONE LAST FIRING at season's end, the last of the special steel, twin of the Commander's Sword + inscription, into the stones]",
         "the memorial \"Excalibur\" is Gallus's Weyland spatha re-hilted to the Commander's gold in the master forge's ONE LAST FIRING at season's end (" + R5 + " " + EM + " not new steel), twin of the Commander's Sword + inscription, into the stones]"),
        ("\"Excalibur\" " + EM + " NEW steel, the master forge's ONE LAST FIRING, the last", "\"Excalibur\" " + EM + " GALLUS'S Weyland spatha re-hilted to the Commander's gold (" + R5 + "; not new steel), the master forge's ONE LAST FIRING, the last"),
        ("of the special steel, the Commander's Sword's exact twin but for the", "of the special steel [the firing, not the steel " + EM + " R-175], the Commander's Sword's exact twin but for the"),
        ("Version 4.0 " + EM + " 18 August 2026 " + MID + " 00K R-111:", "Version 4.1 " + EM + " 5 September 2026 " + MID + " " + R5 + " (the memorial is Gallus's spatha re-hilted, header + 310). Prior: Version 4.0 " + EM + " 18 August 2026 " + MID + " 00K R-111:"),
    ], "S3 EPISODE LIST")
    replace_all(FINAL_EP, [
        ("THE MEMORIAL \"EXCALIBUR\" [R-66]: NEW steel; the master forge's ONE", "THE MEMORIAL \"EXCALIBUR\" [R-66; " + R5 + "]: GALLUS'S Weyland spatha re-hilted to the gold, not new steel; the master forge's ONE"),
    ], "FINAL EPISODE")
    replace_all(CHAR_BIBLE, [
        ("(new steel, EX", "(Gallus's Weyland spatha re-hilted to the gold " + EM + " " + R5 + "; EX"),
        ("made a cavalry military engineer and covert operator;", "made a cavalry military engineer and covert operator; carries his OWN Sasanian sword, no Weyland spatha, and holds the GREEN seat from 108 (" + R4 + ");"),
        ("Version 0.6 " + EM + " 5 September 2026 " + EM + " " + W + ":", "Version 0.7 " + EM + " 5 September 2026, later " + EM + " " + R4 + " (Mardin) " + MID + " " + R5 + " (Valerius's memorial). Prior: Version 0.6 " + EM + " 5 September 2026 " + EM + " " + W + ":"),
    ], "CHARACTER BIBLE")
    replace_all(SHOW_BIBLE, [
        ("forges for Valerius's grave " + EM + " the Commander's Sword's EXACT TWIN in", "re-hilts for Valerius's grave (Gallus's Weyland spatha, " + R5 + ") " + EM + " the Commander's Sword's EXACT TWIN in"),
        ("  NEW steel " + EM + " the master forge fired ONE LAST TIME as the book", "  GALLUS'S Weyland spatha re-hilted gold (" + R5 + ", " + D5 + "; not new steel) " + EM + " the master forge fired ONE LAST TIME as the book"),
        ("Version 2.7 " + EM + " 5 September 2026 " + MID + " " + W + " R-163", "Version 2.8 " + EM + " 5 September 2026, later " + MID + " " + R5 + " (the memorial is Gallus's spatha re-hilted, " + SEC + "3 and the sword-in-the-stone block). Prior: Version 2.7 " + EM + " 5 September 2026 " + MID + " " + W + " R-163"),
    ], "SHOWRUNNER'S BIBLE")
    replace_all(VRI, [
        ("   the memorial Excalibur is its exact twin but for the inscription.", "   the memorial Excalibur is its exact twin but for the inscription (Gallus's steel re-hilted, " + R5 + ")."),
        ("(the grave's \"Excalibur\" is NEW steel, its twin only in shape; 00G R-66)", "(the grave's \"Excalibur\" is Gallus's blade re-hilted gold, its twin in shape; 00G R-66 as amended by " + R5 + ")"),
        ("(a) R-50 " + EM + " the memorial Excalibur is a blade WEYLAND FORGES as the", "(a) R-50 " + EM + " the memorial Excalibur is a blade WEYLAND RE-HILTS (Gallus's, " + R5 + ") as the"),
        ("The memorial is NEW STEEL: the master forge's ONE LAST FIRING at", "The memorial is GALLUS'S Weyland spatha re-hilted gold (" + R5 + ", " + D5 + "; NOT new steel): the master forge's ONE LAST FIRING at"),
    ], "VISUAL REFERENCE INDEX")
    replace_all(RUNBOOK, [
        ("every rider but Ambrosius; Valerius standard;", "every rider but Ambrosius [and Mardin " + EM + " " + R4 + "]; Valerius standard;"),
        ("R-153 Mardin wears Gallus" + RQ + "s green pauldron;", "R-153 Mardin wears Gallus" + RQ + "s green pauldron [" + R4 + ": and holds the green seat; his own Sasanian sword];"),
    ], "RUNBOOK")
    # ---- character files
    replace_all(F_MARDIN, [
        ("SEAT & COLOR: SEAT 3 of the Ten. NO COLOR, NO DRACO, NO WINDSOCK " + EM + " not classically trained Roman cavalry; the physician-engineer on the crest with the bow; the show needs the JUXTAPOSITION. (He could field Gallus's unassigned GREEN draco if a nine-Manus were ever needed on screen " + EM + " a door left open.) [A " + EM + " 00K R-111b; Colors spec]",
         "SEAT & COLOR: SEAT 3 of the Ten " + EM + " THE GREEN SEAT (" + R4 + ", " + D5 + "): Gallus's death at 108 opened the green, and Mardin " + EM + " a primary warrior in the offensives, mounted, with his own kit and his own sword, his Sasanian kit already green " + EM + " occupies it at the table; Gallus's green brand on his LEFT pauldron; NO DRACO, NO WINDSOCK " + EM + " not classically trained Roman cavalry; the physician-engineer on the crest with the bow; the show needs the JUXTAPOSITION. (He could field the green draco if a nine-Manus were ever needed on screen " + EM + " a door left open.) [A " + EM + " " + R4 + "; 00T R-153; 00K R-111b]"),
        ("NO COLOR, NO DRACO, NO WINDSOCK, NO COLORED BRAND on the pauldron " + EM + " Seat 3 is colorless by design (whether he wears a plain pauldron at all is unspecified). [A " + EM + " Colors spec]",
         "THE GREEN (" + R4 + ", " + D5 + "): Gallus's green brand on the LEFT pauldron; Seat 3 is the green seat; NO DRACO, NO WINDSOCK " + EM + " he rides overwatch with the bow. [A " + EM + " " + R4 + "; 00T R-153]"),
        ("THE WEYLAND SPATHA IN HIS HAND [A " + EM + " 00T R-151, 1 Sept 2026]: R-151 puts the standard Weyland spatha in every rider" + RQ + "s hand but Ambrosius" + RQ + "s " + EM + " his included " + EM + " and the 1 Sept shots show it raised (bone grip, redwood pommel).",
         "NO WEYLAND SPATHA (" + R4 + ", " + D5 + "): the author rules that he carries HIS OWN SASANIAN SWORD and no Weyland blade; R-151" + RQ + "s " + LQ + "every rider but Ambrosius" + RQQ + " now reads " + LQ + "but Ambrosius and Mardin." + RQQ + " The 1 Sept moorland shots that show a spatha raised are look references for the man and NON-CANON on the sword; his sword folder is the authority. [Was: R-151 puts the standard Weyland spatha in every rider" + RQ + "s hand but Ambrosius" + RQ + "s " + EM + " his included " + EM + " and the 1 Sept shots show it raised (bone grip, redwood pommel).]"),
        ("WHETHER the eastern blade and a Weyland blade are the same weapon, two weapons, or successive weapons is NOT ESTABLISHED; the built 110 text (\"no spatha\") leans toward the eastern blade as his only sword. " + SEC + "13. [C/?]",
         "RULED (" + R4 + ", " + D5 + "): the eastern blade is his ONLY sword " + EM + " no Weyland spatha, ever; the built 110 text (\"no spatha\") was right; R-76 reads with this one exception. [A]"),
        ("The GREEN DRACO stays where 00K R-111b left it: unassigned, the one he could field if a nine-Manus were ever needed. He still carries no color of his own at the table.",
         "The GREEN DRACO stays unfielded " + EM + " he rides overwatch with the bow " + EM + " the one he could field if a nine-Manus were ever needed. At the table the green is HIS: Seat 3 is the green seat (" + R4 + ", " + D5 + ")."),
        ("His SEAT stays colorless and the green DRACO stays unassigned (00K R-111b); only the shoulder changed.",
         "His SEAT is the GREEN SEAT (" + R4 + ", " + D5 + " " + EM + " superseding the 2 Sept " + LQ + "pauldron only" + RQQ + " closure); the green DRACO stays unfielded."),
        ("17. BOTH BLADES, OR ONE? R-151 puts a Weyland spatha in his hand; the Sasanian sword is the audited eastern blade. Rec [P]: BOTH",
         "17. BOTH BLADES, OR ONE? " + EM + " CLOSED (" + R4 + ", " + D5 + "): ONE " + EM + " his own Sasanian sword, always; no Weyland spatha. [Was: R-151 puts a Weyland spatha in his hand; the Sasanian sword is the audited eastern blade. Rec [P]: BOTH"),
        bump_pair(F_MARDIN, R4 + " (S#327): Seat 3 is the GREEN SEAT (pauldron + seat; draco unfielded); HIS OWN Sasanian sword, no Weyland spatha " + EM + " " + SEC + "1, " + SEC + "8, " + SEC + "9, " + SEC + "11, " + SEC + "12, " + SEC + "13-17; the moorland spatha renders non-canon on the sword."),
    ], "MARDIN file")
    replace_all(F_GALLUS, [
        ("After 108 the GREEN is UNASSIGNED " + EM + " \"a door left open (if a nine-Manus is ever needed on screen, MARDIN can field the green draco)\"; \"green (Gallus) permanently unassigned\" in the 204+ standing form (00M R-119).",
         "After 108 the GREEN passes to MARDIN'S SEAT (" + R4 + ", " + D5 + "): his brand on Mardin's pauldron, Seat 3 the green seat; the green DRACO stays unfielded " + EM + " \"a door left open (if a nine-Manus is ever needed on screen, MARDIN can field the green draco)\"; the 204+ standing form still rides seven (00M R-119)."),
        ("his green \"permanently unassigned\" is the reason the standing Manus is SEVEN and one rider is always held (00M R-119).",
         "his column slot never refilled is the reason the standing Manus is SEVEN and one rider is always held (00M R-119; the green itself is Mardin's at the table " + EM + " " + R4 + ")."),
        ("the memorial goes into Valerius's cairn beside it at 310.", "the memorial " + EM + " HIS OWN BLADE, re-hilted to the Commander's gold (" + R5 + ") " + EM + " goes into Valerius's cairn beside it at 310."),
        ("Gallus is represented by a tree.", "Gallus is represented by a tree " + EM + " and, since 310, by the ground itself: his Weyland spatha, re-hilted gold, is the sword in Valerius's cairn (" + R5 + ")."),
        ("no heir carries his blade; the willow in the 1066 shot.", "no heir carries his blade " + EM + " the ground does: his spatha, re-hilted gold, is the sword William pulls (" + R5 + "); the willow in the 1066 shot."),
        ("Left UNASSIGNED with the sword after his death (Character Bible) " + EM + " the COLOR is now split: the green PAULDRON is Mardin" + RQ + "s (00T R-153), the green DRACO stays unassigned.",
         "Left with the sword after his death " + EM + " the SWORD hangs in the Sanctuary as the memorial blade until 310 (" + R5 + "); the green PAULDRON and the green SEAT are Mardin" + RQ + "s (00T R-153; " + R4 + "); the green DRACO stays unfielded."),
        ("(Mardin may field the green if a nine-Manus is ever needed).\" [A " + EM + " Character Bible; 00K R-111", "(Mardin may field the green if a nine-Manus is ever needed).\" [" + R4 + ": the green is Mardin's at the table.] [A " + EM + " Character Bible; 00K R-111"),
        ("1. WHERE DOES HIS BLADE PHYSICALLY GO? " + EM + " the author's own open item (00I Open Item 4), the last live question about him.",
         "1. WHERE DOES HIS BLADE PHYSICALLY GO? " + EM + " CLOSED (" + R5 + ", " + D5 + "): it HANGS IN THE SANCTUARY AS A MEMORIAL SWORD through S2 and S3, and at 310 Weyland re-hilts it to the Commander's gold and it goes into Valerius's cairn " + EM + " the sword William pulls in 1066. [Was: the author's own open item (00I Open Item 4), the last live question about him."),
        ("10. CLOSED 2 Sept 2026 (00T R-153 amended): the author confirmed the split " + EM + " Mardin wears the green pauldron; the green draco stays unassigned;",
         "10. RE-CLOSED " + D5 + " (" + R4 + "): Mardin holds the GREEN SEAT " + EM + " pauldron and seat; the draco unfielded. [2 Sept, 00T R-153 amended: the split " + EM + " Mardin wears the green pauldron; the green draco stays unassigned;"),
        bump_pair(F_GALLUS, R4 + " (the green is Mardin's seat) + " + R5 + " (his spatha is the memorial, re-hilted gold at 310; 00I Open Item 4 closed) (S#327) " + EM + " " + SEC + "1, " + SEC + "3, " + SEC + "4, " + SEC + "9, " + SEC + "13."),
    ], "GALLUS file")
    replace_all(F_WEYLAND, [
        ("he fires the forge ONE LAST TIME with the LAST OF THE SPECIAL STEEL and makes the memorial \"Excalibur,\" the Commander's Sword's exact twin but for the inscription",
         "he fires the forge ONE LAST TIME and makes the memorial \"Excalibur\" by RE-HILTING GALLUS'S WEYLAND SPATHA " + EM + " kept in the Sanctuary as the memorial sword since 108 " + EM + " to the Commander's gold, the Commander's Sword's exact twin but for the inscription (" + R5 + ", " + D5 + "; not new steel)"),
        ("use THE LAST OF THE SPECIAL STEEL to make the memorial: NEW steel, a new blade, identical in appearance to the Commander's Sword but for the inscription",
         "make the memorial [AMENDED " + R5 + ", " + D5 + "]: NOT new steel " + EM + " GALLUS'S OWN WEYLAND SPATHA, the blade that hung in the Sanctuary as its memorial sword from 108, RE-HILTED to the Commander's gold guard and grip, identical in appearance to the Commander's Sword but for the inscription"),
        ("his own hands, the forge's one last firing, the last of the special steel. [A " + EM + " 00G R-66]", "his own hands, the forge's one last firing " + EM + " Gallus's spatha re-hilted to the gold, not new steel (" + R5 + "). [A " + EM + " 00G R-66 as amended]"),
        ("NEW steel, new blade; identical in appearance to the Commander's Sword but for the inscription; SET", "GALLUS'S Weyland spatha re-hilted to the Commander's gold (" + R5 + " " + EM + " not new steel); identical in appearance to the Commander's Sword but for the inscription; SET"),
        ("the memorial is NEW steel (00G R-66).", "the memorial is GALLUS'S blade re-hilted (" + R5 + ", " + D5 + "; 00G R-66's 'new steel' superseded)."),
        bump_pair(F_WEYLAND, R5 + " (S#327): the memorial is Gallus's Weyland spatha RE-HILTED to the Commander's gold at 310, not new steel; the inscription stands " + EM + " " + SEC + "3, " + SEC + "4, " + SEC + "9, " + SEC + "12."),
    ], "WEYLAND file")
    replace_all(F_VALERIUS, [
        ("the LAST of the special steel; the Commander's Sword's exact twin but for the inscription EX", "Gallus's Weyland spatha, the Sanctuary's memorial sword since 108, RE-HILTED to the Commander's gold (" + R5 + " " + EM + " not new steel); the Commander's Sword's exact twin but for the inscription EX"),
        ("NEW steel: the master forge's ONE LAST FIRING at S3's end, the LAST of the special steel (later called wootz/Damascus); WEYLAND'S OWN HANDS;",
         "GALLUS'S WEYLAND SPATHA (" + R5 + ", " + D5 + " " + EM + " not new steel): kept in the Sanctuary as its memorial sword from 108, RE-HILTED to the Commander's gold in the master forge's ONE LAST FIRING at S3's end; WEYLAND'S OWN HANDS;"),
        ("the sword in his cairn is a duplicate of the Commander" + RQ + "s Sword, new steel (00G R-66).", "the sword in his cairn is Gallus's Weyland spatha re-hilted to the Commander" + RQ + "s gold (00G R-66 as amended by " + R5 + ")."),
        bump_pair(F_VALERIUS, R5 + " (S#327): the memorial in his cairn is Gallus's Weyland spatha re-hilted to the Commander's gold, not new steel; the inscription stands " + EM + " " + SEC + "4, " + SEC + "9, " + SEC + "13."),
    ], "VALERIUS file")
    replace_all(SK_VALERIUS, [
        ("The sword in his grave is new steel, forged after his death.", "The sword in his grave is Gallus" + RQ + "s blade, re-hilted to the gold after his death (" + R5 + ")."),
    ], "VALERIUS sketch")
    replace_all(F_LUCIUS, [
        ("THE TWIN (00G R-66): Weyland's one last firing at S3's end " + EM + " the Commander's Sword's exact twin", "THE TWIN (00G R-66; " + R5 + "): Weyland's one last firing at S3's end re-hilts Gallus's Weyland spatha to the gold " + EM + " the Commander's Sword's exact twin"),
        bump_pair(F_LUCIUS, R5 + " (S#327): the twin is Gallus's spatha re-hilted (" + SEC + "9)."),
    ], "LUCIUS file")
    replace_all(F_AMBROSIUS, [
        ("(2) The memorial \"EXCALIBUR\" " + EM + " NEW steel, forged at S3's end in the master forge's ONE LAST FIRING from the last of the special steel, the Commander's Sword's exact twin",
         "(2) The memorial \"EXCALIBUR\" " + EM + " GALLUS'S Weyland spatha, the Sanctuary's memorial sword from 108, RE-HILTED to the Commander's gold at S3's end in the master forge's ONE LAST FIRING (" + R5 + " " + EM + " not new steel), the Commander's Sword's exact twin"),
        bump_pair(F_AMBROSIUS, R5 + " (S#327): the memorial is Gallus's spatha re-hilted, not new steel (" + SEC + "9 three-sword trap)."),
    ], "AMBROSIUS file")
    replace_all(F_AFRICANUS, [
        ("the memorial \"Excalibur\" is NEW steel into the cairn.", "the memorial \"Excalibur\" is Gallus's re-hilted blade into the cairn (" + R5 + ")."),
        bump_pair(F_AFRICANUS, R5 + " (S#327): context line " + EM + " the memorial is Gallus's spatha re-hilted."),
    ], "AFRICANUS file")
    for fid, label, seat in ((F_GALAAD, "GALAAD file", "6"), (F_PERCENNIUS, "PERCENNIUS file", "9")):
        replace_all(fid, [
            ("the memorial \"Excalibur\" is new steel into the cairn at 310. None of it touches Seat " + seat + ".", "the memorial \"Excalibur\" is Gallus's re-hilted blade into the cairn at 310 (" + R5 + "). None of it touches Seat " + seat + "."),
            bump_pair(fid, R5 + " (S#327): context line " + EM + " the memorial is Gallus's spatha re-hilted."),
        ], label)
    replace_all(F_DRUSTAN, [
        ("the memorial \"Excalibur\" is new steel into the cairn at 310. None of it touches Seat 10", "the memorial \"Excalibur\" is Gallus's re-hilted blade into the cairn at 310 (" + R5 + "). None of it touches Seat 10"),
        bump_pair(F_DRUSTAN, R5 + " (S#327): context line " + EM + " the memorial is Gallus's spatha re-hilted."),
    ], "DRUSTAN file")


run()
print("\nTOTAL pairs=%d changed=%d problem-anchors=%d" % (TOTAL["pairs"], TOTAL["changed"], len(TOTAL["zeros"])))
for z in TOTAL["zeros"]:
    print("  ", z)
