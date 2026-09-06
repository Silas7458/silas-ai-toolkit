# -*- coding: utf-8 -*-
# cascade_00W16.py - S#328 (6 Sept 2026): 00W R-177 THE FRAME FOLLOWS THE BUILT HOUR applied to Seasons Two and Three.
# Every S2/S3 frame value (Master + State CENTRAL QUESTION / TURNS, the Series Episode Map dossiers + grid, the S2 Full
# Season Summary, the S3 Episode List / State / One-Pager) was read against the built hours; the splits below are the
# frame docs that had not followed the builds, plus the R-131 / R-175 stragglers the windowed lint surfaced on the way.
#   python cascade_00W16.py dry | all
import sys, os, io, json, importlib.util
spec = importlib.util.spec_from_file_location("w2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cascade_00W2.py"))
src = open(spec.origin, encoding="utf-8").read().split("# ------------------------------------------------------------------ ids")[0]
ns = {}; exec(compile(src, spec.origin, "exec"), ns)
replace_all = ns["replace_all"]; find = ns["find"]; TOTAL = ns["TOTAL"]; EM = ns["EM"]; DRY = ns["DRY"]; gws = ns["gws"]
mirror_text = ns["mirror_text"]

R = "00W R-177"; D6 = "6 September 2026"

MAP = "1RjPbhpWwDliekXVYlFzXI1CNMal4Skey5xGaalm0z8Q"
S2M = "1pu5Qx78pLylAGfgtg2reGJ6rYsxqEENkdrMIT4Eaqsw"
S2S = "1A_-g8NdmZ0hRHmZzs5bLkfar1x5R7s_3je_EUuQwL1k"
S3L = "1Z6XpsPnXO9Msy9vHQUyDKlC2m0FNy3_6MO6dTORC1cg"
S3O = "1myNuetS7FitlzRCL3rGNrDRXu-6R82857twlFXndGKU"
LAUNCH = "1xMbRJdbgodqcWCGtAydXCF9_gENM-Rle3Rbw2Ci9lCY"
BIBLE = "1SaArCJb2HbI8baLQNE2EA3prThQyZUkAjLCkd1EowqM"
OPENQ = "16qiI2TLgnRbbw-jd0IphtVhKgGVT7A6hOezrskVHkn8"
W00 = "1PW6x_Yx4jBuALpjIJquDGeSyP6NOVqRG4eBV-xnPkEI"


# ---------------------------------------------------------------- paragraph replace (by index range, for the long dossiers)
def get_doc(doc_id):
    return gws(["docs", "documents", "get", "--params", json.dumps({"documentId": doc_id})])


def find_paragraphs(doc, prefix):
    hits = []

    def walk(elems):
        for el in elems:
            if "paragraph" in el:
                text = "".join(e.get("textRun", {}).get("content", "") for e in el["paragraph"].get("elements", []))
                if text.startswith(prefix):
                    hits.append((el["startIndex"], el["endIndex"], text))
            elif "table" in el:
                for row in el["table"].get("tableRows", []):
                    for cell in row.get("tableCells", []):
                        walk(cell.get("content", []))
    walk(doc["body"]["content"])
    return hits


