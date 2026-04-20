#!/usr/bin/env python3
"""Build companion documents derived from the One Point Hospice Eligibility
Resource Flip Book. The flip book itself is already in the notebook
(source_id f889ce93...). These companions extract and promote the
high-value frameworks and scales that would otherwise be hidden inside
the scanned PDF.
"""

from __future__ import annotations

import asyncio, json, re, subprocess, sys
from pathlib import Path
from playwright.async_api import async_playwright

DRIVE_FOLDER_ID = "1zL6M_LdPtP52OyJNH0q0dy-j5PCg8z4u"
OUT_DIR = Path("flipbook-companion-pdfs")
OUT_DIR.mkdir(exist_ok=True)

CSS = """
<style>
@page { size: Letter; margin: 0.6in; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt; line-height: 1.5; color: #222; }
h1 { font-size: 20pt; color: #1a3a52; border-bottom: 3px double #1a3a52; padding-bottom: 6px; margin: 0 0 6pt 0; }
h2 { font-size: 13pt; color: #1a3a52; border-bottom: 1px solid #c0c8d0; padding-bottom: 3px; margin-top: 16pt; }
h3 { font-size: 11.5pt; color: #2a4a62; margin-top: 10pt; }
.meta { font-size: 10pt; color: #555; font-style: italic; margin-bottom: 10pt; }
.tag { display: inline-block; background: #e8eef2; color: #1a3a52; padding: 2px 8px; border-radius: 4px; font-size: 9pt; margin-right: 4px; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 10pt; }
th { background: #1a3a52; color: white; padding: 5px 8px; text-align: left; }
td { padding: 4px 8px; border: 1px solid #bbb; vertical-align: top; }
tr:nth-child(even) td { background: #f6f9fb; }
.callout { background: #fff8e6; border-left: 4px solid #d4a017; padding: 8px 12px; margin: 10pt 0; font-size: 10.5pt; }
.path-card { border-left: 5px solid #1a3a52; background: #f2f6f9; padding: 10px 14px; margin: 10pt 0; border-radius: 3px; }
.path-title { font-weight: bold; color: #1a3a52; font-size: 12pt; font-family: Arial, sans-serif; }
.picture { background: #eef5ea; border-left: 4px solid #4a7a3a; padding: 8px 12px; margin: 10pt 0; font-size: 10.5pt; }
.picture-label { font-weight: bold; color: #2d5a1a; font-family: Arial, sans-serif; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.5px; }
ul { margin: 4pt 0 8pt 20pt; } li { margin-bottom: 3pt; }
.source { margin-top: 16pt; padding-top: 8pt; border-top: 1px solid #ccc; font-size: 9pt; color: #666; font-style: italic; }
</style>
"""


def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def render(title, body_html, tag="Companion to flip book"):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">{CSS}</head><body>
<h1>{esc(title)}</h1>
<div class="meta"><span class="tag">{esc(tag)}</span>Companion reference derived from the Hospice Eligibility Resource Flip Book (One Point Hospice). Part of the Amerix Hospice Compliance knowledge corpus.</div>
{body_html}
<div class="source">Source: Hospice Eligibility Resource Flip Book (One Point Hospice). See the original flip book PDF in the Hospice regs Drive folder for the scanned layout and additional context. This companion document promotes key frameworks/scales to searchable first-class references.</div>
</body></html>"""


DOCS = []

# ==========================================================
# 1. FOUR WAYS TO DOCUMENT ELIGIBILITY — THE FRAMEWORK
# ==========================================================
DOCS.append({
    "slug": "Four-Ways-To-Document-Eligibility",
    "title": "Four Ways to Document Hospice Eligibility",
    "body": """
<p><strong>The operational framework for hospice eligibility documentation.</strong> Every hospice admission and recertification falls into one of four paths. Knowing which path a patient is on changes the documentation strategy. Pulled directly from the Hospice Eligibility Resource Flip Book (One Point Hospice, page 21).</p>

<div class="picture">
<div class="picture-label">THE PICTURE-PAINTING PRINCIPLE</div>
Palmetto's LCD framework is already permissive compared to checkbox-style MACs. But even within Palmetto, many hospice patients don't fit a single LCD cleanly. The Four Ways framework gives a disciplined way to pick the right documentation strategy for EACH patient, instead of forcing every patient to meet the same "Perfect Fit" bar. Clinical judgment is explicitly preserved.
</div>

