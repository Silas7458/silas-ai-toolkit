#!/usr/bin/env python3
"""Companion documents extracted from Corridor Hospice Quickflips
(Palmetto Version). The Corridor guide itself is in the notebook
(source_id 107f0982...). These companions promote specific gaps in
our corpus - levels of care, recertification workflow, nursing home
coordination, and a master cross-reference map of all 35 Quickflips.
"""

import asyncio, json, subprocess, sys
from pathlib import Path
from playwright.async_api import async_playwright

DRIVE_FOLDER_ID = "1zL6M_LdPtP52OyJNH0q0dy-j5PCg8z4u"
OUT_DIR = Path("corridor-companion-pdfs")
OUT_DIR.mkdir(exist_ok=True)

CSS = """
<style>
@page { size: Letter; margin: 0.6in; }
body { font-family: Georgia, serif; font-size: 11pt; line-height: 1.5; color: #222; }
h1 { font-size: 20pt; color: #1a3a52; border-bottom: 3px double #1a3a52; padding-bottom: 6px; }
h2 { font-size: 13pt; color: #1a3a52; border-bottom: 1px solid #c0c8d0; padding-bottom: 3px; margin-top: 16pt; }
h3 { font-size: 11.5pt; color: #2a4a62; margin-top: 10pt; }
.meta { font-size: 10pt; color: #555; font-style: italic; margin-bottom: 10pt; }
.tag { display: inline-block; background: #e8eef2; color: #1a3a52; padding: 2px 8px; border-radius: 4px; font-size: 9pt; margin-right: 4px; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 10pt; }
th { background: #1a3a52; color: white; padding: 5px 8px; text-align: left; }
td { padding: 4px 8px; border: 1px solid #bbb; vertical-align: top; }
tr:nth-child(even) td { background: #f6f9fb; }
.callout { background: #fff8e6; border-left: 4px solid #d4a017; padding: 8px 12px; margin: 10pt 0; font-size: 10.5pt; }
.loc-card { border: 2px solid #1a3a52; background: #f2f6f9; padding: 10px 14px; margin: 12pt 0; border-radius: 3px; }
.loc-title { font-weight: bold; color: #1a3a52; font-size: 13pt; font-family: Arial, sans-serif; margin-bottom: 4pt; }
.loc-sub { color: #666; font-style: italic; font-size: 10pt; margin-bottom: 6pt; }
ul { margin: 4pt 0 8pt 20pt; } li { margin-bottom: 3pt; }
blockquote { border-left: 3px solid #999; background: #f7f7f7; padding: 6px 12px; margin: 6pt 0; font-size: 10.5pt; font-style: italic; }
.source { margin-top: 16pt; padding-top: 8pt; border-top: 1px solid #ccc; font-size: 9pt; color: #666; font-style: italic; }
</style>
"""


def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def render(title, body, tag="Companion to Corridor Quickflips"):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">{CSS}</head><body>
<h1>{esc(title)}</h1>
<div class="meta"><span class="tag">{esc(tag)}</span>Companion reference extracted from Corridor Hospice Quickflips (Palmetto Version). Part of the Amerix Hospice Compliance knowledge corpus.</div>
{body}
<div class="source">Source: Corridor Hospice Quickflips: A Guide for Hospice Clinicians, Palmetto Version. See the original Corridor guide PDF in the Hospice regs Drive folder for full context.</div>
</body></html>"""


DOCS = []

# ==========================================================
# 1. LEVELS OF CARE GUIDE
# ==========================================================
DOCS.append({
    "slug": "Hospice-Levels-Of-Care-Guide",
    "title": "Hospice Levels of Care — Criteria and Documentation",
    "body": """
<p>Medicare pays hospice at four distinct levels of care. Choosing the correct level and documenting appropriately is both a clinical and a billing obligation. This guide synthesizes Corridor Hospice Quickflips #29-32 (Palmetto Version) with CMS Medicare Benefit Policy Manual Ch. 9.</p>

<div class="callout">
<strong>Key principle:</strong> Level of care is driven by the patient's and family's needs for symptom control at that moment in time, not by the patient's general prognosis. Routine Home Care is the default; the other three levels (Continuous Home Care, General Inpatient, Respite) are specific higher-intensity or specialized settings with distinct criteria and documentation requirements.
</div>