def replace_paragraph(doc_id, prefix, new_text, label):
    """Replace the whole text of the ONE paragraph that starts with `prefix` (the trailing newline is kept)."""
    TOTAL["pairs"] += 1
    if DRY:
        t = mirror_text(doc_id)
        n = sum(1 for line in t.split("\n") if line.startswith(prefix))
        print("%-30s DRY paragraph-by-prefix: mirror lines starting with prefix = %d; new text %d chars" % (label, n, len(new_text)))
        if n != 1:
            TOTAL["zeros"].append((label, prefix[:100], n))
        return
    doc = get_doc(doc_id)
    hits = find_paragraphs(doc, prefix)
    if len(hits) != 1:
        raise SystemExit("%s: expected 1 paragraph starting with %r, found %d" % (label, prefix[:60], len(hits)))
    start, end, old = hits[0]
    reqs = [{"deleteContentRange": {"range": {"startIndex": start, "endIndex": end - 1}}},
            {"insertText": {"location": {"index": start}, "text": new_text}}]
    gws(["docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id}), "--json", json.dumps({"requests": reqs}, ensure_ascii=False)])
    TOTAL["changed"] += 1
    print("%-30s paragraph replaced: %d -> %d chars" % (label, len(old.rstrip("\n")), len(new_text)))


# ---------------------------------------------------------------- the two rewritten dossiers (from the built acts, 00M / 00N)
DOS204 = ('Question: What is a life worth ' + EM + ' and what does it bind you to? (Answered in the tag, shown not spoken: a life is worth another life, and it binds you to the ones who paid it ' + EM + ' Africanus, a season on, riding out in a dead man\'s blue.) '
'Who rides (the teaser raid): the SEVEN-RIDER WHITE MANUS ' + EM + ' X Valerius (gold); A/R Felix (a, silver), LANCEANUS (c, orange ' + EM + ' his first ride in Portarius\'s seat and color), Cassian (e, yellow); B/L Ambrosius (b, purple), Dacus (d, red), Maro (f, blue); Mardin the second overwatch; Elen the treeline; Cato (black) holds the fort. '
'Summary: SMASH IN mid-raid ' + EM + ' the abbreviated seven-man Butterfly on a Saxon SLAVE COLUMN bound for the port, the camera riding with LANCEANUS in the ORANGE for the first time (he plants his draco at the A-exit ' + EM + ' the orange howling over a man made somebody); MARO, the old blue, stepping OVER the chained, not through them; ELEN\'s two protective arrows keep the old man alive without his ever knowing; the drovers dead and branded, the coffle freed ' + EM + ' and one freed man does not kneel: he goes straight for a loose Saxon horse and is up and turning it before anyone can stop him. '
'A MAN ON A HORSE ' + EM + ' he answers the founding question (not who are you ' + EM + ' what can you do) by being, visibly, a fighter: a former numerus Maurorum cavalryman, Rome\'s own African light horse of the Wall, a senior man of it by his bearing (the Oenomaus / "Doctore" register ' + EM + ' 00M R-120); his Berber name is one their mouths cannot hold ' + EM + ' Felix and Dacus mangle it twice and he lets "AFRICANUS" stand. THE ASK, decided in the field, moving: his wife and daughter were driven ahead to the port he was bound for, sold, on the next boat out ' + EM + ' the clock is now; someone voices the doubt (not Britons, not ours, and a walled city is everything the Dragons do not do); VALERIUS answers with his own law ' + EM + ' the oath does not say Briton, it says no child ' + EM + ' and ELEN, from the scar: nobody came for her for two years; they are already here. Mardin rides ahead alone to scout the port. '
'THEY NAMED HIM FOR A PLACE ' + EM + ' the approach: Africanus rides LIGHT, the Mauri way (half-standing, a fistful of javelins, a small round shield), and DACUS, the maker of Dragons, sees cavalry to the bone; Mardin\'s recon; THE PLAN ' + EM + ' no cavalry inside walls: FOUR go in by DAYLIGHT in Saxon disguise stripped from the column dead, on Saxon horses ' + EM + ' AMBROSIUS, ELEN, MARO, AFRICANUS ' + EM + ' the rest the mounted net outside the gate. '
'HIDDEN IN DAYLIGHT ' + EM + ' the show\'s first DAYTIME infiltration of a walled, Saxon-held river-port with a slave market (NOT the first stealth hour: 106 was the night Assassin\'s-Creed hour): the four tie the horses close to the gate ' + EM + ' the way out, staged; Elen and Ambrosius go over the sun-warm rooftops; Maro works the ground as a Saxon trader with Africanus at his heel as his bound slave ' + EM + ' the one cover that lets a conspicuous man walk a slave market unquestioned; the dread is exposure, not darkness; they find the pens, the wife and the small girl ' + EM + ' and the lot is being walked to the quay TODAY, so they take them IN MOTION; the alarm goes up across the port. '
'TWO ARROWS TOO LATE ' + EM + ' the running fight to the gate; FOUR SAXON ARCHERS on the wall draw on the escape; Elen drops two; the other two are already loosing at the girl and her mother ' + EM + ' and MARO dives, tackles the child down and under him, and TAKES BOTH ARROWS IN THE BACK; Elen kills the last two archers, which is why she is the first to reach him, and the armor BREAKS ' + EM + ' the first tears we have ever seen from her, cutting tracks through the eye-black; the child alive under him; Maro\'s body across a saddle on the ride away in the grey. '
'THE STEEL REMEMBERS ' + EM + ' the burial under the willow (Gallus\'s, 108), Corvus presiding; LUCIA among the mourners takes the veil beside the 105 nun ' + EM + ' the convent born of cumulative grief, NOT romance (00M R-118: Maro was a brother-friend, never a suitor) ' + EM + ' and ELEN WATCHES HER GO, the fighter watching the woman walk through the other door (the four fates of the era\'s women made legible without a word: the blade, the veil, the water, the ordinary life ' + EM + ' loads the Lady\'s 304 choice); THE SWORD-OF-THE-SEAT SHOWN IN FULL for the first time ' + EM + ' Maro\'s Weyland blade, armor, horse and the BLUE brought to Africanus; he refuses (he never asked a man to die); DACUS gives him the truth of the ritual, LOCKED VERBATIM: "You don\'t remake the steel because you don\'t replace the man. You carry him. Every hand that holds this blade holds every hand that held it before. Take it, and Maro rides on." He takes it; Maro\'s room travels with the seat ' + EM + ' Elen\'s roommate now is Africanus; he lowers himself into Maro\'s section of the red table. '
'THE BLUE RIDES OUT ' + EM + ' the tag, one to two months on, never stated: the daughter running with the other children; Africanus, a season\'s drill in his hands, rides out in Maro\'s blue, the blue draco up and howling, Elen beside him ' + EM + ' the debt made a Dragon. HARD CUT ' + EM + ' a Saxon hall: HENGIST, told the ghosts now walk inside walled cities and pull people out of slave markets in daylight, sends for a specialist: "The ghosts have no faces. Send the one who makes men GIVE him faces." (' + "→" + ' 205.) '
'Battle: front ' + EM + ' the abbreviated seven-man Butterfly on the slave column, open Saxon country; back ' + EM + ' the daytime penetration and running extraction from the walled port (market, pens, quay, rooftops, the gate). Losses ' + EM + ' GAIUS MARO, killed shielding the daughter; the Dragons break their own never-assault-a-hold doctrine (106) by choice, and it costs a founder. '
'Runtime: Teaser 4 ' + "·" + ' One 9 ' + "·" + ' Two 8 ' + "·" + ' Three 14 ' + "·" + ' Four 11 ' + "·" + ' Five 6 ' + "·" + ' Tag 3 = ~55. Turns: the orange rides / a man on a horse / they named him for a place / hidden in daylight / two arrows too late / the steel remembers / the blue rides out. '
'Acts: Teaser ("The orange rides again") ' + "·" + ' One ("A man on a horse") ' + "·" + ' Two ("They named him for a place") ' + "·" + ' Three ("Hidden in daylight") ' + "·" + ' Four ("Two arrows too late") ' + "·" + ' Five ("The steel remembers") ' + "·" + ' Tag ("The blue rides out"). '
'Refines: Elen (the armor cracks ' + EM + ' her first grief; the freed reaching the freed; loads 209) ' + "·" + ' Africanus (freed ' + "→" + ' bound ' + "→" + ' Dragon; Rome\'s African horse, the real man among the myth-seeds) ' + "·" + ' Ambrosius (earned command in a quiet key ' + EM + ' the patient infiltration; ' + "→" + ' 207/208) ' + "·" + ' Valerius (bends the doctrine for the law he wrote) ' + "·" + ' Lanceanus (the orange\'s first ride; the hero plant at the A-exit). '
'Plants: Africanus + the blue ' + "→" + ' S3 and the Final Season ' + "·" + ' Elen and Africanus roommates (the seat travels as a whole life) ' + "·" + ' the convent, FOUNDED here ' + "→" + ' grief\'s home in S3, and the road not taken that makes the Lady\'s 304 walk a CHOICE ' + "·" + ' the port penetrated ' + "→" + ' Hengist sends the wolf (205) ' + "·" + ' Africanus\'s Mauri speed ' + "→" + ' the Cato/Africanus (f)-slot swap (205' + "–" + '206). '
'Pays: 202\'s sword-of-the-seat ("shown in full at 204") ' + "·" + ' the "sold overseas" clock (102/103) at the quay ' + "·" + ' "not who are you ' + EM + ' what can you do" (101/103) in its purest form ' + "·" + ' the Lex Innocentium (110) proven UNIVERSAL ' + EM + ' a foreign woman and child ' + "·" + ' Maro as Elen\'s safe roommate / "little warrior" (110) ' + "·" + ' Elen\'s teaser arrows saving Maro, paid off cruelly at the wall. '
'Rewatch detonation [P]: in Act Three Maro quietly steadies the frightened daughter ' + EM + ' on rewatch, he had already chosen her. Census after 204: ~84 ' + "→" + ' ~86 (+3: Africanus, wife, daughter; ' + "−" + '1: Maro). Sword-pass: Gaius Maro ' + "→" + ' Africanus (+ horse, armor, room and the blue). '
'Rulings folded (00M): R-118 Maro removed from the Lucia triangle; R-119 the seven-man is the standing Manus (the 204+ lineup; Cato held/rotating; the Cato' + "↔" + 'Africanus (f) swap until Africanus is trained); R-120 Africanus = numerus Maurorum. '
'Recorded (dead): "the first stealth infiltration" (106 was the night one); "an African warrior ' + EM + ' a horseman but not a trained cavalryman"; "Lucia\'s second bereavement ' + EM + ' both men who loved her"; the "12-episode numbering" ' + EM + ' the season stays TEN. [Dossier rewritten from the built acts 6 Sept 2026 ' + EM + ' ' + R + ', the frame follows the built hour.]')

DOS205 = ('Question: How do you fight an enemy who doesn\'t need to beat you in the field? (Answered in the tag, shown not spoken: you can\'t, not with the sword ' + EM + ' he wins by making the people you saved afraid they were ever saved; the ghost that was hope becomes a curse, and the one man who understands the wolf can\'t reach him from a saddle.) '
'Positioning: the anti-201 ' + EM + ' 201 was the flawless machine; 205 is the machine meeting the one problem it can\'t solve; MARDIN\'s hour; register DREAD, not spectacle. THE ANTI-CYMOD KEY (00N): Wulfhere is the Dragons\' own iron discipline WITH THE CODE CUT OUT ' + EM + ' the Dragons are necessary monsters BOUND by the Lex Innocentium, NOT merciful but LAWFUL; his black knights hold the same discipline with no law at all. THE WULFHERE KEY (00N R-123, the anti-Landa lock): cold, courteous, EMPTY ' + EM + ' the Charles Dance / Tywin Lannister register, the banality of evil, an Eichmann with a sword-arm; his refinements are METHOD, not charm (the rare wine loosens a tongue better than water; the courtesy calms a man into talking); no wit, no games, no relish; the audience wants him dead in every frame; he never gets a cool win and does not die for his men. '
'Summary: THE LEDGER AND THE CUP OF WINE ' + EM + ' a Briton village at first light, wrong: no fire, no plunder; black-armored riders in disciplined ranks, WAITING, while at a plain table dragged into the mud WULFHERE pours a measure of genuinely rare wine for an old villager and asks about "the riders with the dragon heads" the way a clerk asks about a debt ' + EM + ' the big one\'s voice, the sun behind them or in their faces; the defiance does not interest him; a nod to the knight behind the chair, and while the first scream climbs he corrects a misspelling in his ledger and nudges the wine an inch closer; beneath a neat column of other men\'s agonies he writes one word: west. '
'I WAS TRAINED IN THAT SAME DARKNESS ' + EM + ' the Sanctuary (post-204: Africanus riding the blue); a runner with news the wrong shape ' + EM + ' a protected village questioned, nothing taken, nothing burned; Lanceanus: "That\'s not a raid. What is that?"; MARDIN goes still ' + EM + ' SPLASH-BACK to the eastern den (00N; the 107 seam deepened): a master\'s hand pushing a coiled whip toward a younger Mardin, his hand NOT closing on it, then his own back and the lashes ' + EM + ' "I was trained oceans away, in this darkness, in the same type of den that makes them ' + EM + ' they wanted to hand me their whip. I took the lashes instead. That\'s why I\'m here and not there."; the unwinnable shape ' + EM + ' the anti-triangulation doctrine (103) beaten not by a tracker but by torture and patience: "You cannot scare a man already comfortable with screaming. And you cannot charge a map."; they ride anyway ' + EM + ' you do not leave your people under the pliers while you theorize; and Mardin, who has faced everything, looks AFRAID as the gate closes. '
'THE BOY GIVES HIM A THREAD ' + EM + ' intercut, the method in full: no looting, no rape, ranks dressed ' + EM + ' Cymod with the law cut out; among the bound THE BOY FROM 203, who knows the Dragons have no faces and has nothing that can hurt them ' + EM + ' except a voice, a laugh, the way one of them prays, the direction they vanished; Wulfhere sits with him last, patient as weather, and the child breaks on the smallest kindness: "...west. They come from the west. The deep woods."; he writes it, feels nothing, orders the mount; a rider is already away with the sealed ledger-copy; the Dragons crest the ridge ' + EM + ' and the village is empty OF HIM. '
'THE HUNTER SEES HIS GHOSTS ' + EM + ' THE INTERCEPTION: the Dragons run the column down in open country and hit it, and for the first time WULFHERE SEES THEM ' + EM + ' the thing itself, better than his own elite knights ' + EM + ' and for one beat forgets to run, watching the way a collector watches a specimen he means to pin; then the hardest, bloodiest fight the Dragons have ever had, because these knights DO NOT SHATTER ' + EM + ' they take the first cut and RE-FORM and have to be killed to the last man; real wounds, a horse down, Africanus fighting for his life in the new blue beside Ambrosius ' + EM + ' every black knight dies and EVERY DRAGON RIDES HOME; and it means nothing, because in the melee the one man who matters wheels and is gone ' + EM + ' he spends his guard and rides, still cataloguing over his shoulder; VALERIUS, winded, the rasp of a wound two years healed (110): "...where\'s the man?" '
'TOTAL WIN, TOTAL LOSS ' + EM + ' the abandoned interrogation ground, the fine cup of wine still standing on the plain table; Mardin reads the whole shape off that one genteel object: "We won everything on that field. And it was worth nothing. He already spent us."; and the wound that doesn\'t close ' + EM + ' the villagers WON\'T LOOK AT THEM; a woman pulls her children back; an old man they fed all winter turns his face to the wall: TO BE KNOWN TO THE DRAGONS IS NOW A DEATH SENTENCE ' + EM + ' the mark has a third meaning (terror to the enemy, hope to the enslaved, a CURSE to the protected); the boy can\'t meet Ambrosius\'s eyes ' + EM + ' the 203 flinch grown permanent. '
'THREE FORESTS, WRONG FIRST ' + EM + ' Wulfhere, lamplit, transcribes a second fair copy for Hengist, a third locked in the case at his elbow; then the map of western Britain, his fragments read like reconciled accounts ' + EM + ' and "the deep woods" in the west is THREE great forests: ARDEN, SELWOOD, and, last and least, the DEAN; he taps Arden first ' + EM + ' the obvious one, the wrong one; the Dean he barely marks; the only reason the Sanctuary lives two more years (00N R-128/R-129 ' + EM + ' the clock that holds his death to 304 and the discovery to 309). OLDER MARDIN, the hour\'s only narration: "He learned the word \'west\' the day he broke a child. He would spend the next two years learning which west ' + EM + ' and we would spend them not knowing he was counting. Killing him, when it finally came, would not call the ledger back. This was the night the noose was tied. It closed a long way off." HARD CUT ' + EM + ' the Sanctuary at dawn, garlands going up, a wedding being planned (' + "→" + ' 206). '
'Battle: WHY ' + EM + ' a village under the Dragons\' protection interrogated to death by black knights hunting the ghost riders; WHERE ' + EM + ' NOT a field of Wulfhere\'s choosing: the Dragons INTERCEPT his contingent on the ride home, in open country; WHAT THEY GET ' + EM + ' the village freed and, for the first time, a clean kill on disciplined heavy horse (every black knight in the contingent dead) ' + EM + ' but Wulfhere cuts free in the melee and his ledger-copy left an hour before a sword was drawn: total on the field, worthless in the war. Losses ' + EM + ' NO DRAGON KILLED; the loss is strategic ' + EM + ' the anonymity that kept them alive is now the thing killing the people they protect, and the wolf has SEEN them. '
'Runtime: Teaser 4 ' + "·" + ' One 11 ' + "·" + ' Two 12 ' + "·" + ' Three 15 ' + "·" + ' Four 9 ' + "·" + ' Tag 3 = ~54. Turns: the ledger and the cup of wine / I was trained in that same darkness / the boy gives him a thread / the hunter sees his ghosts / total win, total loss / three forests, wrong first. '
'Acts: Teaser ("The ledger and the cup of wine") ' + "·" + ' One ("I was trained in that same darkness") ' + "·" + ' Two ("The boy gives him a thread") ' + "·" + ' Three ("The hunter sees his ghosts" ' + EM + ' the interception) ' + "·" + ' Four ("Total win, total loss") ' + "·" + ' Tag ("Three forests, wrong first"). '
'Refines: Mardin (the man who refused his own making ' + EM + ' his 106/107 past made load-bearing without making him a former torturer) ' + "·" + ' Wulfhere (the season\'s true antagonist, fully keyed) ' + "·" + ' Valerius ("where\'s the man?" ' + EM + ' the 110 scar referenced, not reopened) ' + "·" + ' Africanus (the new blue tested against real heavy cavalry). '
'Pays: the anti-triangulation doctrine (103) ' + "·" + ' masks-even-at-camps (the camps hold voices, kindnesses, habits, never faces ' + EM + ' exactly what he harvests) ' + "·" + ' 102\'s brand doctrine (a third term) ' + "·" + ' 203\'s boy (hope ' + "→" + ' flinch ' + "→" + ' the break) ' + "·" + ' 204\'s tag ("send the one who makes men give him faces") ' + "·" + ' the 201/202 noose (the country waking ' + "→" + ' the wolf is what it wakes into). '
'Plants: the LEDGER + COPIES ' + "→" + ' the finding of the Sanctuary at 309 (killing him at 304 does NOT undo it) ' + "·" + ' the three-forests uncertainty ' + "→" + ' the S3 clock ' + "·" + ' the black knights as a recurring disciplined-heavy-horse foil (he replenishes; the 303 knights are a later force) ' + "·" + ' the people fearing the mark ' + "→" + ' 209\'s dark side. '
'Rewatch detonation: the rare wine, the "thank you," the ledger correction mid-scream; the boy\'s "west... the deep woods" as the first line of the Sanctuary\'s death warrant. Census after 205: ~86 ' + "→" + ' ~86 (freed villagers to the camps). '
'Recorded (dead ' + EM + ' 00N): the "Snape / Torquemada / Templar-eradicator, cruel" key; the "cup of water"; "the clash is bloody and inconclusive" as the battle (it is an interception ' + EM + ' total on the field, worthless in the war); "Teaser: Hengist dispatches the specialist" (that beat is 204\'s tag); the old "lesser name" subplot. [Dossier rewritten from the built acts 6 Sept 2026 ' + EM + ' ' + R + ', the frame follows the built hour.]')

GRID205 = ('FULL BUILD (25 Aug 2026, 00N) ' + EM + ' the ledger and the cup of rare wine; Mardin knows the den that made him (offered the whip, took the lashes); the 203 boy breaks on a kindness ' + EM + ' "west... the deep woods"; the INTERCEPTION ' + EM + ' every black knight killed, no Dragon dies, WULFHERE escapes; the villagers won\'t look at their protectors; three forests, wrong first (Arden before Selwood before the Dean ' + EM + ' the S3 clock)')

# ---------------------------------------------------------------- 00W record
W_RECORD = ('R-177 APPLIED TO SEASONS TWO AND THREE (S#328, 6 Sept 2026, Brother ' + EM + ' no question to the author, per the ruling). METHOD: every S2/S3 frame value (the Master\'s and the State\'s CENTRAL QUESTION / BATTLE / TURNS lines, the Series Episode Map\'s per-episode Question ' + "·" + ' Summary ' + "·" + ' Acts dossiers and status grid, the S2 Full Season Summary, the S3 Episode List\'s SEASON IDENTITY / HEARTBEAT / QUESTION, the S3 State ' + "§" + '1' + "–" + "§" + '3, the S3 One-Pager) was read against the built hours. SEASON TWO ' + EM + ' the five built hours (201' + "–" + '205) agree with their own CENTRAL QUESTION and TURNS in the Master and the State: those lines were written with the builds, and nothing moves. The splits were all in frame docs that had not followed the builds: (1) the SERIES EPISODE MAP\'s 204 and 205 dossiers still carried the pre-build skeletons ("the first stealth infiltration... a horseman but not a trained cavalryman... Lucia\'s second bereavement, both men who loved her"; "Snape / Torquemada... the clash is bloody and inconclusive... Teaser: Hengist dispatches the specialist") although the Map\'s own v14 line claimed the 204 dossier had moved to BUILT ' + EM + ' both dossiers and the 205 grid row are rewritten from the built acts (00M, 00N); (2) the Map\'s 207 question read "when the mentor is gone" (its v15 patch) while the Master and the State had read "when the man who made him is gone" since v4.9 (19 Aug) ' + EM + ' the Map now follows the Master; (3) the Map\'s 201 and 202 dossiers still said "the son watching the father" (the retired father/son framing, 00L) in two places the line-level lint could not see because those lines also carry a DEAD-list word ' + EM + ' now the pupil watching the master; (4) the Map still called Galaad "the parentless boy... his \'mini him\'" (206 dossier), "the parentless boy who becomes Galaad Castus" (110 dossier, the love-threads line) and "a parentless boy of the fifty raised and named by the convent" (the S3 curtain-up) beside the R-131 citation ' + EM + ' now Felix Younger, his own man, one of the fifty; the 206 grid row\'s "FELIX\'S boy" likewise; (5) the Map\'s 101 dossier still "sets the two-season belief that Valerius is Arthur" ' + EM + ' seventeen episodes, a season and a half (00W R-166 wave); (6) the Map\'s Season Two end state and the CHARACTER BIBLE\'s Weyland entry still had Weyland "forge the memorial" ' + EM + ' he re-hilts Gallus\'s spatha (R-175); (7) the S2 FULL SEASON SUMMARY\'s 205 entry still described the battle as "a first, bloody, INCONCLUSIVE clash" and his death as "~S3E4" ' + EM + ' now the interception (00N R-122) and 304; (8) the S2 Master\'s BUILD STATE block and the Summary\'s and Map\'s build-state lines still read "201' + "–" + '204 built; 205' + "–" + '206 act-broken", and the Master\'s 6-Aug REVAMP CAVEAT still said "only the merged E2 act-compression remains" ' + EM + ' now 201' + "–" + '205 FULL BUILDS, 206 act-broken and runtime-mapped, 207' + "–" + '210 outcomes locked, the caveat closed as a record; (9) the WRITERS\' ROOM LAUNCH PROMPT\'s 205 line and the open-questions doc\'s Wulfhere item 3 still carried the Snape key ' + EM + ' bracketed to 00N. SEASON THREE ' + EM + ' nothing is act-broken, so there is no built hour for the frame to follow; the sweep is the frame docs against each other and the rulings: (10) the S3 EPISODE LIST\'s own title line still read SEASON THREE ' + EM + ' "THE ARMY" and its SEASON IDENTITY still read "S1 SURVIVAL -> S2 RESISTANCE -> S3 ARMY" against its own header delta (00E R-59: S3 is WAR; the ARMY is the Final Season\'s) ' + EM + ' now WAR; (11) the S3 ONE-PAGER\'s body still carried "ARMY (S3)", "one nameless veteran dies first", "FELIX\'s death pays off his name ' + EM + ' \'Lucky\' finally runs out", "ONLY SEBASTIAN DACUS survives", "only Sebastian Dacus remains", S3-O-07 "Felix\'s death beat", and the S2-insert paragraph\'s "FIRST STEALTH INFILTRATION... not a trained cavalryman" ' + EM + ' each bracketed to the ruling that retired it (00E R-53, 00K R-111d, 00M R-120); the One-Pager remains a July identity doc read through its delta header. The S3 season question (WHAT HAPPENS WHEN THE LAW GETS POWER?) and the HEARTBEAT agree across the List, the State, the Map and the One-Pager; nothing moves. NOTHING HERE IS AUTHOR CANON: ages, dates, names and deaths are untouched; the record values live in this paragraph and in each doc\'s changelog. LINT: the retired wordings above were added to the registry, and the lint now tests a long line (over 500 characters ' + EM + ' the Map\'s dossiers, the character-file prose) for a record marker only within a window around the hit instead of skipping the whole line, which is how (3), (4) and (6) had hidden; the 00-series rulings docs and the character files\' section-12 DEAD bullets stay whole-line records.')

# ---------------------------------------------------------------- SERIES EPISODE MAP
replace_paragraph(MAP, "Question: What is a life worth, and what does it bind you to? Summary: a Manus raid on a slave column", DOS204, "MAP 204 dossier")
replace_paragraph(MAP, "Question: How do you fight an enemy who doesn't need to beat you in the field? Summary: HENGIST, enraged", DOS205, "MAP 205 dossier")
replace_all(MAP, [
    ("Version 17 " + EM + " 5 September 2026, latest " + "·",
     "Version 18 " + EM + " " + D6 + " " + "·" + " " + R + " SWEEP OF SEASONS TWO AND THREE (the frame follows the built hour): the 204 and 205 dossiers and the 205 grid row rewritten from the built acts (00M, 00N " + EM + " they had regressed to the pre-build skeletons); 207's question follows the Master (\"the man who made him\"); \"the son watching the father\" " + "→" + " the pupil watching the master (201, 202); Galaad = Felix Younger, his own man, one of the fifty (00O R-131) in the 110 dossier, the love-threads line, the 206 dossier and row, and the S3 curtain-up; 101 sets a seventeen-episode belief; Weyland re-hilts the memorial (R-175); the S2 build-state line (201" + "–" + "205 FULL BUILDS). Prior: Version 17 " + EM + " 5 September 2026, latest " + "·"),
    ("201" + "–" + "204 are FULL BUILDS; 205" + "–" + "206 act-broken and runtime-mapped; 207" + "–" + "210 author-locked outcomes awaiting act staging. Governing: S2 Master v4.11; S2 State v2.11; S2 Full Season Summary v7.1 (rebuilt 20 Aug)",
     "201" + "–" + "205 are FULL BUILDS (205 built 25 Aug, 00N); 206 act-broken and runtime-mapped; 207" + "–" + "210 author-locked outcomes awaiting act staging. Governing: S2 Master v4.15; S2 State v2.14; S2 Full Season Summary v7.3"),
    ("ACTS BROKEN " + EM + " HENGIST dispatches WULFHERE the Inquisitor + his black knights; he tortures the villages for voices, not faces; the bloody, inconclusive clash; the noose begins to tighten (his intel dooms the Sanctuary)", GRID205),
    ("FELIX'S woman and FELIX'S boy", "FELIX'S woman and FELIX YOUNGER " + EM + " Galaad, his own man, a mirror not a ward (00O R-131)"),
    ("204 " + EM + " \"THE DRAGON DEBT\" (Africanus) (working title, author 18 Aug) " + "·" + " ACTS BROKEN " + EM + " Teaser + 5 acts + Tag " + "·" + " ~55 min",
     "204 " + EM + " \"THE DRAGON DEBT\" (Africanus) (working title, author 18 Aug) " + "·" + " FULL BUILD (20 Aug 2026, 00M) " + EM + " Teaser + 5 acts + Tag " + "·" + " ~55 min " + "·" + " NO NARRATOR"),
    ("205 " + EM + " \"THE WOLF AND THE DRAGON\" (Wulfhere) (working title, author 18 Aug) " + "·" + " ACTS BROKEN " + EM + " Teaser + 4 acts + Tag " + "·" + " ~54 min",
     "205 " + EM + " \"THE WOLF AND THE DRAGON\" (Wulfhere) (working title, author 18 Aug) " + "·" + " FULL BUILD (25 Aug 2026, 00N) " + EM + " Teaser + 4 acts + Tag " + "·" + " ~54 min " + "·" + " one narrator beat (the tag)"),
    ("FELIX taking an interest in the parentless boy who becomes GALAAD CASTUS " + EM + " his \"mini him,\" devout, brave, strong, fast, who will earn the seat on his own merit (00O R-131: not his protégé)",
     "FELIX RECOGNIZING HIMSELF in a young Dragon who becomes GALAAD CASTUS " + EM + " FELIX YOUNGER, his own man, a mirror not a ward (never a boy, never \"his mini him\" " + EM + " 00O R-131): devout, calculated, brave, strong, fast, at war with his own violence and faith, who will earn the seat on his own merit at 306"),
    ("Question: What happens when the mentor is gone?", "Question: What happens when the man who made him is gone?"),
    ("(the son watching the father; the 207 plant)", "(the pupil watching the master; the 207 plant)"),
    ("Ambrosius (the son watching the father lose; the first look at Lanceanus)", "Ambrosius (the pupil watching the master lose; the first look at Lanceanus)"),
    ("a parentless boy of the fifty raised and named by the convent; FELIX YOUNGER, no one's protégé (00O R-131)",
     "one of the fifty; FELIX YOUNGER " + EM + " his own man, no one's protégé and not a child the convent raised (00O R-131)"),
    ("VITELLIUS LANCEANUS and the parentless boy who becomes GALAAD CASTUS.", "VITELLIUS LANCEANUS and the young man who becomes GALAAD CASTUS (Felix Younger, his own man " + EM + " 00O R-131)."),
    ("Lucia; the parentless boy who becomes Galaad Castus.", "Lucia; the young man who becomes Galaad Castus (his own man " + EM + " 00O R-131)."),
    ("sets the two-season belief that Valerius is Arthur", "sets the seventeen-episode belief (a season and a half, 101 to 207) that Valerius is Arthur"),
    ("Weyland forges the memorial;", "Weyland re-hilts Gallus's spatha as the memorial (00W R-175);"),
], "SERIES EPISODE MAP")

# ---------------------------------------------------------------- S2 MASTER
replace_all(S2M, [
    ("MASTER EPISODE DOCUMENT " + EM + " Version 4.14 " + EM + " 5 September 2026 " + "·",
     "MASTER EPISODE DOCUMENT " + EM + " Version 4.15 " + EM + " " + D6 + " " + "·" + " " + R + " SWEEP (the frame follows the built hour): every CENTRAL QUESTION and TURNS line read against its built acts " + EM + " 201" + "–" + "205 agree, nothing moves; the BUILD STATE block brought to the built reality (201" + "–" + "205 FULL BUILDS; 206 act-broken and runtime-mapped; the 6-Aug revamp caveat closed as a record). Prior: Version 4.14 " + EM + " 5 September 2026 " + "·"),
    ("(FULL BUILD 20 Aug 2026), 205, 206.",
     "(FULL BUILD 20 Aug 2026), 205 “The Wolf and the Dragon” (FULL BUILD 25 Aug 2026 " + EM + " 00N). ACT-BROKEN AND RUNTIME-MAPPED (beats, not a full build): 206 “The Dragon Festival”."),
    ("[REVAMP CAVEAT [A " + EM + " 6 Aug]:",
     "[REVAMP CAVEAT " + EM + " CLOSED as a record (the swap and the 202 act-compression were completed 16 Aug 2026; the BUILD STATE line above is current " + EM + " " + R + " sweep, " + D6 + "). As written 6 Aug [A]:"),
], "S2 MASTER")

# ---------------------------------------------------------------- S2 FULL SEASON SUMMARY
replace_all(S2S, [
    ("Version 7.2 " + EM + " 5 September 2026 " + "·",
     "Version 7.3 " + EM + " " + D6 + " " + "·" + " " + R + " sweep: the 205 entry follows the built hour (00N " + EM + " the INTERCEPTION: every black knight killed, no Dragon dies, Wulfhere escapes; killed at 304); the build-state line (201" + "–" + "205 built). Prior: Version 7.2 " + EM + " 5 September 2026 " + "·"),
    ("So the Dragons ride out to stop him; the BATTLE is a first, bloody, INCONCLUSIVE clash that proves he cannot be scared off like a Saxon warband. He is the noose tightening.",
     "So the Dragons ride out to stop him " + EM + " and INTERCEPT his contingent on the ride home, in open country: the hardest, bloodiest fight they have ever had, because black knights do not shatter; every black knight dies, NO Dragon dies " + EM + " and WULFHERE cuts free in the melee and rides, his ledger-copy gone ahead an hour before a sword was drawn. Total on the field, worthless in the war (00N R-122). The people they free will not look at them: to be known to the Dragons is now a death sentence. He is the noose tightening " + EM + " and that night he weighs three forests, Arden first and the Dean last, which is why the Sanctuary lives two more years."),
    ("(killed ~S3E4)", "(killed at 304)"),
    ("BATTLE: the first, inconclusive clash with Wulfhere and the black knights.",
     "BATTLE: the interception of Wulfhere's returning contingent " + EM + " every black knight killed, no Dragon lost, Wulfhere escapes; strategically worthless (the ledger left first)."),
    ("BUILD STATE: 201, 202, 203, 204 are FULLY BUILT TO ACTS (see the S2 Master v4.11 / S2 State v2.11); 205" + "–" + "206 act-broken and runtime-mapped;",
     "BUILD STATE: 201, 202, 203, 204, 205 are FULLY BUILT TO ACTS (see the S2 Master v4.15 / S2 State v2.14); 206 act-broken and runtime-mapped;"),
], "S2 SUMMARY")

# ---------------------------------------------------------------- S3 EPISODE LIST
replace_all(S3L, [
    ("Version 4.3 " + EM + " 5 September 2026 " + "·",
     "Version 4.4 " + EM + " " + D6 + " " + "·" + " " + R + " sweep: the title line and SEASON IDENTITY follow the season's word " + EM + " WAR, not THE ARMY (00E R-59; the header delta had said so since 28 July while the body still read ARMY). Prior: Version 4.3 " + EM + " 5 September 2026 " + "·"),
    ("SEASON THREE " + EM + " \"THE ARMY\" (working)", "SEASON THREE " + EM + " \"WAR\" (working) [00E R-59; \"THE ARMY\" is the Final Season's word]"),
    ("SEASON IDENTITY: the guerrilla band becomes an ARMY.", "SEASON IDENTITY: the guerrilla band goes to open WAR [00E R-59 " + EM + " the true army belongs to the Final Season]."),
    ("ARMY. QUESTION: what happens when the law GETS power?", "WAR [00E R-59]. QUESTION: what happens when the law GETS power?"),
], "S3 EPISODE LIST")

# ---------------------------------------------------------------- S3 ONE-PAGER
replace_all(S3O, [
    ("Version 1.3 " + EM + " 28 July 2026 " + EM + " SURGICALLY AMENDED PER 00E",
     "Version 1.4 " + EM + " " + D6 + " " + EM + " " + R + " sweep: the body's remaining July frame values bracketed to the rulings that retired them (ARMY (S3) " + "→" + " WAR, R-59; the nameless veteran and \"Lucky finally runs out\", R-53 / R-111d; \"only Dacus survives\", R-111d; S3-O-07; the S2-insert paragraph's stealth infiltration / untrained horseman, 00M R-120). Prior: Version 1.3 " + EM + " 28 July 2026 " + EM + " SURGICALLY AMENDED PER 00E"),
    ("The guerrilla band finally becomes an ARMY", "The guerrilla band finally goes to open WAR [was: becomes an ARMY " + EM + " 00E R-59]"),
    ("SURVIVAL (S1) -> RESISTANCE (S2) -> ARMY (S3).", "SURVIVAL (S1) -> RESISTANCE (S2) -> WAR (S3) -> ARMY (the Final Season) [00E R-59]."),
    ("  - *** ONLY SEBASTIAN DACUS survives to the end of S3 *** " + EM + " the last", "  - *** ONLY SEBASTIAN DACUS still RIDES at the end of S3 *** [Felix LIVES, retired at 306 " + EM + " 00K R-111d] " + EM + " the last"),
    ("    living legacy man of Valerius's day, carried forward.", "    legacy man of Valerius's day in the saddle, carried forward."),
    ("  - Start early: one nameless veteran dies first, replaced by one of", "  - [SUPERSEDED 00E R-53 " + EM + " every veteran is named; Cato falls first, at 302] Start early: one nameless veteran dies first, replaced by one of"),
    ("  - FELIX's death pays off his name " + EM + " \"Lucky\" finally runs out. Maximum", "  - [DEAD " + EM + " 00K R-111d: Felix LIVES; \"Lucky\" does not run out, he walks away with it] FELIX's death pays off his name " + EM + " \"Lucky\" finally runs out. Maximum"),
    ("  Dacus remains of Valerius's day.", "  Dacus remains of Valerius's day in the saddle (Felix lives, retired since 306 " + EM + " 00K R-111d)."),
    ("S3-O-07. Felix's death beat and its ironic timing.", "S3-O-07. RE-RULED 00K R-111d " + EM + " Felix LIVES (wounded at 306, retires, the living pass to Galaad); the exact wound, the ceremony and its timing still to build. [was: Felix's death beat and its ironic timing.]"),
    ("1. THE CLANDESTINE RESCUE / AFRICANUS ARC [A] " + EM, "1. THE CLANDESTINE RESCUE / AFRICANUS ARC [A; as raised " + EM + " BUILT at 204 (00M): the first DAYTIME infiltration of a walled port, 106 the night hour; Africanus a former numerus Maurorum cavalryman, R-120] " + EM),
], "S3 ONE-PAGER")

# ---------------------------------------------------------------- WRITERS' ROOM LAUNCH PROMPT
replace_all(LAUNCH, [
    ("[updated 21 Aug 2026 " + EM + " Season Two build-out: episodes 205" + "–" + "210]", "[updated " + D6 + " (205 built, 00N) " + "·" + " 21 Aug 2026 " + EM + " Season Two build-out: episodes 205" + "–" + "210]"),
    ("- 205 \"THE WOLF AND THE DRAGON\" (Wulfhere). HENGIST dispatches WULFHERE",
     "- 205 \"THE WOLF AND THE DRAGON\" (Wulfhere) [BUILT 25 Aug 2026 " + EM + " 00N supersedes the line that follows: Tywin / anti-Landa register, cold, courteous, EMPTY; the battle is the INTERCEPTION " + EM + " every black knight killed, no Dragon dies, Wulfhere escapes; killed at 304]. As launched: HENGIST dispatches WULFHERE"),
], "LAUNCH PROMPT")

# ---------------------------------------------------------------- CHARACTER BIBLE (Weyland entry, R-175)
replace_all(BIBLE, [
    ("Version 0.7 " + EM + " 5 September 2026, later " + EM, "Version 0.8 " + EM + " " + D6 + " " + EM + " the Weyland entry re-hilts the memorial (00W R-175 " + EM + " the v0.7 pass had missed it). Prior: Version 0.7 " + EM + " 5 September 2026, later " + EM),
    ("Lives through S3; forges the memorial Excalibur before the exodus;", "Lives through S3; re-hilts Gallus's Weyland spatha to the Commander's gold as the memorial Excalibur before the exodus (00W R-175 " + EM + " not new steel);"),
], "CHARACTER BIBLE")

# ---------------------------------------------------------------- CONSOLIDATED OPEN QUESTIONS (Wulfhere item 3, superseded by 00N)
replace_all(OPENQ, [
    ("DOES HE ENJOY IT? \"Cruel\" is ruled; appetite is not.", "[SUPERSEDED 00N R-123 " + EM + " the Tywin register: cold, courteous, EMPTY; no appetite, no relish, no games] DOES HE ENJOY IT? \"Cruel\" is ruled; appetite is not."),
], "OPEN QUESTIONS (Wulfhere 3)")

# ---------------------------------------------------------------- 00W record
replace_all(W00, [("END OF 00W.", W_RECORD + "\nEND OF 00W.")], "00W record")

print("TOTAL pairs=%d changed=%d zeros=%d" % (TOTAL["pairs"], TOTAL["changed"], len(TOTAL["zeros"])))
for z in TOTAL["zeros"]:
    print("  ", z)