<h2>Path 1 — Perfect Fit</h2>
<div class="path-card">
<div class="path-title">PATH 1 &nbsp; Perfect Fit</div>
<p><strong>When to use:</strong> Patient clearly meets a specific MAC Local Coverage Determination (LCD) guideline for a disease with an LCD (e.g., Palmetto L34544 Liver, L34547 Neurological, L34548 Cardiopulmonary, L34558 AFTT, L34559 Renal, L34567 Alzheimer's).</p>
<p><strong>Documentation posture:</strong> Straight narrative against the specific LCD criteria. Cite the Part 1 core + supporting findings. This is the simplest path — patients whose presentation checks every LCD box.</p>
<p><strong>Caveat:</strong> Perfect-fit patients are the minority. Most real-world patients don't hit every LCD criterion precisely. Do not force Path 1 framing on a patient who actually belongs on Path 2, 3, or 4 — that weakens the record on audit.</p>
</div>

<h2>Path 2 — Close Fit + Rapid Decline</h2>
<div class="path-card">
<div class="path-title">PATH 2 &nbsp; Close Fit + Rapid Decline</div>
<p><strong>When to use:</strong> Patient almost meets an LCD but falls short on one or more specific criteria. However, they demonstrate <em>rapid decline</em> such that a 6-month prognosis is clinically expected.</p>
<p><strong>Documentation posture:</strong> Marshal evidence of rapid decline:</p>
<ul>
<li>Rapid loss of function — declining PPS (document baseline AND follow-up over months)</li>
<li>Rapid weight loss — not due to reversible causes (depression, diuretics)</li>
<li>Frequent office, ED, or hospital visits — cluster of acute-care events over weeks to months</li>
<li>Rapid deterioration in laboratory values — serial labs showing trend</li>
<li>Imaging findings — X-ray or other imaging showing progression</li>
</ul>
<p>The velocity of decline is the documentation focus. See Hospice-Scale-FDR (Functional Decline Rate) and Hospice-Scale-SEV (Symptom Escalation Velocity) for quantified decline metrics.</p>
</div>

<h2>Path 3 — Close Fit + Significant Related Condition</h2>
<div class="path-card">
<div class="path-title">PATH 3 &nbsp; Close Fit + Significant Related Condition</div>
<p><strong>When to use:</strong> Patient almost meets LCD for the primary terminal diagnosis AND has a significant comorbidity that contributes to the 6-month prognosis.</p>
<p><strong>Common significant related conditions:</strong></p>
<ul>
<li>Congestive heart failure</li>
<li>Chronic obstructive pulmonary disease (COPD)</li>
<li>Renal failure</li>
<li>Dementia</li>
</ul>
<p><strong>Documentation posture:</strong> Document the primary diagnosis against the applicable LCD, then explicitly document the comorbid condition's contribution. Not "this patient also has COPD" but "COPD severity is such that it compounds the 6-month prognosis for the primary hospice diagnosis." See Hospice-Scale-CCI (Charlson Comorbidity Index) for a quantified comorbidity-burden anchor.</p>
</div>

<h2>Path 4 — Physician's Clinical Judgment (No Applicable LCD)</h2>
<div class="path-card">
<div class="path-title">PATH 4 &nbsp; Physician's Clinical Judgment</div>
<p><strong>When to use:</strong> No disease-specific LCD exists for the patient's primary terminal illness. Hospice eligibility rests on the CMS Medicare Benefit Policy Manual Ch. 9 general 6-month-prognosis standard, supported by clinical documentation.</p>
<p><strong>Documentation posture:</strong> Document sound medical judgment through:</p>
<ul>
<li>Clinical narrative explaining why the physician believes 6-month prognosis applies</li>
<li>Observable deterioration per the "Other Terminal Illnesses" 11-point checklist (serial physician assessments, multiple ER visits, progressive pressure ulcers, functional decline, systolic BP drop, ADL decline, nausea/vomiting, weight loss, albumin decline, malnutrition with low BMI, disease-processes combination, rest O2 requirement, declined artificial ventilation)</li>
<li>Supporting quantified scales — PPS, ECOG, FAST, BODE, CCI, etc.</li>
</ul>
<p><strong>CMS reminder (footnote in the flip book):</strong> "Per CMS, patients may not meet the LCD guidelines, yet still have a life expectancy of 6 months or less. Coverage of these patients may be approved if documentation of clinical factors supporting a less-than-6-month life expectancy, that is, well-documented written evidence."</p>
</div>

<h2>Deciding which path a patient is on</h2>
<p>At admission and at each recertification, explicitly pick which path best describes this patient. Document that choice in the narrative:</p>
<ol>
<li>Does the patient meet all LCD criteria cleanly? → <strong>Path 1 (Perfect Fit)</strong></li>
<li>If not, do they have an LCD that nearly fits + rapid decline evidence? → <strong>Path 2 (Close + Decline)</strong></li>
<li>If not, do they have an LCD that nearly fits + a significant contributing comorbidity? → <strong>Path 3 (Close + Comorbidity)</strong></li>
<li>If no LCD applies at all, can the physician document sound clinical judgment for 6-month prognosis? → <strong>Path 4 (Clinical Judgment)</strong></li>
</ol>

<div class="callout">
<strong>Audit defense implication:</strong> When an audit challenges eligibility, the clearest defense is to show the specific path you used and the specific evidence marshaled for that path. Patients who were implicitly on Path 2 or 3 but documented as if Path 1 are vulnerable because the LCD criteria aren't all met. Patients explicitly on Path 2, 3, or 4 with appropriate evidence are well-defended because the framework CMS itself allows is being used correctly.
</div>

<h2>Integrations with our broader knowledge corpus</h2>
<ul>
<li><strong>Palmetto LCDs</strong> (governing): support Paths 1, 2, and 3 directly. The Palmetto LCD supporting-findings sections are Path 2 and 3 material.</li>
<li><strong>Cross-MAC Indicator Toolbox</strong>: provides additional brush strokes for Paths 2 and 3 — indicators NGS/CGS recognize even when Palmetto's specific LCD is borderline.</li>
<li><strong>Hospice Assessment Scales</strong>: quantify decline for Path 2 (velocity) and capture baseline burden for Path 3 (CCI for comorbidities, BODE for pulmonary, etc).</li>
<li><strong>Flip Book "Other Terminal Illnesses" checklist</strong>: primary documentation template for Path 4 patients.</li>
</ul>
""",
    "tag": "DOCUMENTATION FRAMEWORK",
})

# ==========================================================
# 2. PAINAD — Pain Assessment in Advanced Dementia
# ==========================================================
DOCS.append({
    "slug": "Hospice-Scale-PAINAD",
    "title": "PAINAD — Pain Assessment in Advanced Dementia",
    "body": """
<p><strong>Summary.</strong> Five-domain observational pain scale for non-communicative patients with advanced dementia. Total score 0-10; each domain scored 0-2. Validated by Warden, Hurley, and Volicer (2003) to detect pain in patients who can no longer self-report. Essential tool in hospice because most advanced-dementia patients cannot reliably complete the Numeric Rating Scale or Wong-Baker FACES.</p>

<h2>Scoring — five domains, each 0-2</h2>
<table>
<tr><th>Domain</th><th>0</th><th>1</th><th>2</th></tr>
<tr><td>Breathing (independent of vocalization)</td><td>Normal</td><td>Occasional labored breathing; short period of hyperventilation</td><td>Noisy labored breathing; long period of hyperventilation; Cheyne-Stokes respirations</td></tr>
<tr><td>Negative vocalization</td><td>None</td><td>Occasional moan or groan; low-level speech with a negative or disapproving quality</td><td>Repeated troubled calling out; loud moaning or groaning; crying</td></tr>
<tr><td>Facial expression</td><td>Smiling or inexpressive</td><td>Sad, frightened, frown</td><td>Facial grimacing</td></tr>
<tr><td>Body language</td><td>Relaxed</td><td>Tense, distressed pacing, fidgeting</td><td>Rigid, fists clenched, knees pulled up, pulling or pushing away, striking out</td></tr>
<tr><td>Consolability</td><td>No need to console</td><td>Distracted or reassured by voice or touch</td><td>Unable to console, distract, or reassure</td></tr>
</table>
<p><strong>Total PAINAD score:</strong> sum of five domains, range 0-10.</p>

<h2>Interpretation</h2>
<table>
<tr><th>Total score</th><th>Interpretation</th></tr>
<tr><td>0</td><td>No observed pain indicators</td></tr>
<tr><td>1-3</td><td>Mild discomfort; monitor; consider low-intensity intervention</td></tr>
<tr><td>4-6</td><td>Moderate pain; intervention indicated</td></tr>
<tr><td>7-10</td><td>Severe pain; immediate/escalated intervention indicated</td></tr>
</table>

<h2>Detailed rubrics (from the flip book, pages 10-14)</h2>

<h3>Breathing patterns</h3>
<ul>
<li><strong>Normal:</strong> effortless, quiet, and rhythmic (smooth) respirations</li>
<li><strong>Occasional labored breathing:</strong> episodic bursts of harsh, difficult, or wearing respirations</li>
<li><strong>Short period of hyperventilation:</strong> intervals of rapid, deep breaths lasting a short period of time</li>
<li><strong>Noisy labored breathing:</strong> negative-sounding respiration on inspiration or expiration; may be loud, gurgling, or wheezing; appears strenuous or wearing</li>
<li><strong>Long period of hyperventilation:</strong> rhythmic waxing and waning of breathing from very deep to shallow respirations with periods of apnea</li>
<li><strong>Cheyne-Stokes respirations:</strong> rhythmic waxing and waning with periods of apnea (cessation of breathing)</li>
</ul>

<h3>Negative vocalization</h3>
<ul>
<li><strong>None:</strong> speech/vocalization with neutral or pleasant quality</li>
<li><strong>Occasional moan or groan:</strong> mournful or murmuring sounds; wails or laments</li>
<li><strong>Low-level speech with a negative or disapproving quality:</strong> muttering, mumbling, whining, grumbling, swearing</li>
<li><strong>Repeated trouble calling out:</strong> mournful/murmuring sounds repeatedly</li>
<li><strong>Loud moaning or groaning:</strong> louder than usual inarticulate involuntary sounds</li>
<li><strong>Crying:</strong> utterance of emotion accompanied by tears; may be sobbing or quiet weeping</li>
</ul>

<h3>Facial expressions</h3>
<ul>
<li><strong>Smiling:</strong> upturned corners of the mouth, brightened eyes, look of pleasure</li>
<li><strong>Sad:</strong> unhappy, lonesome, sorrowful or dejected look; may have tears</li>
<li><strong>Frightened:</strong> fear, alarm, heightened anxiety; wide-open eyes</li>
<li><strong>Frown:</strong> downward turn of corners of mouth; increased facial wrinkling in forehead and around mouth</li>
<li><strong>Facial grimacing:</strong> distorted and distressed look; more wrinkled brow; area around mouth squeezed; eyes may be squeezed shut</li>
</ul>

<h3>Body language</h3>
<ul>
<li><strong>Relaxed:</strong> calm, restful, mellow; taking it easy</li>
<li><strong>Tense:</strong> strained, apprehensive or worried; jaw may be clenched (exclude contractures)</li>
<li><strong>Distressed pacing:</strong> unsettled activity; may be fearful, worried, or disturbed; rate may be faster or slower</li>
<li><strong>Fidgeting:</strong> restless movement; squirming, wiggling; hitching the chair across the room; repetitive touching, tugging, or rubbing body parts</li>
<li><strong>Rigid:</strong> stiffening of body; arms/legs tight and unyielding; trunk may appear straight (exclude contractures)</li>
<li><strong>Fists clenched:</strong> tightly closed hands; may be opened and closed repeatedly or held tightly shut</li>
<li><strong>Knees pulled up:</strong> flexing legs and drawing knees up toward chest; overall troubled appearance (exclude contractures)</li>
<li><strong>Pulling or pushing away:</strong> resistiveness upon approach or to care; trying to escape by yanking or wrenching himself or herself free or shoving you away</li>
<li><strong>Striking out:</strong> hitting, kicking, grabbing, punching, biting — physical assault</li>
</ul>

<h3>Consolability</h3>
<ul>
<li><strong>No need to console:</strong> sense of well-being; patient appears content</li>
<li><strong>Distracted or reassured by voice or touch:</strong> behavior stops during interaction with no indication the patient is distressed; soothable</li>
<li><strong>Unable to console, distract, or reassure:</strong> inability to soothe the patient or stop a behavior with words or actions; no amount of verbal or physical comforting will alleviate</li>
</ul>

<h2>Hospice relevance</h2>
<p>Essential for Alzheimer's/dementia hospice patients at FAST stages 6-7 where self-report is no longer reliable. A persistent PAINAD &gt;=4 despite scheduled analgesia is evidence of refractory symptom burden that may support GIP level-of-care arguments or care-plan escalation. Document serial PAINAD at every visit where pain is a concern. Triangulates with Hospice-Scale-SEV (Symptom Escalation Velocity) for trajectory.</p>

<h2>How this fits the picture</h2>
<div class="picture">
<div class="picture-label">PICTURE-PAINTING</div>
PAINAD is an observational tool for patients whose cognition no longer allows self-report. A high PAINAD score is NOT a terminal-prognosis signal per se; it is a symptom-burden signal. In the hospice picture, use PAINAD to demonstrate (a) pain is being actively assessed in non-verbal patients, (b) interventions are being titrated to response, and (c) symptom burden either is controlled (supports continued hospice care) or is refractory (supports GIP escalation). Pain control adequacy is a CAHPS-relevant quality metric independent of eligibility.
</div>

<h2>Pitfalls</h2>
<ul>
<li>Contractures mimic "rigid" body language — explicitly exclude per scoring guidance</li>
<li>Baseline breathing patterns may already be abnormal (CHF, COPD) — establish baseline before interpreting PAINAD breathing domain</li>
<li>Vocalization may reflect dementia behaviors other than pain (e.g., agitation, delirium) — use PAINAD as one signal, not the only one</li>
<li>Best administered during care activities (bathing, transfer) where latent pain is expressed, not at rest</li>
</ul>

<h2>Reference</h2>
<p>Warden V, Hurley AC, Volicer L. Development and psychometric evaluation of the Pain Assessment in Advanced Dementia (PAINAD) scale. Journal of the American Medical Directors Association. 2003;4(1):9-15.</p>
""",
    "tag": "Non-verbal pain assessment",
})

# ==========================================================
# 3. FLACC — non-verbal pain scale
# ==========================================================
DOCS.append({
    "slug": "Hospice-Scale-FLACC",
    "title": "FLACC — Face, Legs, Activity, Cry, Consolability Pain Scale",
    "body": """
<p><strong>Summary.</strong> Five-category observational pain scale originally developed for pediatric patients; widely used in hospice for non-communicative adults. Total 0-10, with each category scored 0-2. Complements PAINAD for non-verbal pain assessment.</p>

<h2>Scoring</h2>
<table>
<tr><th>Category</th><th>0</th><th>1</th><th>2</th></tr>
<tr><td>Face</td><td>No particular expression or smile</td><td>Occasional grimace or frown, withdrawn, disinterested, appears worried</td><td>Frequent to constant quivering chin, clenched jaw, distressed looking face, expression of fright/panic</td></tr>
<tr><td>Legs</td><td>Normal position or relaxed, usual tone and motion to limbs</td><td>Uneasy, restless, tense, occasional tremors</td><td>Kicking or legs drawn up, marked increase in spasticity, constant tremors, jerking</td></tr>
<tr><td>Activity</td><td>Lying quietly, normal position, moves easily, regular rhythmic respirations</td><td>Squirming, shifting back and forth, tense/guarded movements, mildly agitated, shallow/splinting respirations, intermittent sighs</td><td>Arched, rigid, or jerking; severe agitation, head banging, shivering (not rigors), breath holding, gasping, severe splinting</td></tr>
<tr><td>Cry</td><td>No cry (awake or asleep)</td><td>Moans or whimpers, occasional complaint, occasional verbal outbursts, constant grunting</td><td>Crying steadily, screams or sobs, frequent complaints, repeated outbursts, constant grunting</td></tr>
<tr><td>Consolability</td><td>Content, relaxed</td><td>Reassured by occasional touching, hugging, or being talked to; distractible</td><td>Difficult to console or comfort; pushing caregiver away, resisting care or comfort measures</td></tr>
</table>
<p><strong>Total:</strong> sum of five categories, range 0-10.</p>

<h2>Interpretation</h2>
<ul>
<li>0: relaxed and comfortable</li>
<li>1-3: mild discomfort</li>
<li>4-6: moderate pain</li>
<li>7-10: severe pain / discomfort</li>
</ul>

<h2>When to use in hospice</h2>
<p>Complementary to PAINAD. Some teams prefer FLACC for alert non-verbal patients (e.g., ALS with anarthria) and PAINAD for advanced-dementia patients. Either is acceptable; the choice is institutional preference. Use the same scale over time for a given patient so trajectories are comparable.</p>

<h2>Reference</h2>
<p>Merkel SI, Voepel-Lewis T, Shayevitz JR, Malviya S. The FLACC: A behavioral scale for scoring postoperative pain in young children. Pediatric Nursing 1997;23:293-297.</p>
""",
    "tag": "Non-verbal pain assessment",
})

# ==========================================================
# 4. NORTON Pressure Sore Risk Scale
# ==========================================================
DOCS.append({
    "slug": "Hospice-Scale-Norton-Pressure-Sore",
    "title": "Norton Pressure Sore Risk Assessment Scale",
    "body": """
<p><strong>Summary.</strong> Five-domain pressure ulcer risk assessment developed by Doreen Norton in 1962 — the original pressure-ulcer risk scale. Domains: physical condition, mental condition, activity, mobility, incontinence. Total 5-20. Lower score = higher risk. Alternative to Braden; simpler but less granular.</p>

<h2>Scoring</h2>
<table>
<tr><th>Category</th><th>4 (best)</th><th>3</th><th>2</th><th>1 (worst)</th></tr>
<tr><td>Physical condition</td><td>Good</td><td>Fair</td><td>Poor</td><td>Very bad</td></tr>
<tr><td>Mental state</td><td>Alert</td><td>Apathetic</td><td>Confused</td><td>Stupor</td></tr>
<tr><td>Activity</td><td>Ambulant</td><td>Walks with help</td><td>Chairbound</td><td>Bedfast</td></tr>
<tr><td>Mobility</td><td>Full</td><td>Slightly limited</td><td>Very limited</td><td>Immobile</td></tr>
<tr><td>Incontinence</td><td>None</td><td>Occasional</td><td>Usually urinary</td><td>Urinary and fecal</td></tr>
</table>
<p><strong>Sum:</strong> range 5-20. <strong>Lower score = higher risk.</strong></p>

<h2>Interpretation (flip book version)</h2>
<table>
<tr><th>Total</th><th>Risk category</th></tr>
<tr><td>5-9</td><td>Very high risk</td></tr>
<tr><td>10-13</td><td>High risk</td></tr>
<tr><td>14-17</td><td>Medium risk</td></tr>
<tr><td>18+</td><td>Low risk</td></tr>
</table>

<h2>Norton vs. Braden in hospice</h2>
<p>Braden is more commonly used in US acute and long-term care; Norton has stronger tradition in UK and some LTC settings. Both are valid. In hospice:</p>
<ul>
<li>Use whichever is documented in the patient's existing records for trend continuity</li>
<li>A Norton ≤9 or a Braden ≤9 both indicate severe risk</li>
<li>Neither is a terminal-prognosis score; both reflect immobility/incontinence/nutritional-decline context that often accompanies terminal trajectory</li>
</ul>

<h2>Reference</h2>
<p>Norton D, McLaren R, Exton-Smith AN. An Investigation of Geriatric Nursing Problems in Hospital. London: National Corporation for the Care of Old People; 1962.</p>
""",
    "tag": "Pressure ulcer risk",
})

# ==========================================================
# 5. OTHER TERMINAL ILLNESSES — 11-point decline checklist
# ==========================================================
DOCS.append({
    "slug": "Other-Terminal-Illnesses-Documentation",
    "title": "Other Terminal Illnesses — Documentation Framework for Path 4 Eligibility",
    "body": """
<p><strong>Summary.</strong> When a patient's terminal illness does not have a disease-specific LCD, hospice eligibility depends on Physician's Clinical Judgment (Path 4 — see Four-Ways-To-Document-Eligibility). The flip book (page 36) provides an 11-point checklist of observable and documented deterioration in overall clinical condition within the past 6 months. This document promotes that checklist to a first-class reference.</p>

<div class="callout">
<strong>Important scope note:</strong> "Other Terminal Illnesses" is NOT a diagnosis. It is a documentation framework for patients whose terminal illness lacks a specific LCD. The patient's actual diagnosis must be listed; this framework supplies the supporting-evidence structure.
</div>

<h2>The 11-point Other Terminal Illness decline checklist</h2>
<p><em>Observable and documented deterioration in overall clinical condition in the past 6 months, evidenced by any of:</em></p>
<ol>
<li>Serial physician assessments documenting worsening clinical status over time</li>
<li>Multiple hospital or ER visits during the past 6 months</li>
<li>Progressive pressure ulcers</li>
<li>Decline in functional status with a PPS of ≤40%</li>
<li>Systolic BP &lt;90 mmHg</li>
<li>Progressive dependence with ADLs</li>
<li>Persistent nausea and vomiting</li>
<li>Recent impaired nutritional status</li>
<li>Weight loss</li>
<li>Decreasing serum albumin ≤2.5 g/dL</li>
<li>Malnutrition with BMI less than 22 kg/m²</li>
<li>Combination of disease processes which, viewed together, present a picture of structural and functional impairment</li>
<li>Requires O2 at rest</li>
<li>Declines artificial ventilation</li>
</ol>

<h2>How to use this checklist</h2>
<ul>
<li>Do not require every bullet — the framework is disjunctive ("any of the following")</li>
<li>The more bullets that apply, the stronger the documentation</li>
<li>Document specific findings with dates, values, and comparisons to baseline</li>
<li>Pair with quantified scales — PPS, ECOG, BODE, CCI, NDI, FDR — for numeric anchors that support the narrative</li>
<li>Use this framework for patients whose diagnoses (e.g., frailty, multiple chronic conditions without clear dominant terminal illness, specific conditions without Palmetto LCDs) put them on Path 4</li>
</ul>

<h2>Relationship to Path 4 clinical judgment</h2>
<p>The CMS Medicare Benefit Policy Manual Ch. 9 §20.1 explicitly allows certification of patients who do not meet any specific LCD if the physician can document sound clinical judgment for 6-month prognosis. The 11-point checklist is the operational scaffold for that clinical-judgment narrative.</p>

<h2>Integration with corpus</h2>
<ul>
<li><strong>Four-Ways-To-Document-Eligibility</strong> (companion doc): identifies when Path 4 applies</li>
<li><strong>Hospice-Scale-CCI (Charlson Comorbidity Index)</strong>: quantifies the "combination of disease processes" bullet</li>
<li><strong>Hospice-Scale-FDR (Functional Decline Rate)</strong>: quantifies the "decline in functional status" and "progressive dependence" bullets</li>
<li><strong>Hospice-Scale-NDI (Nutritional Decline Index)</strong>: quantifies the weight-loss, albumin, and BMI bullets</li>
<li><strong>HospiceToolbox-Adult-Failure-To-Thrive</strong>: closely related framework for AFTT-adjacent presentations</li>
<li><strong>HospiceToolbox-General-Non-Disease-Specific</strong>: overlaps — both are non-disease-specific, both emphasize decline over time</li>
</ul>

<h2>Reference</h2>
<p>Hospice Eligibility Resource Flip Book (One Point Hospice), page 36 (Other Terminal Illnesses). CMS Medicare Benefit Policy Manual, Chapter 9 §20.1 (certification of terminal illness).</p>
""",
    "tag": "Path 4 documentation framework",
})

# ==========================================================
# 6. FLIP BOOK CROSS-REFERENCE MAP
# ==========================================================
DOCS.append({
    "slug": "Flipbook-Cross-Reference-Map",
    "title": "Flip Book Cross-Reference Map — How the Flip Book Connects to the Corpus",
    "body": """
<p><strong>Purpose of this document.</strong> The Hospice Eligibility Resource Flip Book (One Point Hospice) is a 36-page scanned clinical reference. This cross-reference map tells NotebookLM (and any user) how each section of the flip book relates to other sources in the Amerix Hospice Compliance knowledge corpus. When a query pulls from the flip book, this map surfaces the related Palmetto LCDs, Amerix Assessment Scales, and Cross-MAC Toolbox docs that complement it.</p>

<h2>Flip book structure (36 pages)</h2>

<h3>Section 1 — Scales &amp; Clinical Assessment Tools (pages 2-20)</h3>
<table>
<tr><th>Flip book page</th><th>Content</th><th>Cross-references in corpus</th></tr>
<tr><td>2</td><td>BMI formula + Mid-arm circumference technique</td><td>Hospice-Scale-NDI (Nutritional Decline Index) — BMI component</td></tr>
<tr><td>3</td><td>BMI lookup table</td><td>Hospice-Scale-NDI</td></tr>
<tr><td>4</td><td>PPS (Palliative Performance Scale)</td><td>Hospice-Scale-FDR (uses PPS as input); HospiceToolbox-General (PPS &lt;70% threshold)</td></tr>
<tr><td>5-6</td><td>FAST (Functional Assessment Staging Tool) - full scale through 7F</td><td>Hospice-Scale-FDR; HospiceToolbox-Dementia-Alzheimers; Palmetto-JMHHH-LCD-L34567</td></tr>
<tr><td>7</td><td>NYHA Functional Classification</td><td>Hospice-Scale-SHFM (NYHA is a SHFM input); HospiceToolbox-Cardiac; Palmetto-JMHHH-LCD-L34548</td></tr>
<tr><td>8</td><td>ECOG Performance Status</td><td>Hospice-Scale-ECOG</td></tr>
<tr><td>9</td><td>PAINAD (Pain Assessment in Advanced Dementia)</td><td>Hospice-Scale-PAINAD (companion doc)</td></tr>
<tr><td>10-14</td><td>PAINAD sub-domain rubrics (breathing, vocalization, face, body, consolability)</td><td>Hospice-Scale-PAINAD</td></tr>
<tr><td>15</td><td>DMAR Mortality Risk Index Score (Mitchell) for dementia</td><td>Hospice-Scale-Mitchell-MRI</td></tr>
<tr><td>16</td><td>ADEPT Stroke/Alzheimer's Prognosis Tool</td><td>Hospice-Scale-Mitchell-MRI (ADEPT is a Mitchell derivative)</td></tr>
<tr><td>17</td><td>FLACC Pain Scale</td><td>Hospice-Scale-FLACC (companion doc)</td></tr>
<tr><td>18-19</td><td>Norton Pressure Sore Risk Scale</td><td>Hospice-Scale-Norton-Pressure-Sore (companion); Hospice-Scale-Braden (alternative)</td></tr>
<tr><td>20</td><td>Fall Risk Assessment</td><td>Hospice-Scale-Morse (Morse Fall Scale alternative); Hospice-Scale-TUG</td></tr>
</table>

<h3>Section 2 — Documentation Framework (pages 21-25)</h3>
<table>
<tr><th>Page</th><th>Content</th><th>Cross-references</th></tr>
<tr><td>21</td><td>Four Ways to Document Eligibility</td><td>Four-Ways-To-Document-Eligibility (companion doc, first-class promotion of this framework)</td></tr>
<tr><td>22</td><td>Medical Director Certification template</td><td>CMS-MBPM-Ch9 §20.1 certification requirements</td></tr>
<tr><td>23</td><td>LCD guidance - 3 MACs (CGS, NGS, Palmetto)</td><td>HospiceToolbox-* (cross-MAC indicator library docs); all Palmetto-JMHHH-LCD-* docs</td></tr>
<tr><td>24-25</td><td>General Guidelines checklist</td><td>HospiceToolbox-General-Non-Disease-Specific</td></tr>
</table>

<h3>Section 3 — Disease-Specific Guidelines (pages 26-36)</h3>
<table>
<tr><th>Page</th><th>Disease</th><th>Primary cross-reference</th></tr>
<tr><td>26</td><td>Amyotrophic Lateral Sclerosis (ALS)</td><td>HospiceToolbox-ALS; Palmetto-JMHHH-LCD-L34547-Neurological</td></tr>
<tr><td>27</td><td>Alzheimer's &amp; Related Diseases (FAST scale criteria)</td><td>HospiceToolbox-Dementia-Alzheimers; Palmetto-JMHHH-LCD-L34567; Hospice-Scale-FDR</td></tr>
<tr><td>28</td><td>Cancer</td><td>HospiceToolbox-Cancer; Hospice-Scale-ECOG; CMS-MBPM-Ch9</td></tr>
<tr><td>29</td><td>Cardiopulmonary (Cardiac + Pulmonary)</td><td>HospiceToolbox-Cardiac; HospiceToolbox-Pulmonary; Palmetto-JMHHH-LCD-L34548; Hospice-Scale-BODE; Hospice-Scale-SHFM</td></tr>
<tr><td>30</td><td>HIV</td><td>HospiceToolbox-HIV</td></tr>
<tr><td>31</td><td>Liver Disease</td><td>HospiceToolbox-Liver; Palmetto-JMHHH-LCD-L34544; Hospice-Scale-MELD</td></tr>
<tr><td>32</td><td>Renal Disease</td><td>HospiceToolbox-Renal; Palmetto-JMHHH-LCD-L34559</td></tr>
<tr><td>33</td><td>Parkinson's Disease</td><td>HospiceToolbox-Neurological; Palmetto-JMHHH-LCD-L34547</td></tr>
<tr><td>34</td><td>Stroke and Coma (CVA late sequelae)</td><td>HospiceToolbox-Stroke-Coma; Palmetto-JMHHH-LCD-L34547</td></tr>
<tr><td>35</td><td>Protein Calorie Malnutrition (trajectory, not principal diagnosis)</td><td>Hospice-Scale-NDI; HospiceToolbox-Adult-Failure-To-Thrive; HospiceToolbox-General</td></tr>
<tr><td>36</td><td>Other Terminal Illnesses (11-point deterioration checklist)</td><td>Other-Terminal-Illnesses-Documentation (companion doc); Four-Ways-To-Document-Eligibility Path 4</td></tr>
</table>

<h2>Source philosophy (from flip book page 1)</h2>
<blockquote>
<p><strong>WHAT THIS TOOLBOX IS:</strong> A collection of tools and guidelines intended to facilitate gathering of information by clinicians to improve documentation of symptoms and assessment findings that demonstrate hospice eligibility; providing guidance for Hospice Medical Directors to utilize in exercising their medical judgement in determining prognosis and documenting hospice eligibility.</p>
<p><strong>WHAT THIS TOOLBOX IS NOT:</strong> A definitive or authoritative listing of criteria for determination of prognosis and hospice eligibility.</p>
<p><strong>MEDICAL JUDGEMENT SHOULD ALWAYS BE USED FOR EACH CASE IN DETERMINING PROGNOSIS AND HOSPICE ELIGIBILITY.</strong></p>
</blockquote>
<p>This philosophy is identical to the governance framing used throughout the Amerix corpus: brush strokes, not criteria; tools, not rubber stamps.</p>

<h2>Key attribution</h2>
<p>The flip book is published by <strong>One Point Hospice</strong> and its predecessors. Page 23 states it is "derived from the 3 different MAC's LCDs, generally choosing the strictest version" — an explicit cross-MAC synthesis that validates the toolbox / brush-strokes approach in the Amerix corpus.</p>
""",
    "tag": "Corpus cross-reference map",
})


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width":1000,"height":1400})
        page = await ctx.new_page()
        for i, doc in enumerate(DOCS, 1):
            html = render(doc["title"], doc["body"], doc.get("tag","Companion"))
            path = OUT_DIR / f"Flipbook-Companion-{doc['slug']}.pdf"
            # The PAINAD, FLACC, Norton get the Hospice-Scale prefix to match existing scale-doc naming
            if doc["slug"].startswith("Hospice-Scale-"):
                path = OUT_DIR / f"{doc['slug']}.pdf"
            elif doc["slug"] in ("Four-Ways-To-Document-Eligibility", "Other-Terminal-Illnesses-Documentation", "Flipbook-Cross-Reference-Map"):
                path = OUT_DIR / f"{doc['slug']}.pdf"
            print(f"[{i}/{len(DOCS)}] {doc['slug']}...", end=" ", flush=True)
            await page.set_content(html, wait_until="networkidle")
            await page.pdf(path=str(path), format="Letter",
                           margin={"top":"0.6in","right":"0.6in","bottom":"0.6in","left":"0.6in"},
                           print_background=True)
            print(f"PDF {path.stat().st_size:,} bytes  -> {path.name}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
