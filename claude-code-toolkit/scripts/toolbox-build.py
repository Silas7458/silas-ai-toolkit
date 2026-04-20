#!/usr/bin/env python3
"""Build the Hospice Appropriateness Indicator Toolbox.

Generates disease-organized PDFs containing brush-strokes extracted from
other MACs' LCDs (NGS, CGS) alongside our governing MAC (Palmetto)
criteria. Each doc prefaced with a prominent governance disclaimer:
these are INDICATORS for picture-painting, not governing criteria.

Input: extracted text from /hospice-toolbox-source/ (CGS per-disease
PDFs + NGS L33393 + CGS L34538 umbrella LCDs).

Output: 11 per-disease PDFs rendered via Playwright + uploaded to Drive.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright


DRIVE_FOLDER_ID = "1zL6M_LdPtP52OyJNH0q0dy-j5PCg8z4u"
OUT_DIR = Path("hospice-toolbox-pdfs")
OUT_DIR.mkdir(exist_ok=True)


CSS = """
<style>
@page { size: Letter; margin: 0.6in; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt; line-height: 1.5; color: #222; margin: 0; }
h1 { font-size: 20pt; color: #1a3a52; border-bottom: 3px double #1a3a52; padding-bottom: 6px; margin: 0 0 6pt 0; }
h2 { font-size: 13pt; color: #1a3a52; border-bottom: 1px solid #c0c8d0; padding-bottom: 3px; margin-top: 16pt; margin-bottom: 6pt; }
h3 { font-size: 11.5pt; color: #2a4a62; margin-top: 10pt; margin-bottom: 4pt; }
.governance { background: #5a1a1a; color: #fff7e6; border: 3px solid #3a0a0a; padding: 12px 16px; margin: 0 0 16pt 0; border-radius: 4px; }
.governance-label { font-weight: bold; font-family: Arial, sans-serif; font-size: 10pt; letter-spacing: 1px; text-transform: uppercase; color: #ffcc99; }
.governance p { margin: 4pt 0; font-size: 10.5pt; }
.mac-excerpt { border-left: 5px solid #1a3a52; background: #f2f6f9; padding: 10px 14px; margin: 10pt 0; font-size: 10.5pt; }
.mac-label { font-weight: bold; font-family: Arial, sans-serif; color: #1a3a52; font-size: 10pt; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6pt; }
.mac-source { font-size: 8.5pt; color: #666; font-style: italic; }
.palette { background: #eef5ea; border: 2px solid #4a7a3a; padding: 12px 16px; margin: 12pt 0; border-radius: 4px; }
.palette-label { font-weight: bold; font-family: Arial, sans-serif; color: #2d5a1a; font-size: 10pt; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4pt; }
.convergence { background: #fff8e6; border: 2px solid #d4a017; padding: 10px 14px; margin: 10pt 0; border-radius: 4px; }
.convergence-label { font-weight: bold; font-family: Arial, sans-serif; color: #8a6a10; font-size: 10pt; text-transform: uppercase; letter-spacing: 0.5px; }
ul { margin: 4pt 0 8pt 20pt; padding: 0; }
li { margin-bottom: 3pt; }
code { font-family: Consolas, monospace; background: #eee; padding: 1px 4px; border-radius: 2px; font-size: 10pt; }
pre { font-family: Consolas, monospace; background: #f5f5f5; padding: 8px; border-left: 3px solid #999; font-size: 9.5pt; white-space: pre-wrap; margin: 8pt 0; }
.footer { margin-top: 18pt; padding-top: 8pt; border-top: 1px solid #ccc; font-size: 9pt; color: #666; font-style: italic; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 10pt; }
th { background: #1a3a52; color: white; padding: 5px 8px; text-align: left; }
td { padding: 4px 8px; border: 1px solid #bbb; vertical-align: top; }
tr:nth-child(even) td { background: #f6f9fb; }
</style>
"""


GOVERNANCE_BANNER = """
<div class="governance">
<div class="governance-label">GOVERNANCE NOTICE — READ BEFORE USE</div>
<p><strong>Palmetto GBA is the governing MAC for our jurisdiction (JM HHH).</strong> The indicators below are extracted from OTHER MACs (NGS, CGS) as a <strong>library of brush strokes</strong> — findings that multiple payers have independently recognized as markers of terminal trajectory. They are <strong>not eligibility criteria for our patients</strong>.</p>
<p>Use this toolbox to <strong>paint the picture</strong>. When a patient's presentation overlaps with indicators from NGS or CGS, that overlap is <em>supporting evidence</em> the picture we are painting under Palmetto is industry-standard — not a requirement to satisfy a different MAC's checklist.</p>
<p>Humans are multifaceted. No two patients present identically. These are tools to select from, not molds to fit patients into. The governing framework remains Palmetto's discretionary clinical-judgment standard.</p>
</div>
"""


def html_escape(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def render_html(doc):
    title = doc["title"]
    parts = [f"<h1>{html_escape(title)}</h1>", GOVERNANCE_BANNER]
    if doc.get("summary"):
        parts.append(f"<p><strong>Summary.</strong> {doc['summary']}</p>")
    if doc.get("palmetto_ref"):
        parts.append(f"<h2>Palmetto — Our governing MAC</h2>")
        parts.append(f'<div class="mac-excerpt"><div class="mac-label">PALMETTO GBA (governing)</div>{doc["palmetto_ref"]}</div>')
    if doc.get("cgs_excerpt"):
        parts.append(f"<h2>CGS Administrators (JM — Kentucky, Ohio)</h2>")
        parts.append(f'<div class="mac-excerpt"><div class="mac-label">CGS — source</div><div class="mac-source">Source: {html_escape(doc.get("cgs_source","CGS per-disease educational PDF + LCD L34538"))}</div><pre>{html_escape(doc["cgs_excerpt"])}</pre></div>')
    if doc.get("ngs_excerpt"):
        parts.append(f"<h2>NGS — National Government Services (J6 / JK)</h2>")
        parts.append(f'<div class="mac-excerpt"><div class="mac-label">NGS — source</div><div class="mac-source">Source: NGS LCD L33393, Hospice — Determining Terminal Status</div><pre>{html_escape(doc["ngs_excerpt"])}</pre></div>')
    if doc.get("convergence"):
        parts.append(f"<h2>Cross-MAC convergence (strongest brush strokes)</h2>")
        parts.append(f'<div class="convergence"><div class="convergence-label">WHERE ALL MACS AGREE</div>{doc["convergence"]}</div>')
    if doc.get("palette"):
        parts.append(f"<h2>Brush-stroke palette — the full library of indicators</h2>")
        parts.append(f'<div class="palette"><div class="palette-label">PICTURE-PAINTING PALETTE</div>{doc["palette"]}</div>')
    if doc.get("how_to_use"):
        parts.append(f"<h2>How to use this toolbox</h2>")
        parts.append(doc["how_to_use"])
    parts.append('<div class="footer">Part of the Amerix Hospice Appropriateness Indicator Toolbox. Cross-MAC indicators extracted as brush strokes for picture-painting under Palmetto GBA. Not a substitute for Palmetto LCDs or clinical judgment.</div>')
    body = "\n".join(parts)
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{CSS}</head><body>{body}</body></html>"


# Extract sections from the umbrella LCDs
def load_extracts():
    with open("C:/Users/silas/hospice-toolbox-source/_extracts.json", encoding="utf-8") as f:
        return json.load(f)


def slice_section(text, start_marker, stop_markers, fallback_chars=3500):
    idx = text.find(start_marker)
    if idx < 0:
        return ""
    end = len(text)
    for stop in stop_markers:
        stop_idx = text.find(stop, idx + len(start_marker))
        if stop_idx > 0:
            end = min(end, stop_idx)
    section = text[idx:end].strip()
    if len(section) > fallback_chars:
        section = section[:fallback_chars] + "\n[...section truncated...]"
    return section


def build_docs(extracts):
    ngs = extracts["NGS-L33393-v2.pdf"]
    cgs_um = extracts["CGS-L34538-v2.pdf"]
    non_disease = extracts["CGS-non-disease_specific.pdf"]

    def cgs_pd(key):
        """Clean extract of a CGS per-disease PDF, stripping preamble."""
        t = extracts[f"CGS-{key}.pdf"]
        # trim the standard preamble and references
        for cut in ["DISEASE SPECIFIC GUIDELINES", "Disease Specific Guidelines"]:
            idx = t.find(cut)
            if idx > 0:
                t = t[idx:]
                break
        # trim the "WHERE DO I FIND MORE INFORMATION" tail
        for cut in ["WHERE DO I FIND", "Where Do I Find"]:
            idx = t.find(cut)
            if idx > 0:
                t = t[:idx]
                break
        return t.strip()

    docs = []

    # -- Non-Disease-Specific (general indicators) --
    docs.append({
        "slug": "General-Non-Disease-Specific",
        "title": "General / Non-Disease-Specific Indicators",
        "summary": "Cross-cutting indicators of decline applicable to ANY terminal illness. The CGS 'Decline in Clinical Status' guidelines are particularly valuable because they enumerate specific clinical findings, signs, and symptoms that predict 6-month prognosis regardless of primary diagnosis.",
        "cgs_excerpt": non_disease[:6000],
        "cgs_source": "CGS Hospice Terminal Prognosis: Non-Disease Specific (educational PDF, revised 2022-02-16)",
        "ngs_excerpt": slice_section(ngs, "Part I. Decline in Clinical Status", ["Part II", "PART II"], 5500),
        "palette": """<ul>
<li><strong>Progression signs:</strong> recurrent/intractable infections (pneumonia, sepsis, UTI), progressive inanition (unexplained weight loss, falling anthropometrics, declining albumin/cholesterol), dysphagia with aspiration or inadequate intake</li>
<li><strong>Worsening symptoms:</strong> dyspnea with rising respiratory rate, intractable cough, poorly-responsive nausea/vomiting, intractable diarrhea, pain requiring escalating major analgesics</li>
<li><strong>Worsening signs:</strong> declining systolic BP &lt;90 or postural hypotension, ascites, venous/arterial/lymphatic obstruction from disease, edema, pleural/pericardial effusion, weakness, change in level of consciousness</li>
<li><strong>Functional decline:</strong> KPS/PPS &lt;70%, dependence in 2+ ADLs (feeding, ambulation, continence, transfer, bathing, dressing)</li>
<li><strong>Progressive infections:</strong> recurrent after treatment; escalating acute care utilization</li>
</ul>""",
        "how_to_use": "<p>For any primary diagnosis, layer these non-disease-specific indicators on top of the disease-specific picture. If a patient meets disease-specific criteria AND shows multiple non-disease-specific signs, the picture converges strongly toward terminal prognosis. If the disease-specific criteria are borderline, the presence of many non-disease-specific signs can still support a defensible hospice narrative under Palmetto's clinical-judgment standard.</p>",
        "convergence": "<p><strong>CGS, NGS, and Palmetto all agree on these baseline indicators:</strong> KPS/PPS &lt;70%, dependence in 2+ ADLs, weight loss, albumin decline, recurrent infections, and progressive functional decline. When multiple of these co-occur with any disease-specific finding, all three MACs' frameworks independently support hospice appropriateness.</p>",
    })

    # --- CGS per-disease based docs ---
    for slug, title, key, convergence_txt, palette_txt in [
        ("Cardiac", "Heart Disease / Congestive Heart Failure", "heart",
         "All three MACs converge on: NYHA IV + optimal medical therapy + supporting cardiac events (symptomatic arrhythmia, syncope, cardiac arrest, cardiac-origin CVA, concomitant HIV).",
         """<ul>
<li><strong>Core:</strong> NYHA Class IV despite optimal therapy; EF ≤20% (supportive); inability to carry out any physical activity without discomfort</li>
<li><strong>Events:</strong> treatment-resistant arrhythmias (SVT or VT), history of cardiac arrest/resuscitation, unexplained syncope, cardiac-origin CVA</li>
<li><strong>Non-specific layering:</strong> progressive cachexia, frequent ED/hospitalizations for CHF exacerbation, refractory dyspnea, renal/hepatic congestion</li>
<li><strong>Comorbidity:</strong> concomitant HIV strengthens the picture; diabetes, CKD, COPD compound</li>
</ul>"""),
        ("Pulmonary", "Pulmonary Disease / COPD", "pulmonary_disease",
         "All three MACs converge on: disabling dyspnea at rest + FEV1 &lt;30% (supportive) + progression evidenced by increasing ED/hospitalizations + resting hypoxemia (pO2 ≤55 or SaO2 ≤88%) or hypercapnia (pCO2 ≥50).",
         """<ul>
<li><strong>Core respiratory:</strong> disabling dyspnea at rest unresponsive to bronchodilators; bed-to-chair functional limitation; FEV1 &lt;30% post-bronchodilator (supportive)</li>
<li><strong>Disease progression:</strong> increasing ED visits/hospitalizations for pulmonary infections or respiratory failure; serial FEV1 decline &gt;40 mL/year</li>
<li><strong>Gas-exchange failure:</strong> resting pO2 ≤55 mmHg OR SaO2 ≤88% on room air OR pCO2 ≥50 mmHg</li>
<li><strong>Systemic signs:</strong> cor pulmonale (right heart failure), unintentional weight loss &gt;10% in 6 months, resting tachycardia &gt;100 bpm</li>
<li><strong>BODE Index:</strong> BODE &gt;=7 captures multiple of these in one validated score (see Hospice-Scale-BODE in corpus)</li>
</ul>"""),
        ("Liver", "Liver Disease", "liver_disease",
         "All three MACs converge on: INR &gt;1.5 AND serum albumin &lt;2.5 g/dL + end-stage complications (refractory ascites, SBP, hepatorenal syndrome, recurrent variceal bleeding, refractory hepatic encephalopathy).",
         """<ul>
<li><strong>Lab anchors:</strong> INR &gt;1.5 (or PT &gt;5 sec over control) AND albumin &lt;2.5 g/dL</li>
<li><strong>End-stage complications (at least one):</strong> refractory ascites, spontaneous bacterial peritonitis (SBP), hepatorenal syndrome, refractory hepatic encephalopathy, recurrent variceal bleeding despite therapy</li>
<li><strong>Supporting:</strong> progressive malnutrition, muscle wasting, continued active alcoholism (&gt;80 g ethanol/day), hepatocellular carcinoma, HBsAg+, HCV refractory to treatment</li>
<li><strong>MELD:</strong> MELD &gt;=20 usually aligns (see Hospice-Scale-MELD in corpus); MELD-Na and MELD 3.0 are refinements</li>
<li><strong>Transplant note:</strong> awaiting transplant + meets criteria = can be certified; discharge if donor procured</li>
</ul>"""),
        ("Renal", "Renal Disease (Acute and Chronic Kidney Failure)", "renal_failure",
         "All three MACs converge on: patient not pursuing dialysis/transplant + GFR &lt;15 mL/min OR creatinine &gt;8.0 (&gt;6.0 for diabetics) + signs/symptoms of uremia (uremia, oliguria, hyperkalemia, uremic pericarditis, hepatorenal, refractory fluid overload).",
         """<ul>
<li><strong>Not on path to renal replacement:</strong> not seeking dialysis, not a transplant candidate, or discontinuing dialysis</li>
<li><strong>Lab thresholds:</strong> GFR &lt;15 mL/min OR serum creatinine &gt;8.0 mg/dL (&gt;6.0 for diabetics)</li>
<li><strong>Acute renal failure supporting:</strong> on mechanical ventilation, active malignancy, chronic lung disease, advanced cardiac/liver disease, sepsis, AIDS, cachexia, thrombocytopenia &lt;25k, DIC, GI bleed</li>
<li><strong>Chronic renal failure signs:</strong> uremia, oliguria, intractable hyperkalemia &gt;7.0 unresponsive to treatment, uremic pericarditis, hepatorenal syndrome, intractable fluid overload</li>
</ul>"""),
        ("Stroke-Coma", "Stroke and Coma", "stroke_coma",
         "All three MACs converge on: KPS/PPS ≤40% + inability to maintain hydration/calories (weight loss, albumin &lt;2.5, aspiration, dysphagia, failed calorie counts) + supporting imaging + medical complications (aspiration pneumonia, UTI, sepsis, stage 3-4 decubiti, recurrent fever).",
         """<ul>
<li><strong>Functional anchor:</strong> KPS or PPS ≤40% (note this is LOWER than the 70% baseline used for most diseases — stroke/coma has a lower qualifying threshold)</li>
<li><strong>Nutrition/hydration failure:</strong> weight loss &gt;10% in 6 months OR &gt;7.5% in 3 months, albumin &lt;2.5, current aspiration unresponsive to SLP, calorie counts showing inadequate intake, severe dysphagia without artificial nutrition</li>
<li><strong>Imaging (hemorrhagic stroke):</strong> large-volume hemorrhage (infratentorial ≥20 mL or supratentorial ≥50 mL), ventricular extension, ≥30% cerebrum involvement, midline shift ≥1.5 cm, obstructive hydrocephalus without shunt</li>
<li><strong>Imaging (thrombotic/embolic):</strong> large anterior with cortical+subcortical involvement, large bihemispheric infarcts, basilar artery occlusion, bilateral vertebral occlusion</li>
<li><strong>Coma criteria (any 3 on day 3):</strong> abnormal brain stem response, absent verbal response, absent withdrawal to pain, Cr &gt;1.5</li>
<li><strong>Complications in prior 12 months:</strong> aspiration pneumonia, pyelonephritis, sepsis, refractory stage 3-4 decubiti, recurrent fever after antibiotics</li>
</ul>"""),
        ("HIV", "HIV Disease / AIDS", "hiv",
         "All three MACs converge on: CD4 &lt;25 or persistent viral load &gt;100k + KPS ≤50% + an AIDS-defining illness (CNS lymphoma, wasting, MAC bacteremia, PML, visceral KS, systemic lymphoma, cryptosporidium, toxoplasmosis, renal failure without dialysis).",
         """<ul>
<li><strong>Core laboratory:</strong> CD4+ count &lt;25 cells/mcL OR persistent HIV RNA viral load &gt;100,000 copies/mL</li>
<li><strong>AIDS-defining opportunistic illness (at least one):</strong> CNS lymphoma, wasting &gt;10% lean body mass, MAC bacteremia untreated/unresponsive, PML, systemic lymphoma partially responsive, visceral Kaposi's unresponsive, renal failure without dialysis, cryptosporidium, toxoplasmosis unresponsive</li>
<li><strong>Functional:</strong> KPS ≤50% (lower threshold than most diseases)</li>
<li><strong>Supporting factors:</strong> chronic persistent diarrhea &gt;1 year, persistent albumin &lt;2.5, active substance abuse, age &gt;50, resistance to ART/prophylaxis, advanced AIDS dementia complex, CHF at rest, advanced liver disease</li>
</ul>"""),
        ("Dementia-Alzheimers", "Dementia / Alzheimer's Disease", "dementia_alzheimers",
         "All three MACs converge on: FAST Stage 7 or beyond + complete ADL dependence (ambulation, dressing, bathing) + urinary/fecal incontinence + speech limited to ≤6 intelligible words + recent medical complication (aspiration pneumonia, pyelonephritis, septicemia, stage 3-4 decubiti, recurrent fever after antibiotics, or inability to maintain intake with 10% weight loss or albumin &lt;2.5).",
         """<ul>
<li><strong>FAST staging:</strong> Stage 7 or beyond on the Functional Assessment Staging scale</li>
<li><strong>Complete ADL loss:</strong> unable to ambulate, dress, or bathe without assistance; urinary AND fecal incontinence</li>
<li><strong>Communication failure:</strong> no consistently meaningful verbal communication — stereotypical phrases only OR ≤6 intelligible words</li>
<li><strong>Recent medical complication (within 12 months):</strong> aspiration pneumonia, pyelonephritis/UTI, septicemia, multiple stage 3-4 decubiti, recurrent post-antibiotic fever, or inability to maintain fluid/calorie intake with 10% weight loss or albumin &lt;2.5</li>
<li><strong>Scope note:</strong> These criteria are specific to Alzheimer's and RELATED disorders. They are NOT appropriate for multi-infarct (vascular) dementia — clinical judgment required for vascular patterns</li>
<li><strong>Supporting scales:</strong> see Hospice-Scale-FDR, Hospice-Scale-Mitchell-MRI, and Hospice-Scale-NDI in corpus for quantified companion metrics</li>
</ul>"""),
    ]:
        docs.append({
            "slug": slug,
            "title": f"Indicator Toolbox — {title}",
            "summary": f"Cross-MAC indicator library for {title}. Direct quotations from source MAC guidelines, organized to support picture-painting under Palmetto's discretionary framework.",
            "cgs_excerpt": cgs_pd(key),
            "cgs_source": f"CGS Hospice Terminal Prognosis: {title} (educational PDF)",
            "ngs_excerpt": "(NGS uses the same disease-specific criteria as documented in the CGS source above; NGS L33393 codifies these within the umbrella LCD. The core thresholds, comorbidity layering, and baseline functional requirements are identical.)",
            "convergence": f"<p>{convergence_txt}</p>",
            "palette": palette_txt,
            "palmetto_ref": f"<p>Palmetto GBA publishes disease-specific LCDs for this condition (see <code>Palmetto-JMHHH-LCD-*</code> PDFs already in your corpus). Palmetto uses a <strong>Part 1 + Part 2</strong> logic: meet a primary threshold AND show supporting findings. The supporting-findings list overlaps substantially with the CGS/NGS indicators above.</p>",
            "how_to_use": "<p>Use as a supplementary source when the Palmetto LCD's supporting-findings section is being expanded. Patients whose presentation includes indicators recognized across all three MACs (the convergence section) have the strongest cross-payer support for terminal prognosis — document those findings prominently. Indicators seen only in NGS or CGS but not Palmetto are <em>additional brush strokes</em> for the picture, not required criteria.</p>",
        })

    # ALS (from umbrella LCDs)
    als_section = slice_section(cgs_um, "Amyotrophic Lateral Sclerosis", ["HIV Disease", "Heart Disease"], 5000)
    docs.append({
        "slug": "ALS",
        "title": "Indicator Toolbox — Amyotrophic Lateral Sclerosis (ALS)",
        "summary": "Cross-MAC indicators for ALS-specific terminal prognosis. ALS has a distinctive linear progression which lets clinicians track rate of decline; this differs from most other hospice diagnoses.",
        "cgs_excerpt": als_section,
        "cgs_source": "CGS LCD L34538 — Amyotrophic Lateral Sclerosis section",
        "ngs_excerpt": slice_section(ngs, "Amyotrophic Lateral Sclerosis", ["HIV", "AIDS", "Heart Disease"], 5000),
        "convergence": "<p>CGS, NGS, and Palmetto converge on: rapid progression in 12 months (wheelchair/bedbound, unintelligible speech, pureed diet, major assistance with ADLs) PLUS critical nutritional impairment OR life-threatening respiratory complications.</p>",
        "palette": """<ul>
<li><strong>Rapid progression in last 12 months:</strong> from independent ambulation → wheelchair/bedbound; from normal speech → barely intelligible; from normal diet → pureed; from independent ADLs → major assistance needed</li>
<li><strong>Critical nutritional impairment:</strong> patient refuses artificial feeding AND sustained weight loss AND dehydration OR insufficient fluid intake; OR, if receiving artificial nutrition, cannot maintain adequate intake</li>
<li><strong>Life-threatening respiratory complications:</strong> dyspnea at rest, vital capacity &lt;30% (supportive), requires O2, patient refuses invasive ventilation (NIV tolerance + progression or NIV intolerance are strong signals)</li>
<li><strong>Critical complications:</strong> recurrent aspiration pneumonia, upper UTI (pyelonephritis), sepsis, recurrent fever after antibiotics, stage 3-4 decubiti</li>
</ul>""",
        "palmetto_ref": "<p>Palmetto does NOT publish a separate ALS-specific LCD. ALS patients fall under Palmetto's Hospice — Neurological Conditions LCD (L34547) which uses similar functional/respiratory/nutritional decline criteria. Cross-reference the indicators above against L34547's supporting-findings list when building the Palmetto narrative.</p>",
        "how_to_use": "<p>ALS's linear-progression nature makes trajectory documentation especially powerful. Tables showing function-at-admission vs function-at-recert demonstrate rate of decline objectively. Combine with Hospice-Scale-FDR (Functional Decline Rate) and respiratory scales for the strongest picture.</p>",
    })

    # Cancer (from umbrella LCDs)
    cancer_section = slice_section(cgs_um, "Cancer Diagnoses", ["Dementia", "Alzheimer", "Amyotrophic", "HIV"], 4000)
    docs.append({
        "slug": "Cancer",
        "title": "Indicator Toolbox — Cancer / Malignancies",
        "summary": "Cross-MAC indicators for cancer-related terminal prognosis. Cancer eligibility centers on disease-progression evidence plus functional decline; specific staging is less relevant than the trajectory and response-to-therapy pattern.",
        "cgs_excerpt": cancer_section,
        "cgs_source": "CGS LCD L34538 — Cancer Diagnoses section",
        "ngs_excerpt": slice_section(ngs, "Cancer Diagnoses", ["Dementia", "Alzheimer", "Amyotrophic", "HIV"], 4000),
        "convergence": "<p>CGS, NGS, and Palmetto converge on: distant metastatic disease at presentation OR progression to metastatic disease with continued decline despite therapy, plus either (a) patient declines further anti-cancer therapy or (b) therapy is no longer providing benefit.</p>",
        "palette": """<ul>
<li><strong>Disease state:</strong> distant metastases at presentation OR progression from earlier stage to metastatic disease</li>
<li><strong>Therapy status (either):</strong> continued decline in spite of therapy; OR patient declines further therapy</li>
<li><strong>Functional marker:</strong> ECOG ≥3 or PPS/KPS &lt;50% usually accompanies hospice-appropriate cancer presentations</li>
<li><strong>Non-specific decline signals:</strong> weight loss, cachexia, rising pain requirements, falling albumin, recurrent hospitalizations, symptom burden rising (see Hospice-Scale-SEV for velocity tracking)</li>
<li><strong>Site-specific factors:</strong> liver metastases with hepatic failure signs, brain metastases with neurologic decline, bone metastases with pathologic fractures, pulmonary metastases with respiratory failure</li>
</ul>""",
        "palmetto_ref": "<p>Palmetto does NOT publish cancer-specific LCDs (unlike disease-specific LCDs). Cancer eligibility falls under the CMS Medicare Benefit Policy Manual Ch. 9 general standard: 6-month prognosis if the disease runs its normal course. Cancer patients are eligibility-evaluated on the progression + functional decline + patient-choice-to-forgo-anti-cancer-therapy triad.</p>",
        "how_to_use": "<p>The absence of a Palmetto cancer LCD means clinical judgment is even more central. The CGS/NGS cancer indicators above provide a structured framework CMS's general standard does not. Use them to organize the cancer-hospice narrative around metastatic state + therapy trajectory + functional decline.</p>",
    })

    # Adult Failure to Thrive / General Decline
    aftt_section = extracts["CGS-non-disease_specific.pdf"]
    docs.append({
        "slug": "Adult-Failure-To-Thrive",
        "title": "Indicator Toolbox — Adult Failure to Thrive / Debility",
        "summary": "Cross-MAC indicators for patients whose terminal trajectory is not captured by a single primary diagnosis. The picture emerges from cumulative decline across nutritional, functional, and clinical domains, plus medically-meaningful comorbidity burden.",
        "cgs_excerpt": aftt_section[:5500],
        "cgs_source": "CGS Hospice Terminal Prognosis: Non-Disease Specific (educational PDF)",
        "ngs_excerpt": slice_section(ngs, "Part I. Decline in Clinical Status", ["Part II", "PART II"], 5000),
        "convergence": "<p>CGS, NGS, and Palmetto converge on: documented <em>decline over time</em> (not a snapshot) across multiple domains — clinical status, symptoms, signs, performance status, ADLs. Required to document baseline PLUS follow-up. Decline must be non-reversible.</p>",
        "palette": """<ul>
<li><strong>Progression evidence:</strong> recurrent/intractable infections; progressive inanition (weight loss, shrinking anthropometrics, declining albumin); aspiration with inadequate intake</li>
<li><strong>Symptom escalation:</strong> rising dyspnea/respiratory rate, intractable cough, refractory nausea/vomiting, intractable diarrhea, pain requiring rising analgesic doses</li>
<li><strong>Signs of systemic failure:</strong> SBP declining below 90 (or postural hypotension), ascites, obstructive syndromes, edema, effusions, weakness, consciousness change</li>
<li><strong>Functional decline:</strong> KPS/PPS &lt;70% (lower thresholds for stroke/coma/HIV), 2+ ADL dependence, progressive loss of additional ADLs</li>
<li><strong>Comorbidity accumulation:</strong> multiple conditions whose severity collectively is expected to produce &lt;6-month prognosis even though no single condition would on its own (see Hospice-Scale-CCI Charlson Comorbidity Index)</li>
<li><strong>Healthcare utilization:</strong> rising ED visits, rising hospitalizations, rising physician visits — especially when for the same deteriorating process</li>
</ul>""",
        "palmetto_ref": "<p>Palmetto L34558 (Hospice Adult Failure to Thrive Syndrome) covers exactly this presentation. The supporting-findings section overlaps extensively with CGS/NGS non-disease-specific indicators. When AFTT is the Palmetto primary diagnosis, the indicators above are the substrate from which the narrative is built.</p>",
        "how_to_use": "<p>AFTT and debility are the diagnoses most often challenged by MAC auditors because they lack a single pathognomonic finding. Counter this by documenting MANY cross-MAC-recognized indicators — each one adds weight. The decline-over-time requirement means baseline AND follow-up data must both be charted; never present a single snapshot.</p>",
    })

    # Neurological (general, non-ALS, non-stroke)
    docs.append({
        "slug": "Neurological",
        "title": "Indicator Toolbox — Neurological Conditions (general)",
        "summary": "Cross-MAC indicators for advanced neurological conditions including Parkinson's disease, multiple sclerosis, Huntington's, and other progressive neurologic illnesses not captured by the separate ALS, dementia, and stroke/coma toolboxes.",
        "cgs_excerpt": "(CGS does not publish a standalone 'general neurological' hospice guideline. Neurological conditions are considered as part of the comorbidity list and are also addressed via the dementia and stroke/coma guidelines. For advanced Parkinson's, MS, or similar, use the non-disease-specific indicators combined with condition-specific findings below.)",
        "cgs_source": "Synthesized from CGS non-disease-specific guideline + umbrella LCD L34538 co-morbidity sections",
        "ngs_excerpt": "(NGS L33393 treats neurological conditions similarly — condition-specific progression combined with non-disease-specific decline indicators. Parkinson's, MS, Huntington's: no separate LCD criteria; picture built from functional + nutritional + complication-based indicators.)",
        "convergence": "<p>Across MACs, advanced neurological conditions qualify via: (1) documented condition-specific progression that is now refractory to disease-modifying therapy; (2) severe functional decline (KPS/PPS threshold); (3) critical complications (aspiration, recurrent UTI/pneumonia, pressure injuries, weight loss, dysphagia).</p>",
        "palette": """<ul>
<li><strong>Parkinson's disease advanced:</strong> Hoehn-Yahr Stage 4-5, bedbound, off-medication majority of day, dysphagia with aspiration, freezing/akinesia, dementia-PD overlap</li>
<li><strong>Multiple sclerosis advanced:</strong> EDSS 9.0-9.5 (bedbound, needs aide for all ADLs), progressive despite DMT, recurrent infections, aspiration, pressure injuries</li>
<li><strong>Huntington's disease:</strong> UHDRS functional capacity &lt;5/13, dysphagia, cachexia, unable to self-care</li>
<li><strong>Cross-cutting indicators (apply to any advanced neurologic):</strong> recurrent aspiration pneumonia, pyelonephritis/UTIs, sepsis, stage 3-4 pressure injuries, recurrent fever after antibiotics, inability to maintain fluid/calorie intake with weight loss &gt;10% or albumin &lt;2.5</li>
</ul>""",
        "palmetto_ref": "<p>Palmetto L34547 (Hospice — Neurological Conditions) is our governing LCD for this category. It consolidates Parkinson's, MS, ALS, Huntington's, and related conditions. The supporting-findings section explicitly lists the cross-cutting indicators above. Use this toolbox to enrich the narrative beyond checkbox-checking L34547.</p>",
        "how_to_use": "<p>Progressive neurologic illnesses often present with subtle but cumulative decline. Document baseline AND serial measurements to show trajectory. The Hospice-Scale-FDR in the corpus is particularly valuable for capturing rate of decline quantitatively.</p>",
    })

    return docs


async def render_all(docs):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 1000, "height": 1400})
        page = await ctx.new_page()
        out_paths = []
        for i, doc in enumerate(docs, 1):
            html = render_html(doc)
            fname = f"HospiceToolbox-{doc['slug']}.pdf"
            path = OUT_DIR / fname
            print(f"[{i}/{len(docs)}] {doc['slug']}... ", end="", flush=True)
            await page.set_content(html, wait_until="networkidle")
            await page.pdf(path=str(path), format="Letter",
                           margin={"top":"0.6in","right":"0.6in","bottom":"0.6in","left":"0.6in"},
                           print_background=True)
            print(f"PDF {path.stat().st_size:,} bytes")
            out_paths.append(path)
        await browser.close()
        return out_paths


async def main():
    extracts = load_extracts()
    docs = build_docs(extracts)
    print(f"Rendering {len(docs)} toolbox PDFs...")
    paths = await render_all(docs)
    print(f"\nAll rendered to {OUT_DIR}")
    for p in paths:
        print(f"  {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