<h2>Level 1 — Routine Home Care (RHC)</h2>
<div class="loc-card">
<div class="loc-title">ROUTINE HOME CARE (RHC)</div>
<div class="loc-sub">Default level; most hospice days are RHC</div>
<p><strong>When:</strong> Patient is at home (or nursing home — see below) receiving standard hospice interdisciplinary services. Symptoms are manageable within the care plan.</p>
<p><strong>Documentation focus:</strong> Standard care plan, IDG oversight, visit frequencies appropriate to patient needs, medications for pain/symptom management.</p>
</div>

<h2>Level 2 — Continuous Home Care (CHC)</h2>
<div class="loc-card">
<div class="loc-title">CONTINUOUS HOME CARE (CHC)</div>
<div class="loc-sub">Quickflip #29, page 95</div>
<p><strong>When to use (per Corridor):</strong> Nursing care may be covered on a continuous basis for as much as 24 hours a day during periods of crisis as necessary to maintain the patient at home. A period of crisis is a period in which the patient requires continuous care (at least 8 hours per 24-hour period) to achieve palliation or management of acute medical symptoms.</p>
<p><strong>Criteria:</strong></p>
<ul>
<li>Patient is experiencing a dying process that is NOT severe and without continuous care the patient will need to be hospitalized</li>
<li>A dying patient can be assured symptoms can be controlled during continuous care</li>
<li>Caregiver has a critical need or is unable to care for patient</li>
</ul>
<p><strong>Coverage requirements (per Corridor):</strong></p>
<ul>
<li>Continuous care is meant to be for very brief periods — generally just a few days</li>
<li>When continuous care is given, it must be documented that the entire team is working with the patient and family to manage symptoms effectively without continuous care</li>
<li>The documentation for starting and maintaining continuous care must reflect the crisis. The Plan of Care must note: "Continuous care requested due to ___________" and document the "dying process" or "end-of-life care" is not acceptable; rather, specifying the distressing symptoms requires continuous care and/or close monitoring is expected</li>
</ul>
</div>

<h2>Level 3 — General Inpatient Care (GIP)</h2>
<div class="loc-card">
<div class="loc-title">GENERAL INPATIENT CARE (GIP)</div>
<div class="loc-sub">Quickflip #30, page 97; Quickflip #31 (Psychosocial Crisis), page 99</div>
<p><strong>When to use (per Corridor):</strong> Access to general inpatient care (GIP) is made available to all hospice patients who are in need of pain control or symptom management that cannot be provided in any other setting.</p>
<p><strong>Documentation must answer the question: "Why did the patient need to be in the facility and what could not be tried at home?"</strong></p>
<p><strong>Indications — patient/family in need of GIP (per Corridor):</strong></p>
<ul>
<li>Symptoms require intensity of care unavailable in other settings due to:
  <ul>
  <li>Bleeding that won't stop</li>
  <li>Pain, nausea, agitation, changes in cognition, delirium</li>
  <li>Terminal agitation, impression sensitive to changes</li>
  <li>Medication adjustment that must be monitored 24/7</li>
  <li>Stabilizing treatment that cannot take place at home</li>
  </ul>
</li>
<li><strong>Supporting documentation might include:</strong>
  <ul>
  <li>Pain, nausea worsening due to caregiver failure</li>
  <li>Nurses assessments made by a doctor or nurse</li>
  <li>Management adjustments in response to the patient's care</li>
  <li>Medication decisions made for the care of the patient</li>
  <li>Stabilizing treatment that cannot take place at home</li>
  </ul>
