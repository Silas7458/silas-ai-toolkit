# -*- coding: utf-8 -*-
"""lint.py - THE LAST ROMAN canon lint (S#327, 5 Sept 2026).

Runs over the LIVE mirror text and prints every straggler it can find, so a fold never ends "clean" on faith:

  1. DEAD-PHRASE hits: every quoted phrase inside a "DEAD (recorded so it cannot return): ..." list in the
     00-series ruling docs, and every quoted phrase in a character file's section-12 "* "..." - DEAD" line,
     plus a hand-kept REGISTRY of retired wordings, searched across every live doc. A hit on a RECORD line
     (DEAD / SUPERSEDED / retired / [Was: / Prior: / Version N / vN.N / a bracket citing the superseding
     ruling) is not reported.
  2. VERSION-LINE defects: a doc whose newest-first changelog has a duplicate version number, or whose first
     version line is not its highest; an "END OF MASTER vX" footer that disagrees with the header version.
  3. Unclosed "[Was:" brackets.

Usage:  python lint.py            (report; exit 0 always - it is advisory)
        python lint.py --json     (machine-readable)
Called automatically at the end of `lr-pull` (bin/lr-pull.cmd) so every pull prints the straggler count.
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CANON = os.path.join(ROOT, "canon")
MAN = os.path.join(ROOT, "_manifest.json")

SKIP_PATH = re.compile(r"_ARCHIVE|HOW TO - CHARACTER FILES|Transcript|^20 - |_SESSION LOG|_GALLERY|NOTES FROM BROTHER|^19 - |STORY-SHAPE ATLAS - SOURCE/.*\.py|requirements\.txt|^0A - AUTHOR DICTATION|^00B - SHOW AND EPISODE ETHOS|AUTHOR VERBATIM", re.I)
RECORD = re.compile(r"\bDEAD\b|\bdead\b|SUPERSEDED|superseded|\bretired\b|RETIRED|STRUCK|struck|\[Was:|\bwas:|Prior:|^Version \d|^v\d+\.\d|re-ruled|re-aged|re-cut|\bformerly\b|the old\b|old profile|old arithmetic|kill log|KILL LOG|withdrawn|REJECTED|rejected|PURGED|purged|\[ANSWERED|\[CLOSED|\bCLOSED\b|not new steel|\[RECORD|00W R-1|00V R-1|00U R-1|00T R-1|00S R-1|00R R-1|00Q R-1|00P R-1|00O R-1|00N R-1|00M R-1|00L R-1|00K R-1|00J R-9|no longer|never again|is moot|straggler|Straggler|STRAGGLER|\(record\)|as re-dated|amended|AMENDED|Kills recorded|kills recorded|\bKILL:|abolished|ABOLISHED|quarantined|QUARANTINED|patched at the source|supersedes|SUPERSEDES", re.M)

LONG_LINE = 500   # chars; above this a record marker counts only near the hit
WINDOW = 220      # chars either side of a hit searched for a record marker on a long line

# Hand-kept registry of retired wordings that do not sit in any quoted DEAD list (add to it as rulings land).
REGISTRY = [
    "his protege", "his protégé", "Felix's protege", "Felix's protégé", "FELIX'S protégé", "protégé since", "under his wing", "Lancelot's PROTEGE",
    "low-mourning", "low-grief", "speed bump", "minimal mourning", "cheap seat",
    "father-figure", "father-commander", "the son watching the father",
    "two full seasons", "twenty episodes", "believed for two seasons", "two-season belief",
    "died S2E01", "dies at S2E01", "falls at S2E01",
    "S3E10 ring of fire", "dies at S3E10", "Vortigern dies in the S3E10",
    "Vortigern's second-in-command", "Vortigern’s second-in-command",
    "born 444", "26 at 460", "32 at 306", "older than Dacus by a decade", "a decade older than Dacus", "a year or two younger", "a year or two the younger",
    "born 411", "born c. 410", "Born c. 410", "born c. 415", "born c. 388",
    "about 50 at the", "from 435", "closed in 435", "in 435", "twenty-five years", "25 years", "fifty-three years", "53 years", "22 at the closure", "43 years",
    "NEW steel", "new steel", "NEW STEEL", "last of the special steel", "LAST OF THE SPECIAL STEEL", "twin-forged", "forges the memorial",
    "Mardin and Elen none", "Mardin and Elen: NO color", "Mardin and Elen no color", "Mardin and Elen carry none", "Mardin (no color", "MARDIN (no color", "the two colorless", "two colorless seats", "Seat 3 stays colorless", "Seat 3 is colorless", "green draco stays unassigned",
    "the Weyland spatha in his hand", "Weyland spatha when he rides",
    "twelve-year-old", "A.D. 450 —", "A.D. 455", "twelve to seventeen", "Cerdicus", "CERDICUS", "Gewissae",
    "PUBLIUS LANCEANUS", "Publius Lancianus", "Lancianus",
    "Badon 485", "at 45", "47 at Badon", "Uthr 47", "born 438", "born 443",
    "east wall", "EAST WALL", "BROKEN THE WALL", "broke the wall", "Amesbury",
    "five years later", "Five years later", "five years a fugitive", "fourteen-year-old", "14 at the supper",
    "Hengist's field warlord arc", "Cato kills Hengist", "kills HENGIST",
    "armor repaired", "What is civilization", "WHAT IS CIVILIZATION",
    # S#328 - 00W R-177 sweep of Seasons Two and Three (retired frame wordings)
    "when the mentor is gone", "parentless boy", "raised and named by the convent", "mini him",
    "first stealth infiltration", "FIRST STEALTH INFILTRATION", "not a trained cavalryman",
    "Snape", "Torquemada", "cold, cultured, methodical, cruel",
    "SECOND BEREAVEMENT", "both men who loved her", "nameless veteran", "finally runs out",
    "ARMY (S3)", "S3 ARMY", "the bloody, inconclusive clash",
    # S#328 - Mardin's Sasanian sword: straight, no cross-guard, never a spatha (see the object spec Doc in his folder)
    "curved Sasanian", "curved sword", "the curved sword", "small flat gold guard", "Mardin's spatha", "Mardin’s spatha", "spatha in Mardin",
    # 00W R-178 (6 Sept 2026) ruled the sword's dimensions and steel; the "not ruled" wording of the same morning is retired
    "LENGTH: NOT RULED", "no blade or overall length exists", "not to be borrowed", "Sasanian sword, pattern-welded",
]

def load_live():
    man = json.load(io.open(MAN, encoding="utf-8"))["files"]
    docs = []
    for f in man:
        if not f.get("live"):
            continue
        for lf in f.get("local_files", []):
            if not lf.endswith(".txt") or SKIP_PATH.search(lf):
                continue
            p = os.path.join(CANON, lf)
            try:
                docs.append((lf, io.open(p, encoding="utf-8").read().split("\n")))
            except OSError:
                pass
    return docs

QUOTE = re.compile(r"[\"“]([^\"“”]{5,90})[\"”]")
# quoted fragments that sit on DEAD lines but are live words/lines of dialogue elsewhere (never stragglers by themselves)
HARVEST_IGNORE = {"FIND THEM!", "AT 45", "SIXTY", "S2E01", "HENGIST", "GEWISSAE", "LANCIANUS"}

def harvest_dead(docs):
    phrases = {}
    for name, lines in docs:
        for i, line in enumerate(lines):
            seg = None
            if line.startswith("DEAD (recorded so it cannot return)"):
                seg = line
            else:
                m0 = re.match(r"^\* (.{0,240}?)\s[—-] (DEAD|SUPERSEDED|RETIRED|STRUCK|PURGED)\b", line)
                if m0:
                    seg = m0.group(1)  # only the quoted phrases BEFORE the DEAD marker are dead; what follows is the live value
            if seg:
                for m in QUOTE.finditer(seg):
                    ph = m.group(1).strip()
                    if not re.search(r"[A-Za-z]", ph) or len(ph) < 5:
                        continue
                    # a single token ("HENGIST", "S2E01", "SIXTY") is a legitimate live word elsewhere; only phrases count
                    if len(ph.split()) < 2 or ph.upper() in HARVEST_IGNORE:
                        continue
                    if ph.lower() in ("dead", "superseded"):
                        continue
                    phrases.setdefault(ph, set()).add(name.split("/")[-1][:40] + ":" + str(i + 1))
    return phrases

def norm(s):
    return s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')

def main():
    as_json = "--json" in sys.argv
    docs = load_live()
    dead = harvest_dead(docs)
    all_phrases = {ph: ("dead-list", src) for ph, src in dead.items()}
    for ph in REGISTRY:
        all_phrases.setdefault(ph, ("registry", set()))
    hits = []
    for name, lines in docs:
        for i, line in enumerate(lines):
            nl = norm(line)
            whole_record = bool(RECORD.search(nl))
            # a changelog / header line is a record however long it is
            if re.match(r"\s*([Vv]ersion \d|[vV]\d+\.\d+\s|MASTER EPISODE DOCUMENT|NEW IN v\d|Prior:|WHAT CHANGED|CHANGES IN v|\* .*\s[\u2014-] (ALL |all )?(DEAD|dead|SUPERSEDED|superseded|RETIRED|retired|STRUCK|PURGED|ABOLISHED|QUARANTINED|CUT|KILLED|killed)\b)", nl) or re.match(r"\s*(\d+\.\s*)?[\[(*\-\u2022]?\s*(CLOSED|SUPERSEDED|DEAD|RETIRED|ANSWERED|RECORD|RE-RULED|STRUCK|Kills recorded|KILL:|SUPERSEDED IN PART)\b", nl):
                continue
            # a SHORT line with a record marker is a record line; a LONG line (a Map dossier, a character-file
            # paragraph) is judged per hit, in a window around it - S#328: "the son watching the father" hid for
            # three weeks behind a DEAD word 1,500 characters away on the same line
            if whole_record and (len(nl) <= LONG_LINE or name.split("/")[-1].startswith("00")):
                continue
            if line.startswith("DEAD (recorded so it cannot return)"):
                continue
            for ph, (kind, src) in all_phrases.items():
                pos = nl.find(norm(ph))
                if pos < 0:
                    continue
                if whole_record and RECORD.search(nl[max(0, pos - WINDOW):pos + len(ph) + WINDOW]):
                    continue
                # a NEGATED mention ('never "five years later"', 'no "Gewissae"', 'not "minimal mourning"') is a rule, not a straggler
                before = nl[max(0, pos - 48):pos]
                if re.search(r"\b(never|NEVER|Never|no|NO|not|NOT|Not|nor)\b[^.;:!?]{0,40}$", before):
                    continue
                after = nl[pos + len(ph):pos + len(ph) + 24]
                if re.match(r"[\"')\u201d]?\s*(is out|is dead|are dead|is retired|is gone|was retired|retired)\b", after):
                    continue
                hits.append({"doc": name, "line": i + 1, "phrase": ph, "kind": kind, "text": line.strip()[:220]})
    # version-line defects
    vdefects = []
    for name, lines in docs:
        # the changelog proper is the lowercase "vN.N - date - ..." lines (newest first); a doc's "Version N.N" header
        # line is a different animal and is checked only against the MASTER footer below
        vers = [(i + 1, re.match(r"^v(\d+)\.(\d+)\s+[—–-]\s", l)) for i, l in enumerate(lines)]  # "vN.N — date — ..." only; v1.3.1-style re-numberings and prose starting "v6.0 REBUILD" are skipped on purpose
        vers = [(ln, (int(m.group(1)), int(m.group(2)))) for ln, m in vers if m]
        if len(vers) >= 2:
            nums = [v for _, v in vers]
            dups = sorted({v for v in nums if nums.count(v) > 1})
            if dups:
                vdefects.append({"doc": name, "issue": "duplicate version number(s) " + ", ".join("v%d.%d" % d for d in dups)})
            if max(nums) != nums[0]:
                vdefects.append({"doc": name, "issue": "first version line v%d.%d is not the highest v%d.%d (changelog not newest-first)" % (nums[0] + max(nums))})
        head = next((re.search(r"Version (\d+\.\d+)", l) for l in lines[:6] if re.search(r"Version (\d+\.\d+)", l)), None)
        foot = next((re.search(r"END OF MASTER v(\d+\.\d+)", l) for l in lines[-3:] if "END OF MASTER" in l), None)
        if head and foot and head.group(1) != foot.group(1):
            vdefects.append({"doc": name, "issue": "footer END OF MASTER v%s vs header Version %s" % (foot.group(1), head.group(1))})
        for i, l in enumerate(lines):
            if "[Was:" in l and l.count("[") > l.count("]"):
                vdefects.append({"doc": name, "line": i + 1, "issue": "unclosed [Was: bracket"})
    if as_json:
        print(json.dumps({"dead_phrases": len(dead), "registry": len(REGISTRY), "hits": hits, "version_defects": vdefects}, ensure_ascii=False, indent=1))
        return
    print("canon lint: %d live docs, %d dead-list phrases harvested + %d registry phrases" % (len(docs), len(dead), len(REGISTRY)))
    if not hits and not vdefects:
        print("CLEAN - no straggler found")
        return
    for h in hits:
        print("STRAGGLER  %s:%d  [%s] %r\n           %s" % (h["doc"].replace("18 - Concept Art & Visual References/Characters/", "CH/")[:70], h["line"], h["kind"], h["phrase"], h["text"][:180]))
    for d in vdefects:
        print("VERSION    %s  %s" % (d["doc"].replace("18 - Concept Art & Visual References/Characters/", "CH/")[:70], d["issue"] + (" (line %d)" % d["line"] if "line" in d else "")))
    print("TOTAL: %d straggler hits, %d version defects" % (len(hits), len(vdefects)))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