</li>
</ul>
<p><strong>What GIP is NOT (Quickflip #31 — critical guidance):</strong></p>
<blockquote>
In April 2007, CMS issued a transmittal (1539) that clarified that GIP cannot be used for caregiver breakdown, stating: "...some hospices are billing Medicare for 'caregiver breakdown' at the higher 'general inpatient' level, rather than the lower payment for 'inpatient respite' or 'routine home care' levels of care. To receive payment for 'general inpatient care' under the Medicare hospice benefit, beneficiaries must require an intensity of care directed towards pain control and symptom management that cannot be managed in any other setting."
</blockquote>
<p>Therefore GIP must be related to symptoms as outlined above. Psychosocial crisis of the caregiver may result in use of respite care (Level 4), not GIP.</p>
</div>

<h2>Level 4 — Respite Care</h2>
<div class="loc-card">
<div class="loc-title">RESPITE CARE</div>
<div class="loc-sub">Quickflip #32, page 101</div>
<p><strong>When to use (per Corridor):</strong> Respite care is short-term inpatient care provided to relieve family members or other persons caring for the patient at home. Respite care may be provided only on an occasional basis. Respite care may be covered for 5 consecutive days at a time including the date of admission, but not counting the date of discharge.</p>
<p><strong>Respite care also can be used in cases of caregiver breakdown, as clarified by the CMS transmittal above.</strong></p>
<p><strong>When patients can be moved to hospice respite care (per Corridor):</strong></p>
<ul>
<li>Document reasons respite care is taken to provide a break for the caregivers. Hospices must include within the following details:
  <ul>
  <li>Document respite care as a planned break to provide a break for the caregivers, not to provide more care</li>
  <li>If due to caregiver breakdown, document the events leading to the request for respite care and the date of admission but NOT including the date of discharge</li>
  <li>Don't forget to document your collaborative care planning and communication with family, staff</li>
  <li>Respite care may not be reimbursed for more than five (5) consecutive days at a time. If longer stays in respite, have an elective surgery or do anything they wish that does not fall into "respite"</li>
  </ul>
</li>
<li>If the patient is receiving other inpatient respite care, the day of the admission is not the day of discharge</li>
<li>Inpatient respite can only be provided in the following facilities:
  <ul>
  <li>A Medicare-certified hospice inpatient facility</li>
  <li>A Medicare-certified hospital or skilled nursing facility that has the capacity to provide 24-hour nursing if the patient needs it</li>
  <li>A Medicaid-certified nursing facility</li>
  </ul>
</li>
</ul>
</div>

<h2>Level of care decision at a glance</h2>
<table>
<tr><th>Patient/caregiver situation</th><th>Correct level</th></tr>
<tr><td>Symptoms managed, care at home is sustainable</td><td><strong>Routine Home Care (RHC)</strong></td></tr>
<tr><td>Symptom crisis requiring continuous (≥8 hrs/day) nursing intervention to avoid hospitalization</td><td><strong>Continuous Home Care (CHC)</strong></td></tr>
<tr><td>Symptom intensity (pain, delirium, bleeding, terminal agitation, etc.) unmanageable in any other setting</td><td><strong>General Inpatient (GIP)</strong></td></tr>
<tr><td>Caregiver needs relief (planned or due to breakdown); patient symptoms manageable</td><td><strong>Respite Care (≤5 consecutive days)</strong></td></tr>
</table>

<h2>Integration with existing corpus</h2>
<ul>
<li><strong>Four-Ways-To-Document-Eligibility.pdf</strong>: level-of-care decisions are independent of the eligibility path, but GIP documentation often uses the same symptom-escalation evidence that supports continued eligibility</li>
<li><strong>Hospice-Scale-SEV (Symptom Escalation Velocity)</strong>: the quantitative anchor for GIP justification</li>
<li><strong>Hospice-Scale-PAINAD / FLACC</strong>: for non-verbal pain assessment that may support GIP</li>
<li><strong>CMS MBPM Ch. 9</strong>: regulatory authority for the four levels of care</li>
</ul>
""",
})

# ==========================================================
# 2. RECERTIFICATION WORKFLOW
# ==========================================================
DOCS.append({
    "slug": "Hospice-Recertification-Workflow",
    "title": "Hospice Recertification — Workflow and Documentation",
    "body": """
<p>Recertification is the continuous re-examination of a patient's terminal status. Unlike the initial certification (a one-time event at admission), recertifications happen every 90 days for the first two benefit periods and every 60 days thereafter — indefinitely, for as long as the patient remains hospice-appropriate. Poor recertification documentation is the single most common cause of hospice eligibility denials.</p>

<p>This guide synthesizes Corridor Hospice Quickflips #28 (Palmetto Version), the CMS Medicare Benefit Policy Manual Ch. 9 recertification requirements, and the Four-Ways-To-Document-Eligibility framework.</p>

<h2>Core principle (per Corridor)</h2>
<blockquote>
Assessment of eligibility should be continuous. The recertification evaluation should intensify at least two weeks before the actual recert date to allow for close monitoring and assessment of the patient's condition. Remember, ineligible patients should be discharged as soon as the team determines that they are ineligible; you should not wait until recert time.
</blockquote>

<h2>Recertification workflow (8 steps per Corridor Quickflip #28)</h2>
<ol>
<li><strong>Review the LCDs for the patient's terminal diagnosis.</strong> Specifically, Palmetto's disease-specific LCDs (L34544 Liver, L34547 Neurological, L34548 Cardiopulmonary, L34558 AFTT, L34559 Renal, L34567 Alzheimer's) and the supporting-findings lists.</li>
<li><strong>Present a review of the patient's disease progression since the last recert date.</strong> Allow time for comparisons to baseline data and data from previous points in time, to accurately demonstrate disease progression.</li>
<li><strong>Discuss symptomatology in terms of the LCD.</strong> Does this patient have a life expectancy of six months or less? In addition to meeting the LCD criteria, what additional patient-specific symptoms/decline in clinical status are evident to support the six-month terminal prognosis?</li>
<li><strong>Document the discussion, leading up to the decision.</strong> Capture both the finding AND the clinical reasoning.</li>
<li><strong>If the team decides to recert:</strong> make the following forward (for problems, goals and interventions appropriate for all involved):
  <ul>
  <li>Update the Plan of Care</li>
  <li>Obtain a recertification of terminal illness from the hospice medical director</li>
  <li>Document in the chart a narrative of the clinical findings that supports a six-month or less prognosis. Notable features of the narrative: the patient's state when admitted to hospice, the patient's course, and subsequent recertification</li>
  </ul>
</li>
</ol>

<h2>The "drift" problem and how to counter it</h2>
<p>A common audit-vulnerability pattern: a patient recertifies multiple times because "they look the same as last time" — but by recert #5 or #6 the justification has drifted from specific decline evidence to habitual renewal. Counter this:</p>
<ul>
<li>Treat every recertification as a fresh clinical question: "Is this patient hospice-appropriate TODAY based on TODAY's findings?"</li>
<li>Maintain baseline data (at admission) AND follow-up data (ongoing) so trajectory is always provable</li>
<li>Use the Four-Ways-To-Document-Eligibility framework explicitly — if Path 1 (Perfect Fit) stops applying, transition to Path 2 (Close Fit + Rapid Decline) with concrete decline evidence</li>
<li>Quantify decline with scales: PPS, FAST, BODE, MELD, FDR (Functional Decline Rate), NDI (Nutritional Decline Index), IRS (Irreversibility Score), SEV (Symptom Escalation Velocity)</li>
<li>If a patient has stabilized and no longer meets any path, discharge — do not recertify and "see what happens"</li>
</ul>

<h2>Narrative quality</h2>
<p>The recertification narrative should be able to stand alone — a reviewer should be able to read ONLY this narrative and conclude "yes, 6-month prognosis is supported." That means:</p>
<ul>
<li>Concrete findings with dates (not "weight loss" but "weight dropped from 148 lb at admission to 132 lb on 2026-03-15 and 127 lb on 2026-04-10")</li>
<li>Specific to the patient's disease (cite the relevant LCD criteria by finding)</li>
<li>Forward-looking (why is the team predicting &lt;6 months even if the patient has already been on hospice for &gt;6 months?)</li>
<li>Acknowledge any stabilization or plateau — and explain why 6-month prognosis still holds despite plateaus</li>
</ul>

<h2>Integration with corpus</h2>
<ul>
<li><strong>Four-Ways-To-Document-Eligibility.pdf</strong>: the path framework applies at recertification as much as at admission</li>
<li><strong>Palmetto-JMHHH-LCD-*</strong>: the governing criteria to re-apply at each recert</li>
<li><strong>Hospice-Scale-FDR, NDI, IRS, SEV, MCS</strong>: quantified decline measures for the narrative</li>
<li><strong>CMS-MBPM-Ch9</strong>: recertification regulatory requirements (60/90 day schedule, face-to-face requirements)</li>
<li><strong>HospiceToolbox-General-Non-Disease-Specific.pdf</strong>: cross-cutting decline indicators</li>
</ul>
""",
})

# ==========================================================
# 3. NURSING HOME COORDINATION
# ==========================================================
DOCS.append({
    "slug": "Hospice-Nursing-Home-Coordination",
    "title": "Hospice Care in a Nursing Home — Documentation and Coordination",
    "body": """
<p>When a hospice patient resides in a nursing home, documentation and coordination requirements are ABOVE AND BEYOND routine home care. Hospice coordination with the facility is a specific Medicare expectation because two care teams are simultaneously responsible for the patient, and Medicare pays both. Failure to document coordination is a frequent audit finding.</p>

<p>This guide synthesizes Corridor Hospice Quickflips #33 (Palmetto Version) with the Medicare Conditions of Participation for hospice.</p>

<h2>Core expectation (per Corridor)</h2>
<blockquote>
A member of the interdisciplinary team will be designated for a patient residing in the facility to provide overall coordination of hospice care and communication with facility staff. This helps ensure quality of care for the patient and family.
</blockquote>

<h2>Required documentation delivered to the facility</h2>
<p>In addition to routine home care documentation, for nursing home patients the hospice clinicians need to document that the following was delivered to the facility:</p>
<ul>
<li>Most recent Plan of Care</li>
<li>Hospice election form and advance directives</li>
<li>Physician certification and recertification of terminal illness</li>
<li>Contact information for hospice personnel involved in hospice care of the patient</li>
<li>Instructions on how to access hospice's 24-hour on call system</li>
<li>Hospice medication information</li>
<li>Hospice physician or attending physician (if any) orders</li>
</ul>

<h2>Coordinated Plan of Care — required elements</h2>
<ul>
<li>What the nursing home staff is responsible for and what are hospice staff responsibilities</li>
<li>Problems, patient goals, interventions and palliative outcomes on the hospice Plan of Care are consistent with the Plan of Care at the facility</li>
<li>Medical orders, updates, and changes made by the nursing home</li>
<li>Coordination of care</li>
</ul>

<h2>Common audit-vulnerability patterns in NH hospice</h2>
<ul>
<li>Two unreconciled care plans (hospice has one, nursing home has another) — a finding for both payer audits and state surveys</li>
<li>Missing or stale distribution of the hospice election form, advance directives, or POC at the facility</li>
<li>Unclear delineation of which team is responsible for which tasks (e.g., who is managing the patient's anticoagulant? pain meds? skincare?)</li>
<li>No documentation of on-call access for facility staff</li>
<li>Changes initiated by facility staff without hospice team awareness</li>
</ul>

<h2>Operational checklist for the hospice IDT member assigned to NH coordination</h2>
<ol>
<li>At admission to hospice (patient already in NH): deliver the full documentation packet (above) to the nursing supervisor</li>
<li>Establish an IDT-side point of contact and verify the facility's point of contact</li>
<li>Reconcile POC with facility POC; document the reconciliation and who is responsible for what</li>
<li>Communicate 24-hour on-call access and confirm the facility has tested it</li>
<li>At every IDT visit, check in with facility staff — changes in patient status, concerns, observations</li>
<li>At every recertification: refresh the certification/recertification copies with the facility</li>
<li>Document ALL communications with the facility in the hospice chart</li>
</ol>

<h2>Integration with corpus</h2>
<ul>
<li><strong>Hospice-Levels-Of-Care-Guide.pdf</strong>: NH residents can be at any level of care (routine, respite, GIP in hospital, continuous)</li>
<li><strong>Hospice-Scale-Mitchell-MRI</strong>: mortality risk index specifically validated in nursing home residents with advanced dementia</li>
<li><strong>Palmetto-JMHHH-LCD-L34567 Alzheimer's</strong>: many NH hospice patients have dementia as the primary terminal diagnosis</li>
<li><strong>CMS MBPM Ch. 9</strong>: regulatory basis for the nursing-home-specific coordination requirements</li>
</ul>
""",
})

# ==========================================================
# 4. CORRIDOR QUICKFLIPS INDEX MAP (cross-reference all 35)
# ==========================================================
DOCS.append({
    "slug": "Corridor-Quickflips-Index-Map",
    "title": "Corridor Hospice Quickflips — Index and Cross-Reference Map",
    "body": """
<p><strong>Purpose.</strong> The Corridor Hospice Quickflips (Palmetto Version) is a 128-page scanned clinical guide containing 35 numbered one-page reference documents. This index maps every Quickflip to its page number, topic, and related sources elsewhere in the Amerix Hospice Compliance corpus. Use this as the gateway into the Corridor guide.</p>

<div class="callout">
<strong>Publisher:</strong> Corridor. <strong>Version:</strong> Palmetto. <strong>Scope per Corridor's own limiting conditions (page 127):</strong> "...intended to encourage critical thinking and facilitate the discussion of the Medicare Conditions of Participation, eligibility, documentation, the interpretive guidelines, Medicare Administrative Contractor manuals, and efficiencies within hospice practice. It is not intended to serve as a substitute for the COPs or consultation with any regulatory agency."
</div>

<h2>Section 1 — Eligibility and Disease-Specific Criteria (Quickflips #1-#12)</h2>
<table>
<tr><th>#</th><th>Topic</th><th>Corridor page</th><th>Our corpus cross-ref</th></tr>
<tr><td>1</td><td>Local Coverage Determinations (overview, Four Ways)</td><td>9</td><td>Four-Ways-To-Document-Eligibility.pdf; all Palmetto-JMHHH-LCD-*</td></tr>
<tr><td>2</td><td>NHPCO General Guidelines</td><td>11</td><td>HospiceToolbox-General-Non-Disease-Specific.pdf; MAHC-AHCPR reference</td></tr>
<tr><td>3</td><td>Comorbidities</td><td>13</td><td>Hospice-Scale-CCI (Charlson); HospiceToolbox-Adult-Failure-To-Thrive</td></tr>
<tr><td>4</td><td>Liver Disease</td><td>15</td><td>Palmetto-JMHHH-LCD-L34544; HospiceToolbox-Liver; Hospice-Scale-MELD</td></tr>
<tr><td>5</td><td>Cardiopulmonary Conditions</td><td>17</td><td>Palmetto-JMHHH-LCD-L34548; HospiceToolbox-Cardiac/Pulmonary; Hospice-Scale-BODE/SHFM</td></tr>
<tr><td>6</td><td>ICF Worksheet - Cardiopulmonary</td><td>21</td><td>ICF Manual hospice.pdf (WHO ICF framework)</td></tr>
<tr><td>7</td><td>Neurological Conditions</td><td>27</td><td>Palmetto-JMHHH-LCD-L34547; HospiceToolbox-Neurological; HospiceToolbox-ALS</td></tr>
<tr><td>8</td><td>ICF Worksheet - Neurological Examples</td><td>37</td><td>ICF Manual hospice.pdf</td></tr>
<tr><td>9</td><td>Failure to Thrive</td><td>43</td><td>Palmetto-JMHHH-LCD-L34558; HospiceToolbox-Adult-Failure-To-Thrive</td></tr>
<tr><td>10</td><td>Renal Failure</td><td>47</td><td>Palmetto-JMHHH-LCD-L34559; HospiceToolbox-Renal</td></tr>
<tr><td>11</td><td>HIV</td><td>51</td><td>HospiceToolbox-HIV</td></tr>
<tr><td>12</td><td>Alzheimer's Disease and Related Disorders</td><td>53</td><td>Palmetto-JMHHH-LCD-L34567; HospiceToolbox-Dementia-Alzheimers; Hospice-Scale-Mitchell-MRI</td></tr>
</table>

<h2>Section 2 — Assessment, Care Planning, and Documentation (Quickflips #13-#22)</h2>
<table>
<tr><th>#</th><th>Topic</th><th>Corridor page</th><th>Our corpus cross-ref</th></tr>
<tr><td>13</td><td>Assessment and Care Planning</td><td>55</td><td>(Clinical IDT workflow - primarily lives in the Corridor source)</td></tr>
<tr><td>13a</td><td>Hospice Item Set (HIS)</td><td>59</td><td>CMS-HOPE-Guidance-Manual-v1.00.pdf (HOPE supersedes HIS as of Oct 2025)</td></tr>
<tr><td>14</td><td>Visit Frequencies - Nurses</td><td>61</td><td>(Operational guidance - lives in Corridor source)</td></tr>
<tr><td>15</td><td>Visit Frequencies - Social Workers &amp; Spiritual Care Counselors</td><td>63</td><td>(Operational guidance - lives in Corridor source)</td></tr>
<tr><td>16</td><td>Hospice Dates and Times</td><td>65</td><td>(Certification/recertification timing - lives in Corridor source)</td></tr>
<tr><td>17</td><td>Psychosocial and Spiritual Goals</td><td>69</td><td>(Lives in Corridor source)</td></tr>
<tr><td>18</td><td>Social Worker Documentation</td><td>71</td><td>(Lives in Corridor source)</td></tr>
<tr><td>19</td><td>Spiritual Care Documentation</td><td>73</td><td>(Lives in Corridor source - "as-evidenced-by / interventions" pattern)</td></tr>
<tr><td>20</td><td>Attending Physician</td><td>75</td><td>CMS-MBPM-Ch9 (attending physician rules)</td></tr>
<tr><td>21</td><td>Consulting Physicians</td><td>77</td><td>(Lives in Corridor source)</td></tr>
<tr><td>22</td><td>IDT Meeting Do's and Don'ts</td><td>79</td><td>(Lives in Corridor source)</td></tr>
</table>

<h2>Section 3 — Operational Practices (Quickflips #23-#27)</h2>
<table>
<tr><th>#</th><th>Topic</th><th>Corridor page</th><th>Our corpus cross-ref</th></tr>
<tr><td>23</td><td>Creating a Culture of Eligibility</td><td>83</td><td>Four-Ways-To-Document-Eligibility.pdf (philosophical alignment)</td></tr>
<tr><td>24</td><td>Presenting a New Admission</td><td>85</td><td>(Operational - Corridor source)</td></tr>
<tr><td>25</td><td>Presenting a Case for Review</td><td>87</td><td>(Operational - Corridor source)</td></tr>
<tr><td>26</td><td>Reviewing Deaths</td><td>89</td><td>(Operational - Corridor source)</td></tr>
<tr><td>27</td><td>Complications for Grief</td><td>91</td><td>(Bereavement - Corridor source)</td></tr>
</table>

<h2>Section 4 — Transitions and Levels of Care (Quickflips #28-#35)</h2>
<table>
<tr><th>#</th><th>Topic</th><th>Corridor page</th><th>Our corpus cross-ref</th></tr>
<tr><td>28</td><td>Recertification</td><td>93</td><td>Hospice-Recertification-Workflow.pdf (companion)</td></tr>
<tr><td>29</td><td>Continuous Care</td><td>95</td><td>Hospice-Levels-Of-Care-Guide.pdf (companion)</td></tr>
<tr><td>30</td><td>General Inpatient Care</td><td>97</td><td>Hospice-Levels-Of-Care-Guide.pdf</td></tr>
<tr><td>31</td><td>GIP Due to Psychosocial Crisis</td><td>99</td><td>Hospice-Levels-Of-Care-Guide.pdf (critical: CMS Transmittal 1539 clarification)</td></tr>
<tr><td>32</td><td>Respite Care</td><td>101</td><td>Hospice-Levels-Of-Care-Guide.pdf</td></tr>
<tr><td>33</td><td>Hospice Care in a Nursing Home</td><td>103</td><td>Hospice-Nursing-Home-Coordination.pdf (companion)</td></tr>
<tr><td>34</td><td>Discharge and Disposition Planning</td><td>105</td><td>(Lives in Corridor source)</td></tr>
<tr><td>35</td><td>SOAP Documentation</td><td>109</td><td>(Lives in Corridor source - Subjective/Objective/Assessment/Plan)</td></tr>
</table>

<h2>How to use this map</h2>
<ol>
<li><strong>When NotebookLM cites the Corridor Quickflips</strong>, look up the Quickflip number to locate the specific page and its scope.</li>
<li><strong>When you want operational / clinical workflow guidance</strong> (visit frequencies, IDT meeting patterns, SOAP documentation), query the Corridor guide directly — most Section 2-4 content lives there and is best-quoted verbatim.</li>
<li><strong>When you want regulatory / eligibility content</strong>, query the Palmetto LCDs first, then the Corridor guide as triangulating commentary.</li>
<li><strong>When a topic has both a companion doc AND Corridor content</strong>, the companion is the distilled version; the Corridor Quickflip is the canonical source. Both will be cited on comprehensive queries.</li>
</ol>
""",
})


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width":1000,"height":1400})
        page = await ctx.new_page()
        for i, doc in enumerate(DOCS, 1):
            html = render(doc["title"], doc["body"])
            path = OUT_DIR / f"{doc['slug']}.pdf"
            print(f"[{i}/{len(DOCS)}] {doc['slug']}...", end=" ", flush=True)
            await page.set_content(html, wait_until="networkidle")
            await page.pdf(path=str(path), format="Letter",
                           margin={"top":"0.6in","right":"0.6in","bottom":"0.6in","left":"0.6in"},
                           print_background=True)
            print(f"PDF {path.stat().st_size:,} bytes")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
