"""Hospice assessment scale reference content.

Each entry is a self-contained reference designed to answer queries
of the form "given inputs X, Y, Z, what is this patient's score and
what does that mean for hospice appropriateness?"

The content emphasizes the picture-painting philosophy: hospice
appropriateness is a constellation of findings. Scales quantify
fragments of that picture. Every scale ends with guidance on what
else should be true alongside a concerning score for the picture
to support hospice eligibility.
"""

SCALES = [

# =====================================================================
# AMERIX COMPOSITE INDICES (custom framework tools)
# =====================================================================

    {
        "acronym": "NDI",
        "full_name": "Nutritional Decline Index",
        "category": "Amerix Composite / Nutrition",
        "source": "Amerix Medical Consulting composite index. Synthesizes CMS LCD nutritional thresholds (weight loss criteria) with standard lab markers and observed intake patterns.",
        "summary": "Composite index quantifying nutritional decline trajectory. Integrates percent body weight loss over defined intervals, laboratory markers of visceral protein stores, and observed oral intake. Designed to convert a scattered set of nutrition signals into a single trend-aware number.",
        "what_it_measures": "Three orthogonal dimensions of nutrition failure: (1) anthropometric decline (weight trajectory), (2) biochemical protein stores (albumin, prealbumin), and (3) behavioral/functional intake (observed meal completion, supplement dependence, dysphagia severity). Serial NDI measurements reveal velocity of decline, which is often more prognostic than any single snapshot.",
        "scoring": "Scored as a weighted composite. Each component contributes 0-3 points; total 0-9. Component definitions:\n\n**Weight loss component:** 0 = stable, 1 = 5-9% loss in 6 months, 2 = 10% loss in 6 months (meets Palmetto LCD threshold), 3 = >10% loss in 3 months OR sustained loss despite nutrition interventions.\n\n**Biochemical component:** 0 = albumin >=3.5 g/dL, 1 = albumin 3.0-3.4, 2 = albumin 2.5-2.9, 3 = albumin <2.5 OR prealbumin <10 mg/dL. Note: albumin is confounded by inflammation, hydration, hepatic synthesis.\n\n**Intake component:** 0 = >=75% of meals, 1 = 50-74%, 2 = 25-49% (often with supplements), 3 = <25% OR dysphagia requiring pureed/thickened OR tube-fed with declining tolerance.",
        "scoring_table": {
            "headers": ["Component", "0 pts", "1 pt", "2 pts", "3 pts"],
            "rows": [
                ["Weight loss", "Stable", "5-9% / 6 mo", "10% / 6 mo", ">10% / 3 mo or refractory"],
                ["Albumin / Prealbumin", ">=3.5 g/dL", "3.0-3.4", "2.5-2.9", "<2.5 or prealb <10"],
                ["Observed intake", ">=75% meals", "50-74%", "25-49%", "<25% or severe dysphagia"],
            ],
        },
        "interpretation": "Total score ranges 0 (intact nutrition) to 9 (advanced nutritional failure). More important than the number is the **velocity**: an NDI rising from 2 to 6 over two months signals rapid trajectory toward end-of-life nutritional failure. A stable NDI of 6, while concerning, may reflect a chronic condition that has plateaued. Always interpret in the context of the underlying disease, appetite interventions already tried, and patient goals of care.",
        "interpretation_table": {
            "headers": ["Total Score", "Clinical meaning", "Typical correlation"],
            "rows": [
                ["0-2", "Minimal nutritional decline", "Nutrition usually not the limiting prognostic factor"],
                ["3-5", "Moderate decline", "Nutrition is contributing to overall trajectory; assess reversibility"],
                ["6-7", "Significant decline", "Meets LCD thresholds in most disease categories; hospice-supportive"],
                ["8-9", "Advanced nutritional failure", "Strongly supports terminal prognosis in the context of an underlying life-limiting illness"],
            ],
        },
        "when_to_use": "At admission and serially (typically every 14 days) for patients on hospice or being evaluated for eligibility. Particularly useful in dementia, failure to thrive, heart failure cachexia, COPD cachexia, and end-stage liver disease where nutritional decline is a leading prognostic signal but is easy to miss when documented piecemeal.",
        "hospice_relevance": "Palmetto GBA Article A53056 (Hospice: Documenting Weight Loss for Beneficiaries with Non-Neoplastic Conditions) is the anchor documentation requirement for nutrition in hospice eligibility. The NDI operationalizes what A53056 asks for. Weight loss of 10% in 6 months, albumin <2.5, and intake <50% are each individually referenced in multiple Palmetto LCDs (L34544 Liver, L34547 Neurological, L34548 Cardiopulmonary, L34558 Adult Failure to Thrive, L34559 Renal, L34567 Alzheimer's).",
        "worked_examples": [
            {
                "label": "Pt A — 84F with advanced Alzheimer's, FAST 7c",
                "body": "Weight 118 lb down from 132 lb 5 months ago (10.6% loss in 5 mo = 2 pts). Albumin 2.7 g/dL (2 pts). Intake 30% of meals, spitting out pureed food (2 pts). **NDI total = 6.** Combined with FAST 7c, speech <=6 words, and recurrent aspiration, this picture supports Alzheimer's hospice eligibility per L34567."
            },
            {
                "label": "Pt B — 67M with COPD on home O2",
                "body": "BMI 19.2 (down from 23.0 over 4 months, ~16% loss = 3 pts). Albumin 3.1 (1 pt). Intake ~60% (1 pt), uses nutritional supplements. **NDI total = 5.** When combined with BODE = 8, two hospitalizations in 3 months, and oxygen-dependent at rest, supports Cardiopulmonary LCD eligibility."
            },
        ],
        "picture_fit": "NDI alone does not make someone hospice-appropriate. A high NDI must sit alongside: (1) an underlying life-limiting illness with a defined terminal trajectory; (2) nutritional decline that is NOT easily reversible (not due to transient causes like acute illness, depression responsive to treatment, or correctable dysphagia); (3) a broader functional and clinical decline consistent with a 6-month prognosis if the condition runs its normal course. A robust 40-year-old recovering from flu can have an NDI of 4 transiently - that is not hospice. A bedbound 85-year-old with advanced dementia and NDI of 6 is painting a very different picture.",
        "pitfalls": "- Albumin is falsely LOW in inflammation, overhydration, nephrotic syndrome, and protein-losing enteropathy - do not treat it as a pure nutrition marker.\n- Pre-albumin has a 2-3 day half-life so it responds faster but is similarly confounded.\n- Weight gain from edema or ascites in CHF/liver disease masks true nutritional decline - document dry weight or note edema status.\n- A one-time weight measurement is not a trajectory - serial weights are mandatory.\n- Intake estimates from family are often over-optimistic - triangulate with nursing observation.",
        "references": "- Palmetto GBA Article A53056 Hospice: Documenting Weight Loss for Beneficiaries with Non-Neoplastic Conditions\n- CMS Medicare Benefit Policy Manual Ch. 9 \u00a740.1.2\n- Reference: Stratton RJ et al. Disease-Related Malnutrition (CABI, 2003)",
    },

    {
        "acronym": "SEV",
        "full_name": "Symptom Escalation Velocity",
        "category": "Amerix Composite / Symptom Burden",
        "source": "Amerix Medical Consulting composite index. Quantifies the rate of change in symptom burden, not the absolute level.",
        "summary": "Rate-of-change measure tracking acceleration in symptom burden (pain, dyspnea, agitation, nausea, diarrhea, delirium) over defined time windows. Captures the velocity of decline, not the absolute symptom level. A stable high-symptom patient and an accelerating lower-symptom patient tell different prognostic stories; SEV distinguishes them.",
        "what_it_measures": "Change in composite symptom burden between two timepoints, expressed as a velocity: (Current composite symptom score - Prior composite symptom score) / (days between). The composite score is the sum of 0-10 severity ratings for the tracked symptoms (or the count of daily PRN doses for each).",
        "scoring": "**Step 1 - Composite Symptom Score (CSS) at time T:** Sum of 0-10 severity ratings (patient or clinician-rated) for: pain, dyspnea at rest, dyspnea on minimal exertion, nausea, anorexia, fatigue, agitation, confusion/delirium.\n\n**Step 2 - SEV velocity:** (CSS at day 14) - (CSS at day 0), divided by 14. Express as CSS-points per week.\n\n**Step 3 - PRN escalation multiplier:** count daily PRN opioid, anxiolytic, or antiemetic doses. If PRN count has doubled or more between intervals, multiply SEV by 1.5 to reflect true escalation (symptoms outrunning scheduled medications).",
        "interpretation": "SEV is interpreted alongside the absolute symptom level:\n- **Low absolute burden + low SEV:** stable, not yet approaching terminal phase.\n- **High absolute burden + low SEV:** chronically high symptoms; prognostically uncertain without other signals.\n- **Rising SEV (any absolute level):** concerning. An SEV > 1 CSS-point per week or a doubling of PRN use over 2 weeks is a signal of accelerating decline.\n- **High absolute + high SEV:** actively dying trajectory; ensure hospice level-of-care matches needs (consider GIP for symptom crisis).",
        "when_to_use": "Recalculate at every IDG meeting and any time a PRN order is increased or a scheduled dose is titrated. SEV is most sensitive in the 4-8 weeks before a transition to actively dying, when absolute symptom scores may still be borderline but the slope is steepening.",
        "hospice_relevance": "Not a Medicare-required score, but the trajectory data SEV captures is exactly what CMS MBPM Ch 9 expects in recertification narratives: evidence the patient is on a decline trajectory toward the expected prognosis. SEV documentation strengthens recertification and appeals against ADR/TPE denials that claim 'no decline' based on a snapshot comparison.",
        "worked_examples": [
            {
                "label": "Pt C — recertification at 90 days, CHF Stage IV",
                "body": "Day 0 CSS: pain 3 + dyspnea-at-rest 2 + dyspnea-exertion 4 + fatigue 5 + anorexia 3 = 17. Day 14 CSS: 4 + 4 + 6 + 7 + 5 = 26. SEV = (26-17)/14 = 0.64 CSS-points/day = 4.5/week. PRN MSIR has escalated from 2 to 6 daily doses (tripled). Adjusted SEV with 1.5x multiplier = 6.75/week. **High SEV, high absolute. Trajectory strongly supports continued hospice eligibility.**"
            },
            {
                "label": "Pt D - COPD, 6 months on hospice, appears stable",
                "body": "Day 0 CSS = 14. Day 14 CSS = 15. SEV = 0.07/day = 0.5/week. PRN stable. **Low SEV, moderate absolute.** Combined with stable BODE and stable weight, this is a 'plateau' picture - the recertification narrative must find other decline signals or risk ADR flag."
            },
        ],
        "picture_fit": "A rising SEV is a finding, not a diagnosis. It must be attributable to the underlying terminal illness, not to a potentially reversible cause (new infection, uncontrolled pain responsive to one titration, newly discovered fracture). If the SEV rise is due to a reversible complication, treat the complication and recheck - do not use it as evidence of terminal trajectory. Picture-painting principle: escalating symptoms consistent with the natural history of the known life-limiting illness, not responsive to usual palliative interventions, alongside declining function and nutrition.",
        "pitfalls": "- Do not compare CSS across patients - use SEV only intra-patient, over time.\n- Caregiver-rated severity tends to over-estimate compared to patient-rated; pick one source and stick with it.\n- A transient SEV spike from an acute event (UTI, pneumonia) is not terminal trajectory - smooth over 2-3 assessments.\n- If the patient can no longer self-report (advanced dementia, delirium), observational scales (PAINAD, RASS) replace patient-rated severity.",
        "references": "- Edmonton Symptom Assessment Scale (ESAS) as a comparator framework\n- CMS Medicare Benefit Policy Manual Ch. 9 \u00a720.1 (recertification narrative)",
    },

    {
        "acronym": "MCS",
        "full_name": "Medical Complexity Score",
        "category": "Amerix Composite / Care Intensity",
        "source": "Amerix Medical Consulting composite index. Tracks the escalation of medical care events as a proxy for disease trajectory.",
        "summary": "Composite score quantifying increased medical care burden - new medications, PRN escalation, visit frequency changes, hospital/ER visits, falls, and acute care episodes. MCS rises when a patient's medical system is working harder to hold a steady state, which typically precedes a functional decline.",
        "what_it_measures": "Six care-event domains over a defined interval (typically 30 days): (1) medications - count of new meds OR dose increases, (2) PRN usage frequency change, (3) scheduled visit frequency change (nursing, aide, MSW), (4) after-hours/on-call contacts, (5) acute care events (ER visits, hospitalizations), (6) safety events (falls, skin breakdown episodes, new aspirations).",
        "scoring": "Each domain scored 0-3:\n- 0: no change from prior interval\n- 1: minor escalation (1 new med, modest frequency change, 1 PRN doubling)\n- 2: moderate escalation (2-3 new meds, visits weekly-to-daily, 1 ER visit, 1 fall without injury)\n- 3: significant escalation (>=4 new meds or major dose shifts, daily visits, hospitalization, multiple falls, crisis visits)\n\nTotal MCS = sum across 6 domains, range 0-18.",
        "interpretation": "MCS 0-3: stable system. MCS 4-8: moderate escalation, monitor for trajectory. MCS 9-12: high complexity, typically correlates with functional decline in prior 30-60 days. MCS >=13: crisis-level intensity, consider increased level of care (GIP, continuous home care if eligible) and reassess goals of care.",
        "when_to_use": "At every 14-day recertification window and any time the care plan is materially modified. MCS is especially useful when the medical director must document why a patient remains hospice-appropriate despite superficially stable vital signs - the care intensity tells the story the numbers don't.",
        "hospice_relevance": "MCS translates care-burden reality into documentation that supports recertification. It captures what MAC auditors want to see: the patient's medical system is escalating even if individual symptoms appear stable. Escalating MCS in the face of maximal palliative interventions is strong evidence that the underlying disease is progressing.",
        "worked_examples": [
            {
                "label": "Pt E - Stage IV CHF, 90-day recert interval",
                "body": "Medications: 3 new (torsemide up from furosemide, added spironolactone, opioid added) = 2. PRN: tripled MS IR daily use = 2. Visits: RN went weekly to 3x/week = 2. On-call: 4 after-hours calls this interval = 2. Acute care: 1 ER visit for volume overload = 2. Safety: 2 falls without injury = 1. **MCS = 11/18.** High complexity; strong support for recertification narrative."
            },
        ],
        "picture_fit": "MCS captures CARE burden, not patient-experienced decline. A patient can have high MCS from aggressive palliation of a plateau condition (OK, not terminal trajectory) or from a progressing disease (terminal trajectory). Always pair MCS interpretation with FDR and NDI - if care is escalating AND function is declining AND nutrition is failing, the picture coheres toward terminal prognosis. If only MCS is rising while function and nutrition are stable, investigate whether the system is over-treating a reversible issue.",
        "pitfalls": "- New medications for symptom control may reflect good palliation, not disease progression. Distinguish disease-modifying additions (e.g., inotropes, new diuretic class) from symptom-targeted ones (e.g., new PRN antiemetic).\n- Hospitalizations OUTSIDE the hospice benefit (e.g., for an unrelated fall fracture) should not inflate MCS - document them separately.\n- Visit frequency is often dictated by policy, not clinical need - compare against a matched interval.",
        "references": "- Amerix IDG documentation framework\n- CMS MBPM Ch. 9 recertification narrative requirements",
    },

    {
        "acronym": "FDR",
        "full_name": "Functional Decline Rate",
        "category": "Amerix Composite / Functional Trajectory",
        "source": "Amerix Medical Consulting composite index. Integrates three standard performance tools (PPS, KPS, FAST) with ADL loss to express velocity of functional decline.",
        "summary": "Rate-of-change metric combining Palliative Performance Scale (PPS) or Karnofsky (KPS) change, loss of Activities of Daily Living (ADLs), and FAST-stage progression (in dementia) into a single decline-velocity number expressed per month.",
        "what_it_measures": "Three input streams: (1) PPS or KPS percentage change over the measurement interval, (2) number of ADLs newly lost in the interval, (3) FAST stage shift if dementia. Integrated into a monthly velocity.",
        "scoring": "**PPS/KPS drop component:** Monthly drop in percentage points. 10 points/month or more is severe; 5-9 is moderate; <5 is minor or stable.\n\n**ADL loss component:** Basic ADLs tracked = bathing, dressing, toileting, transfers, continence, feeding (Katz 6 ADLs). Count newly lost ADLs in the interval. 2 or more lost in a month is severe; 1 is moderate; 0 is stable.\n\n**FAST progression (dementia only):** Sub-stage shift (7a -> 7b -> 7c etc.) over 6 months. Progression through a sub-stage in under 6 months is rapid; 6-12 months is typical; >12 months is slow.\n\n**FDR category:** Take the worst of the three signals.",
        "interpretation": "- **Stable trajectory:** PPS/KPS drop <5/month, 0 new ADL losses, no FAST progression in 6+ months.\n- **Moderate trajectory:** 5-9 PPS/KPS points/month, 1 new ADL loss, FAST progression at typical rate.\n- **Rapid trajectory:** >=10 PPS/KPS points/month, >=2 ADL losses in a month, FAST sub-stage progression in <6 months.\n- Rapid trajectory within the prior 6-12 months, alone or combined with any disease-specific LCD criteria, usually supports the 'likely prognosis of 6 months or less' threshold.",
        "when_to_use": "Every 14-day IDG review and at recertification windows. FDR is the single most important decline signal in dementia and debility recertification narratives.",
        "hospice_relevance": "Palmetto L34567 (Hospice Alzheimer's) explicitly references FAST progression. L34547 (Neurological) references ADL dependence. CMS MBPM Ch 9 references 'documented clinical decline.' FDR bundles all three into a measurable, narratable number.",
        "worked_examples": [
            {
                "label": "Pt F - FAST 7a at admission",
                "body": "Admission PPS 40%, dependent in bathing+dressing, FAST 7a. At 90 days: PPS 30%, now also dependent in toileting and transfers, speech down to 3-4 words (FAST 7b). PPS drop 10 points in 90 days = 3.3/month. ADLs lost: 2 new in 90 days (~0.7/month). FAST progression 7a->7b in 90 days (rapid, <6 mo). **FDR = rapid trajectory** driven by FAST progression."
            },
            {
                "label": "Pt G - CHF, 180-day recert",
                "body": "KPS 50% at admission, 40% at 6 months. Lost 1 ADL (transfers). No dementia. Monthly KPS drop 1.7 points - mild. 1 ADL in 6 months - mild. **FDR = moderate-to-mild trajectory.** Alone, this may not strongly support recert; must be paired with MCS rise, NDI, and/or symptom escalation for a cohesive picture."
            },
        ],
        "picture_fit": "FDR is the MOST-CITED decline metric in hospice denials and appeals. A documented FDR of 'rapid' over a 6-month look-back is extremely hard to argue against. But FDR in isolation is not enough - the decline must be attributable to the terminal illness, not to a reversible cause (severe UTI, unrecognized depression, undertreated pain, dehydration). Always ask: what is driving this decline, and is it reversible? If not, FDR joins the picture.",
        "pitfalls": "- PPS/KPS rated by different observers vary by +/-10 points; use the same rater when possible.\n- Acute illnesses (pneumonia, UTI) cause transient PPS drops - reassess post-recovery before calling it decline trajectory.\n- ADL loss timing is often underdocumented - the date of 'became dependent in toileting' is rarely precise. Use IDG consensus.",
        "references": "- Palmetto GBA LCD L34567, L34547\n- Reisberg B. FAST Staging (1988)\n- Anderson F et al. PPS validation (1996)",
    },

    {
        "acronym": "CII",
        "full_name": "Care Intensity Index",
        "category": "Amerix Composite / Care Utilization",
        "source": "Amerix Medical Consulting composite index. Quantifies the visit, on-call, and coordination intensity the hospice IDG is expending per patient.",
        "summary": "Operational-load metric capturing visit frequency (scheduled + PRN + crisis), after-hours calls, IDG discussion volume, family/caregiver contacts, and care plan modifications. CII correlates with patient acuity and often rises 4-8 weeks before terminal transition.",
        "what_it_measures": "Five domains over a 14-30 day interval: (1) scheduled visits (RN, aide, MSW, chaplain), (2) PRN/crisis visits, (3) on-call/after-hours contacts, (4) IDG meetings where the patient is discussed as a problem case, (5) care-plan modifications.",
        "scoring": "**Low:** Weekly RN visit, aide 1-2x/week, rare on-call, routine IDG mention, few care plan changes.\n**Moderate:** RN 2-3x/week, aide 3x/week, occasional on-call (1-2 calls/week), patient discussed each IDG, 1-2 care plan changes in the interval.\n**High:** RN daily or 4+/week, aide daily, frequent on-call (3+ calls/week), patient is a standing IDG item, multiple care plan changes, occasional crisis visits.\n**Crisis:** Continuous care eligible; multiple same-day visits; 24/7 on-call engagement; IDG urgent review; GIP-level acuity.",
        "interpretation": "Interpret against trend, not absolute: a stable patient at 'Moderate' is not concerning. A patient who moved from 'Low' to 'High' in 30 days is rapidly decompensating. CII escalation without corresponding MCS or SEV escalation may indicate family-driven or social complexity rather than disease progression - still real, but different clinical story.",
        "when_to_use": "Monthly recert review and any patient discussed in IDG more than twice per cycle.",
        "hospice_relevance": "CII is operational, not regulatory. But CII trajectories feed the recertification narrative: 'care needs have intensified from X visits/week to Y visits/week, with increasing on-call crisis contacts, consistent with advancing disease trajectory.'",
        "worked_examples": [
            {
                "label": "Pt H - Pancreatic cancer, 60 days on hospice",
                "body": "Admission: RN 2x/week, aide 3x/week, rare on-call. Current: RN 5x/week, aide daily, 2-3 on-call calls/week for pain/symptom escalation, crisis visit for delirium 4 days ago. **CII transitioned from Low-Moderate to High in 60 days.** Combined with SEV rise and PPS drop, clear active-dying trajectory."
            },
        ],
        "picture_fit": "High CII absent other decline signals suggests caregiver stress, social issues, or knowledge gaps, not necessarily terminal progression. Always pair with FDR, NDI, SEV, and MCS. Picture-painting rule: rising care needs that mirror rising medical and functional decline is a coherent picture of progression; rising care needs while the patient is otherwise stable suggests non-medical contributors.",
        "pitfalls": "- Policy-driven visit frequency changes (e.g., agency mandates 2 RN visits/week at recert) inflate CII artificially.\n- Patients close to non-hospice facilities sometimes have higher CII due to geography, not acuity.\n- Family dynamics - demanding family generates visits - do not equal higher acuity.",
        "references": "- Amerix IDG operational metrics framework",
    },

    {
        "acronym": "IRS",
        "full_name": "Irreversibility Score",
        "category": "Amerix Composite / Structural Decline",
        "source": "Amerix Medical Consulting composite index. Quantifies the accumulation of non-recoverable structural/functional losses.",
        "summary": "Count-and-severity index of permanent changes that cannot be reversed by treatment: new-onset incontinence (bladder, bowel), contracture development, Stage 3 or 4 pressure injuries, permanent aspiration/tube-feeding dependence, permanent bed-bound status, cognitive decline to a new baseline. IRS rises monotonically over time - it cannot go down.",
        "what_it_measures": "Cumulative burden of irreversible deficits. Each new irreversible change adds to the score. The score reflects 'how much ground has been permanently lost' and is particularly relevant to dementia, stroke, Parkinson's, and advanced debility where functional reversibility is low.",
        "scoring": "**Each item = 1 point, unless noted.**\n- New bladder incontinence (persistent): 1\n- New bowel incontinence (persistent): 1\n- Contracture (any joint): 1 per joint, max 3\n- Stage 3 pressure injury: 2\n- Stage 4 pressure injury: 3\n- Unstageable or DTI progressing: 2\n- Aspiration requiring texture modification: 1\n- Aspiration requiring tube feeding: 2\n- Permanent bed-bound (bed-to-chair only with max assist): 2\n- Persistent non-verbal status (from prior verbal baseline): 2\n- Permanent dependence in all 6 Katz ADLs: 3\n- Irrecoverable cognitive stage drop (e.g., FAST 6d to FAST 7a): 2\n\nTotal: additive, no upper cap.",
        "interpretation": "Unlike the other Amerix indices, absolute IRS value is less important than the **rate of accumulation**. Adding 4-6 IRS points in a 90-day interval indicates active structural decline. IRS accumulation slows when a patient approaches stable terminal plateau and resumes accelerating in the final 2-4 weeks.",
        "when_to_use": "Every recertification interval and any time a new irreversible deficit is documented in the EMR (new contracture, new pressure injury, new tube feeding decision, etc.). IRS is particularly powerful for chronic, slow-declining illnesses (dementia, Parkinson's, MS, advanced frailty) where month-to-month functional change is subtle but cumulative structural change is clear.",
        "hospice_relevance": "Several Palmetto hospice LCDs explicitly reference irreversible findings: L34547 (Neurological) lists 'aspiration pneumonia,' 'stage 3-4 pressure ulcers,' 'sepsis,' and 'recurrent UTI' as secondary conditions supporting prognosis. L34567 (Alzheimer's) references FAST 7 with irreversible deficits. IRS accumulation is direct evidence of the irreversible-illness trajectory CMS expects.",
        "worked_examples": [
            {
                "label": "Pt I - 88F, advanced dementia, 180-day recert",
                "body": "Admission IRS: 1 (bladder incontinence). 90 days: added bowel incontinence (+1), stage 2 pressure injury that progressed to stage 3 (+2), aspiration with texture modification (+1). IRS went 1 -> 5 in 90 days. Another 90 days: contracture in both hands (+2), FAST drop to 7c (+2), now permanently bed-bound (+2). IRS went 5 -> 11 over the full 180-day interval. **Rapid IRS accumulation strongly supports recertification.**"
            },
        ],
        "picture_fit": "IRS is the best single metric for documenting 'this disease has done damage that cannot be undone.' It pairs especially well with FDR (functional trajectory) and NDI (nutrition). Picture rule: irreversible structural losses accumulating while functional reserve erodes and nutrition fails = clear terminal trajectory. Also important: IRS does not require comparison to a living baseline - at any given moment, the structural state IS the evidence.",
        "pitfalls": "- Pressure injuries from a single hospitalization event may be acute, not disease-trajectory - distinguish persistent from transient.\n- Contractures from positioning alone (in bed-bound patients) are disease-trajectory by definition of being bed-bound.\n- Be careful not to double-count: a tube-fed patient is already capturing the aspiration change; do not add both texture-modification and tube-feeding points for the same progression.",
        "references": "- Palmetto GBA LCD L34547, L34567\n- NPUAP Pressure Injury Staging (2016 update)",
    },

    {
        "acronym": "MAHC-AHCPR",
        "full_name": "NHO/AHCPR Medical Guidelines for Determining Prognosis in Selected Non-Cancer Diseases",
        "category": "Historical Hospice Eligibility Framework",
        "source": "Stuart B et al. National Hospice Organization (NHO) / Agency for Health Care Policy and Research (AHCPR) 1996. Foundational document for all current Palmetto and other MAC hospice LCDs.",
        "summary": "The 1996 NHO/AHCPR Medical Guidelines for Determining Prognosis in Selected Non-Cancer Diseases established the structured framework for documenting hospice eligibility in non-cancer patients. Most disease-specific hospice LCDs (Palmetto L34544/L34547/L34548/L34558/L34559/L34567) trace directly to these guidelines, with the 'Modified' version reflecting subsequent Medicare Medical Director updates.",
        "what_it_measures": "Disease-specific prognostic criteria structured as Primary plus Supporting findings: (1) a core clinical threshold that the patient must meet, and (2) supporting findings that strengthen the terminal prognosis picture. Not a numeric score - a structured qualifying framework.",
        "scoring": "**Format per disease:** Each disease has a 'Part 1' primary criterion and a 'Part 2' list of supporting factors. Meeting Part 1 plus one or more Part 2 findings supports the 6-month prognosis claim. Modern LCDs have evolved the exact thresholds but retained the Part 1 + Part 2 structure.\n\nCore disease categories covered by the original guidelines and updated in current LCDs:\n- Heart Disease (NYHA IV + optimal therapy + supporting findings)\n- Pulmonary Disease (disabling dyspnea at rest + FEV1 <30% + supporting findings)\n- Dementia (FAST >=7a + complications like aspiration, pressure ulcers, weight loss)\n- HIV Disease (CD4 criteria + supporting illnesses)\n- Stroke and Coma (specific neurologic findings + complications)\n- Liver Disease (INR and serum albumin thresholds + supporting findings)\n- Renal Disease (ineligibility for dialysis/transplant + creatinine clearance threshold + supporting findings)\n- ALS (various combinations of respiratory, nutritional, and functional failure)",
        "interpretation": "Meeting the disease-specific Part 1 criterion is necessary but not alone sufficient: best practice (and Palmetto LCD guidance) requires supporting findings to substantiate the 6-month prognosis. The supporting findings are typically cachexia, repeated hospitalizations, recurrent aspiration, progressive decline, or refractoriness to therapy - signals that amplify the core criterion.",
        "when_to_use": "Every admission for non-cancer terminal diagnoses. The framework structures the initial certification narrative and each recertification. While current LCDs are the operational documents, the AHCPR guidelines remain the conceptual framework.",
        "hospice_relevance": "Every Palmetto hospice LCD cites Part 1 + Part 2 logic. Understanding the parent framework helps interpret the LCDs and justifies why all three of LCD-meets + functional-decline + supporting-complications is the standard defensive posture for recertification.",
        "worked_examples": [
            {
                "label": "Heart Disease eligibility per the AHCPR + L34548 framework",
                "body": "**Part 1 (core):** NYHA class IV despite optimal medical management (ACEi/ARB + beta-blocker + diuretic + aldosterone antagonist as tolerated). **Part 2 (supporting):** EF <=20% OR treatment-resistant symptomatic arrhythmia OR history of cardiac arrest OR history of syncope with known cardiac etiology OR embolic CVA of cardiac origin OR HIV disease. Any Part 1 + Part 2 = supports hospice eligibility."
            },
            {
                "label": "Pulmonary Disease per the AHCPR + L34548 framework",
                "body": "**Part 1:** Disabling dyspnea at rest, poorly responsive to bronchodilators, FEV1 <30% predicted (post-bronchodilator). **Part 2:** Progressive pulmonary disease (ER visits or hospitalizations), hypoxemia at rest (pO2 <=55 mmHg or O2 sat <=88% on room air), hypercapnia (pCO2 >=50 mmHg), right heart failure, resting tachycardia >100 bpm, unintentional weight loss >10% in 6 months. Part 1 + one or more Part 2 = supports eligibility."
            },
        ],
        "picture_fit": "The AHCPR/NHO framework is explicit about picture-painting: 'A patient should not be deemed ineligible for hospice based on failure to meet one or more of these criteria.' The introduction emphasizes clinician judgment. The modern LCDs have tightened some language but have kept this spirit. When documenting, treat the criteria as a structured checklist of evidence to marshal, not a pass/fail gate.",
        "pitfalls": "- Don't document 'meets LCD' as a single sentence - marshal the Part 1 finding AND list specific Part 2 findings by name.\n- Don't assume a patient is ineligible because they miss one Part 1 threshold by a small margin if they have many Part 2 findings - the guidelines explicitly allow clinical judgment.\n- Current LCDs have superseded some original AHCPR thresholds - always reference the current Palmetto LCD for the specific disease.",
        "references": "- Stuart B et al. Medical Guidelines for Determining Prognosis in Selected Non-Cancer Diseases. NHO 1996.\n- Current Palmetto GBA LCDs L34544, L34547, L34548, L34558, L34559, L34567 (all adopt Part 1 + Part 2 logic)\n- Fox E et al. Evaluation of Prognostic Criteria for Determining Hospice Eligibility. JAMA 1999;282:1638-1645",
    },

# =====================================================================
# STANDARD CLINICAL PROGNOSTIC SCALES
# =====================================================================

    {
        "acronym": "BODE",
        "full_name": "BODE Index",
        "category": "Pulmonary / COPD Mortality",
        "source": "Celli BR, Cote CG, Marin JM, et al. The body-mass index, airflow obstruction, dyspnea, and exercise capacity index in chronic obstructive pulmonary disease. New England Journal of Medicine 2004;350:1005-1012.",
        "summary": "Multidimensional 0-10 scoring system predicting mortality in COPD, using four inputs: Body-mass index (B), airflow Obstruction (FEV1 percent predicted), Dyspnea (mMRC scale), and Exercise capacity (6-minute walk distance). Published validation showed BODE outperforms FEV1 alone for predicting all-cause and respiratory mortality.",
        "what_it_measures": "A composite of systemic (BMI, exercise tolerance) and pulmonary (FEV1, dyspnea) markers. Each input captures a different aspect of the COPD disease burden: FEV1 captures airflow limitation, mMRC captures perceived disease impact, 6MWD captures systemic capacity, and BMI captures cachectic progression.",
        "scoring": "Each of four components scored 0-3; sum is the BODE Index (range 0-10). Higher = worse prognosis.",
        "scoring_table": {
            "headers": ["Variable", "0 pts", "1 pt", "2 pts", "3 pts"],
            "rows": [
                ["FEV1 (% predicted)", ">=65%", "50-64%", "36-49%", "<=35%"],
                ["6-minute walk (m)", ">=350", "250-349", "150-249", "<=149"],
                ["mMRC Dyspnea", "0-1", "2", "3", "4"],
                ["BMI", ">21", "<=21", "-", "-"],
            ],
        },
        "interpretation": "BODE 0-2: best quartile, 4-year all-cause mortality approximately 18%. BODE 3-4: approximately 32%. BODE 5-6: approximately 40%. BODE 7-10: worst quartile, 4-year mortality approximately 80%. For hospice purposes, BODE >=7 is a strong prognostic signal consistent with 6-month survival <=50% when combined with other pulmonary decline indicators.",
        "when_to_use": "Any COPD patient being evaluated for hospice eligibility or whose trajectory is uncertain. Requires ability to perform a 6-minute walk, which advanced patients may not tolerate - in those cases, a documented inability to complete 6MWD (or <50m) is itself prognostic and can be scored as 3 with a note.",
        "hospice_relevance": "Palmetto LCD L34548 (Cardiopulmonary) lists FEV1 <30% predicted and disabling dyspnea as primary criteria - a BODE of 7+ captures both. The LCD also lists unintentional weight loss >10%, repeated hospitalizations, and resting hypoxemia as supporting findings. BODE's BMI and 6MWD components map onto these signals. Documented BODE with serial measurements (showing decline over time) is a strong defense against recertification denials.",
        "worked_examples": [
            {
                "label": "Pt J - 72M COPD on 3L NC O2",
                "body": "FEV1 25% predicted (3 pts), 6MWD 120m with desaturation to 84% (3 pts), mMRC 4 (breathless on dressing - 3 pts), BMI 19.4 (1 pt). **BODE = 10.** Combined with weight loss 12% in 5 months and two hospitalizations for exacerbation in 4 months, supports Cardiopulmonary LCD hospice eligibility."
            },
            {
                "label": "Pt K - 65F COPD but still walking 400m",
                "body": "FEV1 45% predicted (2 pts), 6MWD 385m (0 pts), mMRC 2 (0 pts), BMI 22 (0 pts). **BODE = 2.** This patient is NOT hospice-appropriate despite COPD - prognostic signals too preserved. Consider palliative care referral, not hospice."
            },
        ],
        "picture_fit": "A high BODE alone doesn't make someone hospice-appropriate. It should sit alongside: recurrent hospitalizations (>=2 in prior year for acute exacerbations), resting hypoxemia, refractory dyspnea despite optimal bronchodilator therapy, and progressive weight loss. BODE is powerful because it captures multi-dimensional decline in one number - but picture-painting requires the supporting clinical narrative.",
        "pitfalls": "- 6MWD is not always feasible in advanced patients; do not score it as 0 if the patient cannot walk at all - score as 3 and document.\n- Post-bronchodilator FEV1 is the correct value; pre-bronchodilator inflates severity.\n- BMI alone is a blunt nutritional marker - pair with weight-loss trajectory (NDI).\n- mMRC is patient-reported; in cognitively impaired patients, use observed behavior substituting (e.g., dyspneic with minimal exertion = mMRC 4).",
        "references": "- Celli BR et al. NEJM 2004;350:1005-12 (original publication and validation)\n- Palmetto GBA LCD L34548",
    },

    {
        "acronym": "SHFM",
        "full_name": "Seattle Heart Failure Model",
        "category": "Cardiac / Heart Failure Mortality",
        "source": "Levy WC, Mozaffarian D, Linker DT, et al. The Seattle Heart Failure Model: prediction of survival in heart failure. Circulation 2006;113:1424-1433. Calculator at depts.washington.edu/shfm.",
        "summary": "Multivariate risk model incorporating 14 clinical variables to predict 1-, 2-, 3-, and 5-year survival in patients with systolic heart failure. Web-based calculator returns exact survival probabilities and mean life expectancy. Validated across multiple cohorts (including IMPACT-HF, ELITE-2, Val-HeFT, RENAISSANCE).",
        "what_it_measures": "Integrated prognostic estimate from clinical, laboratory, medication, and device inputs. Captures the prognostic impact of therapy modifications (e.g., adding ACEi or ICD shifts survival curves upward), making it useful for both prognosis and therapy-decision discussions.",
        "scoring": "Enter the following into the web calculator:\n- Age, gender\n- NYHA class (I-IV)\n- Weight (kg)\n- Ejection fraction (%)\n- Systolic blood pressure\n- Ischemic etiology (yes/no)\n- Laboratory: hemoglobin, lymphocyte %, uric acid, total cholesterol, sodium\n- Medications: diuretic (dose), ACEi/ARB, beta-blocker, aldosterone antagonist, statin, allopurinol\n- Devices: biventricular pacer, ICD\n\nOutput: predicted annual survival percentage and median life expectancy in years.",
        "interpretation": "- **SHFM 1-year survival >=85%:** good prognosis, usually not hospice-appropriate on cardiac grounds alone.\n- **SHFM 1-year survival 50-84%:** intermediate; consider palliative care; hospice may be appropriate if additional decline signals present.\n- **SHFM 1-year survival <50%:** strongly supports hospice eligibility when combined with symptomatic NYHA IV status and supporting findings (repeated admissions, cachexia, refractoriness).\n- **SHFM median life expectancy <=1 year:** explicit support for hospice eligibility.\n- **SHFM median life expectancy <=6 months:** by itself consistent with the terminal prognosis standard.",
        "when_to_use": "Any advanced heart failure patient being evaluated for hospice or requiring a prognostic conversation. Re-run SHFM at each recert interval - worsening trajectory is documented as falling survival curves.",
        "hospice_relevance": "Palmetto LCD L34548 requires NYHA IV + optimal therapy + supporting findings. SHFM quantifies what 'optimal therapy' produces as survival, making the gap between optimal-care-survival and the 6-month prognosis threshold visible and narratable. An SHFM 1-year survival of 30% is powerful evidence for the terminal trajectory.",
        "worked_examples": [
            {
                "label": "Pt L - 78M ischemic CM, EF 18%",
                "body": "NYHA IV despite carvedilol 25mg BID + lisinopril 20mg + furosemide 80mg BID + spironolactone 25mg + ICD. Hgb 10.8, sodium 134, lymphocyte 14%. SHFM output: 1-year survival 42%, median life expectancy 10 months. **Supports hospice eligibility** when paired with weight loss, recurrent CHF admissions, and cachexia."
            },
        ],
        "picture_fit": "SHFM is probabilistic, not deterministic. An SHFM 6-month survival of 55% does not exclude a patient from hospice if other signals (frequent admissions, renal decline, cachexia, symptomatic at rest) point terminal. Use SHFM as the quantitative anchor in the cardiac eligibility narrative, not the sole determinant.",
        "pitfalls": "- SHFM assumes systolic HF; it does not validate well for HFpEF - treat as indicative, not definitive, in preserved EF.\n- Device inputs improve predicted survival; patients who refuse a recommended ICD upgrade will show an artificially better SHFM than their actual trajectory.\n- SHFM underestimates mortality in elderly (>=80) and in advanced kidney disease.",
        "references": "- Levy WC et al. Circulation 2006;113:1424-33\n- Palmetto GBA LCD L34548",
    },

    {
        "acronym": "MELD",
        "full_name": "Model for End-Stage Liver Disease",
        "category": "Liver Disease / Mortality",
        "source": "Kamath PS, Wiesner RH, Malinchoc M, et al. Hepatology 2001;33:464-70. MELD-Na: Kim WR et al. NEJM 2008. MELD 3.0: Kim WR et al. Gastroenterology 2021.",
        "summary": "Laboratory-based score predicting 3-month mortality in end-stage liver disease. Originally validated for TIPS procedure risk, adopted by UNOS for liver transplant prioritization. MELD 3.0 (2021) is the current version, adding sex, albumin, and interactions.",
        "what_it_measures": "Three-month mortality risk from the three dominant drivers of liver failure physiology: bilirubin (synthetic-excretory failure), creatinine (hepatorenal dysfunction), and INR (synthetic/coagulation failure). MELD-Na adds sodium (hyponatremia marker of advanced cirrhosis). MELD 3.0 adds albumin and sex adjustment.",
        "scoring": "**MELD (original):** 3.78 * ln(bilirubin mg/dL) + 11.2 * ln(INR) + 9.57 * ln(creatinine mg/dL) + 6.43. Round to nearest integer. Minimum lab value = 1 (prevents negative log). Max creatinine = 4 (or if on dialysis). Range 6-40.\n\n**MELD-Na (2016-2023):** MELD + 1.32 * (137 - Na) - [0.033 * MELD * (137 - Na)]. Na capped at 125-137.\n\n**MELD 3.0 (current):** More complex formula with additional inputs; use the UNOS calculator at optn.transplant.hrsa.gov.",
        "interpretation_table": {
            "headers": ["MELD", "3-month mortality", "Hospice implication"],
            "rows": [
                ["<=9", "~1.9%", "Not hospice-supportive on MELD grounds alone"],
                ["10-19", "~6%", "Intermediate; requires additional decline signals"],
                ["20-29", "~19.6%", "Growing risk; combined with complications usually supports eligibility"],
                ["30-39", "~52.6%", "Strongly supports hospice eligibility"],
                [">=40", "~71.3%", "Very high 3-month mortality; supports terminal prognosis"],
            ],
        },
        "when_to_use": "Any advanced liver disease patient: decompensated cirrhosis, hepatorenal syndrome, refractory ascites, recurrent hepatic encephalopathy, variceal bleeding without transplant option. Re-score monthly or when labs change significantly.",
        "hospice_relevance": "Palmetto LCD L34544 (Hospice - Liver Disease) primary criteria: INR >1.5 AND serum albumin <2.5 g/dL AND one of: refractory ascites, SBP history, hepatorenal syndrome, HE encephalopathy recurrent, recurrent variceal bleeding. High MELD captures much of this physiology but is not the LCD's formal threshold - MELD supports the LCD narrative rather than replacing it.",
        "worked_examples": [
            {
                "label": "Pt M - 61F alcohol cirrhosis, not transplant-eligible",
                "body": "Bilirubin 8.2, creatinine 2.1, INR 2.4, sodium 128. MELD = 29 (calculator). MELD-Na = 33. **3-month mortality ~52%.** Combined with refractory ascites requiring paracentesis q2 weeks, recent hepatic encephalopathy hospitalization, albumin 2.1 - supports L34544 hospice eligibility."
            },
        ],
        "picture_fit": "MELD is powerful because it is fully lab-based and reproducible, but it misses the quality-of-life picture - a patient with MELD 18 can be bedbound with severe HE and cachexia (hospice-appropriate), while another patient with MELD 22 may be working full-time (not hospice). Use MELD as an anchor and supplement with clinical signs: ascites frequency, HE episodes, variceal bleeding history, weight loss, functional status.",
        "pitfalls": "- In hepatorenal syndrome being treated, MELD changes rapidly - use a stable 7-14 day lab window.\n- Patients on dialysis: use creatinine = 4 per the MELD rules.\n- MELD does not capture HCC burden; hepatoma patients often have lower MELD but worse prognosis - the LCD mentions HCC as a separate supporting condition.\n- MELD 3.0 changes scores by 1-3 points vs MELD-Na - document which version you used.",
        "references": "- Kamath PS et al. Hepatology 2001;33:464-70\n- Kim WR et al. NEJM 2008 (MELD-Na)\n- Kim WR et al. Gastroenterology 2021 (MELD 3.0)\n- Palmetto GBA LCD L34544",
    },

    {
        "acronym": "PPI",
        "full_name": "Palliative Prognostic Index",
        "category": "Palliative / General Prognosis",
        "source": "Morita T, Tsunoda J, Inoue S, Chihara S. The Palliative Prognostic Index: a scoring system for survival prediction of terminally ill cancer patients. Supportive Care in Cancer 1999;7:128-133.",
        "summary": "Clinical scoring system (no lab values needed) predicting survival in terminally ill cancer patients. Uses PPS score, oral intake, edema, dyspnea at rest, and delirium. Widely validated, useful bedside in patients with incomplete laboratory data.",
        "what_it_measures": "Five clinical findings, all observable at the bedside. Designed for cancer but often applied (with caution) to advanced non-cancer palliative populations.",
        "scoring": "**Sum of component points:**\n- PPS: 10-20% = 4 pts | 30-50% = 2.5 pts | >=60% = 0 pts\n- Oral intake: severely reduced (mouthfuls or less) = 2.5 | moderately reduced = 1 | normal = 0\n- Edema: present = 1 | absent = 0\n- Dyspnea at rest: present = 3.5 | absent = 0\n- Delirium: present (not drug-induced) = 4 | absent = 0\n\nTotal range: 0-15.",
        "interpretation": "- **PPI > 6:** 3-week survival probability approximately 83% sensitivity, 71% specificity (i.e., likely death within 3 weeks).\n- **PPI > 4:** 6-week survival probability; likely death within 6 weeks.\n- **PPI <= 4:** longer survival prognosis; not strongly short-term prognostic.",
        "when_to_use": "Cancer patients on hospice at recertification and at any notable clinical change. Reasonable anchor for rapid prognostic estimates in patients who cannot complete a 6MWD or have unavailable labs.",
        "hospice_relevance": "Not a Medicare-required score. Useful for the active-dying window (days to weeks) more than the 6-month eligibility window. A rising PPI on serial measurements supports the active-dying transition and potential GIP-level-of-care justification.",
        "worked_examples": [
            {
                "label": "Pt N - Pancreatic cancer, last 60 days of life",
                "body": "PPS 30% (2.5 pts), oral intake mouthfuls only (2.5 pts), pedal edema 2+ (1 pt), dyspnea at rest (3.5 pts), no delirium (0 pts). **PPI = 9.5.** Predicted <3-week survival. Supports GIP eligibility if symptoms uncontrolled."
            },
        ],
        "picture_fit": "PPI is for the END of the eligibility journey (days to weeks), not the beginning (6-month window). Use it to calibrate caregiver expectations, IDG discussions, and levels of care - not to certify initial eligibility.",
        "pitfalls": "- Delirium scoring excludes drug-induced delirium; clarify etiology before scoring.\n- Oral intake changes rapidly; use 24-48h average.\n- Validated in cancer; apply cautiously in non-cancer.",
        "references": "- Morita T et al. Support Care Cancer 1999;7:128-33\n- Further validation: Stone CA et al. Palliative Medicine 2008",
    },

    {
        "acronym": "PaP",
        "full_name": "Palliative Prognosis Score",
        "category": "Palliative / General Prognosis",
        "source": "Pirovano M, Maltoni M, Nanni O, et al. A new palliative prognostic score: a first step for the staging of terminally ill cancer patients. Journal of Pain and Symptom Management 1999;17:231-239. D-PaP variant: Scarpi E et al. 2011.",
        "summary": "Six-variable prognostic score for 30-day survival in cancer patients. Unlike PPI, PaP requires a blood count. D-PaP adds delirium. Outputs three risk groups (A/B/C) with corresponding 30-day survival probabilities.",
        "what_it_measures": "30-day survival probability in terminally ill patients. Integrates clinical prediction of survival (CPS - clinician gestalt) with objective markers.",
        "scoring": "**Variable points:**\n- Dyspnea: no=0, yes=1\n- Anorexia: no=0, yes=1.5\n- KPS: 30+ = 0, 10-20 = 2.5\n- Clinician's prediction of survival (weeks): >12=0, 11-12=2, 9-10=2.5, 7-8=2.5, 5-6=4.5, 3-4=6, 1-2=8.5\n- Total WBC (x10^9/L): <=8.5 = 0, 8.6-11 = 0.5, >11 = 1.5\n- Lymphocyte %: 20-40 = 0, 12-19.9 = 1, 0-11.9 = 2.5\n\nTotal range 0-17.5\n\n**D-PaP adds delirium:** present = 2, absent = 0.",
        "interpretation_table": {
            "headers": ["PaP Group", "Score", "30-day survival"],
            "rows": [
                ["A (low risk)", "0-5.5", ">70%"],
                ["B (intermediate)", "5.6-11", "30-70%"],
                ["C (high risk)", "11.1-17.5", "<30%"],
            ],
        },
        "when_to_use": "Cancer patients on hospice when a blood count is available. Particularly useful at recertification intervals to demonstrate ongoing terminal trajectory objectively.",
        "hospice_relevance": "Not Medicare-required. Complements PPI and supports the active-dying narrative in cancer hospice patients. Group C PaP is strong documentary evidence for continued hospice eligibility.",
        "worked_examples": [
            {
                "label": "Pt O - Metastatic breast cancer, KPS 20",
                "body": "Dyspnea yes (1), anorexia yes (1.5), KPS 20 (2.5), CPS 5-6 weeks (4.5), WBC 13 (1.5), lymphocyte 8% (2.5). **PaP = 13.5 = Group C**, 30-day survival <30%. Supports recertification."
            },
        ],
        "picture_fit": "Like PPI, PaP is a short-horizon tool. Use it for the last 1-3 months of life. Combine with PPS/KPS trajectory, NDI, and disease-specific markers for the full picture.",
        "pitfalls": "- CPS (clinician prediction) is the most-heavily-weighted variable; biased toward optimism across all clinicians.\n- WBC elevations from infection (common in cancer) inflate PaP but may not reflect cancer trajectory.\n- Steroid effects on WBC and lymphocytes skew scores - note steroid use.",
        "references": "- Pirovano M et al. JPSM 1999;17:231-9\n- Scarpi E et al. Support Care Cancer 2011 (D-PaP)",
    },

    {
        "acronym": "CCI",
        "full_name": "Charlson Comorbidity Index",
        "category": "Comorbidity / Mortality Risk",
        "source": "Charlson ME, Pompei P, Ales KL, MacKenzie CR. A new method of classifying prognostic comorbidity in longitudinal studies: development and validation. Journal of Chronic Diseases 1987;40:373-383.",
        "summary": "Weighted index of 17-19 comorbid conditions predicting 10-year mortality. Original conditions weighted 1-6 based on hazard ratio. Modified versions (age-adjusted CCI, updated CCI) extend applicability. Most widely used comorbidity metric in clinical research.",
        "what_it_measures": "Cumulative comorbidity burden expressed as a mortality-risk-weighted score. Provides a comparable number across heterogeneous patients to answer 'how sick is this patient baseline-wise?'",
        "scoring": "**1 point each:** MI, CHF, PVD, CVD/TIA, dementia, COPD, connective tissue disease, peptic ulcer disease, mild liver disease, DM without end-organ damage.\n**2 points each:** Hemiplegia, moderate-severe CKD, DM with end-organ damage, any solid tumor (not metastatic), leukemia, lymphoma.\n**3 points each:** Moderate-severe liver disease.\n**6 points each:** Metastatic solid tumor, AIDS.\n\n**Age adjustment:** add 1 point per decade over age 40 (50-59 = 1, 60-69 = 2, 70-79 = 3, 80+ = 4).",
        "interpretation": "- **CCI 0:** 12% 10-year mortality.\n- **CCI 1-2:** 26%\n- **CCI 3-4:** 52%\n- **CCI >=5:** 85%+.\n\nCorrelations to 1-year mortality in hospitalized patients: CCI 0 ~8%, CCI 1-2 ~25%, CCI >=3 ~60%+.",
        "when_to_use": "Any patient whose primary hospice-qualifying illness is not obviously terminal on its own, but whose overall burden of chronic disease makes 6-month prognosis reasonable. Particularly useful for frailty, debility, and failure-to-thrive presentations where no single LCD cleanly applies.",
        "hospice_relevance": "Not required by LCDs, but CCI can support 'adult failure to thrive' and 'debility' eligibility narratives. Palmetto LCD L34558 specifically addresses Adult Failure to Thrive Syndrome where multiple comorbidities collectively drive terminal trajectory. A high CCI quantifies what the narrative describes.",
        "worked_examples": [
            {
                "label": "Pt P - 82F with CHF, COPD, CKD stage 4, dementia, prior CVA",
                "body": "CHF (1) + COPD (1) + CKD moderate-severe (2) + dementia (1) + CVA (1) = 6. Age 82 adds 4. **Total age-adjusted CCI = 10.** Predicted 1-year mortality >60%. Strong support for debility/AFTT hospice narrative."
            },
        ],
        "picture_fit": "CCI is BASELINE comorbidity. It does not capture velocity or decline - a patient with CCI 10 who is stable for years is not the same as a patient with CCI 8 who is rapidly decompensating. Use CCI as the static backdrop against which dynamic decline signals (FDR, NDI, SEV, MCS) are interpreted. A high CCI plus rapid Amerix-index progression is a powerful combined picture.",
        "pitfalls": "- Many EMRs auto-calculate CCI based on ICD codes; garbage in, garbage out - review the diagnosis list.\n- CCI does not include all terminal illnesses (ALS, Parkinson's, MS) directly - use domain-specific scales.\n- Age adjustment can push scores high even in well-preserved elderly; always pair with functional status.",
        "references": "- Charlson ME et al. J Chronic Dis 1987;40:373-83\n- Quan H et al. Med Care 2005 (updated weights)",
    },

    {
        "acronym": "CFS",
        "full_name": "Clinical Frailty Scale (Rockwood)",
        "category": "Frailty / Functional Reserve",
        "source": "Rockwood K, Song X, MacKnight C, et al. A global clinical measure of fitness and frailty in elderly people. CMAJ 2005;173:489-495.",
        "summary": "9-point ordinal scale summarizing fitness, frailty, and dependence using a brief visual pictograph and descriptor. Widely adopted in palliative care, hospice, and end-of-life decision-making. Reflects BASELINE (pre-illness) status, not transient deconditioning.",
        "what_it_measures": "Frailty as a global construct integrating function, cognition, and dependence. Rapid bedside assessment correlated with mortality, hospitalization, and nursing home placement.",
        "scoring_table": {
            "headers": ["CFS", "Descriptor", "Brief definition"],
            "rows": [
                ["1", "Very Fit", "Robust, active, exercising regularly, among the fittest for age"],
                ["2", "Well", "No active disease symptoms but less fit than category 1"],
                ["3", "Managing Well", "Medical problems well controlled, not regularly active beyond walking"],
                ["4", "Vulnerable (Living with Very Mild Frailty)", "Not dependent on others but symptoms slow them; complain of being 'slowed up'"],
                ["5", "Mildly Frail", "Need help with high-order IADLs (finances, transportation, heavy housework, medications)"],
                ["6", "Moderately Frail", "Need help with all outside activities + IADLs + bathing and minor help dressing"],
                ["7", "Severely Frail", "Completely dependent for personal care, stable but mortality risk high"],
                ["8", "Very Severely Frail", "Completely dependent, approaching end of life, could not recover from minor illness"],
                ["9", "Terminally Ill", "Life expectancy <6 months even without frailty (e.g., advanced cancer)"],
            ],
        },
        "interpretation": "- **CFS 1-3:** Fit or managing - typically not hospice.\n- **CFS 4:** Vulnerable - palliative considerations begin.\n- **CFS 5-6:** Mild-moderate frailty - palliative care appropriate; hospice if additional trajectory signals.\n- **CFS >=7:** Severe frailty - commonly hospice-eligible when combined with disease-specific decline.\n- **CFS 8-9:** Actively declining; typically 6-month or shorter prognosis.",
        "when_to_use": "Every hospice admission and recertification. Especially useful in frail elderly, debility, and failure-to-thrive cases. Takes <1 minute at bedside.",
        "hospice_relevance": "Not LCD-required but increasingly referenced in payer audits. CFS 7-8 is solid documentary support for debility and frailty-driven hospice narratives, which often lack a single-disease LCD match.",
        "worked_examples": [
            {
                "label": "Pt Q - 86F in assisted living",
                "body": "Dependent in bathing, dressing, toileting; can transfer with 1-person assist; feeds herself with supervision; cognition mild-moderate impairment; states she is 'tired all the time.' **CFS 7 (Severely Frail).** If she adds worsening anorexia and unintentional weight loss, moves toward CFS 8 and hospice eligibility."
            },
        ],
        "picture_fit": "CFS is a BASELINE framework, not a decline metric. Pair with trajectory metrics (FDR, NDI) to tell the full picture. A CFS 7 that has been stable for 2 years is different from a CFS 7 that was CFS 5 six months ago - the direction matters.",
        "pitfalls": "- Rate BASELINE (pre-acute-illness) status, not hospital bed appearance.\n- In dementia, use CFS cautiously - FAST is more specific for dementia trajectory.\n- Self-report in CFS assessment is reliable if cognition intact; in impaired patients, use caregiver/observation.",
        "references": "- Rockwood K et al. CMAJ 2005;173:489-95\n- Updated CFS 2.0 (2020) includes additional descriptors for categories 5-7",
    },

    {
        "acronym": "Braden",
        "full_name": "Braden Scale for Predicting Pressure Ulcer Risk",
        "category": "Skin Integrity / Pressure Injury Risk",
        "source": "Bergstrom N, Braden BJ, Laguzza A, Holman V. The Braden Scale for Predicting Pressure Sore Risk. Nursing Research 1987;36:205-210.",
        "summary": "Six-subscale assessment predicting pressure injury risk. Widely validated, used in virtually every acute-care and long-term-care setting. Applied in hospice for risk stratification and care planning, and is a documentation element in quality reporting (CAHPS, HOPE).",
        "what_it_measures": "Probability of pressure injury development based on perfusion, moisture, activity, mobility, nutrition, and friction/shear.",
        "scoring_table": {
            "headers": ["Subscale", "1", "2", "3", "4"],
            "rows": [
                ["Sensory perception", "Completely limited", "Very limited", "Slightly limited", "No impairment"],
                ["Moisture", "Constantly moist", "Very moist", "Occasionally moist", "Rarely moist"],
                ["Activity", "Bedfast", "Chairfast", "Walks occasionally", "Walks frequently"],
                ["Mobility", "Completely immobile", "Very limited", "Slightly limited", "No limitation"],
                ["Nutrition", "Very poor", "Probably inadequate", "Adequate", "Excellent"],
                ["Friction and shear (1-3 only)", "Problem", "Potential problem", "No apparent problem", "-"],
            ],
        },
        "interpretation": "Sum of six subscales (range 6-23):\n- **<=9:** Severe risk\n- **10-12:** High risk\n- **13-14:** Moderate risk\n- **15-18:** Mild risk\n- **>=19:** No or minimal risk.",
        "when_to_use": "Admission and every 7-14 days (or per facility protocol) for any hospice patient with reduced mobility. Trigger for pressure-reduction interventions and care plan updates.",
        "hospice_relevance": "Braden scores in the severe-risk range often correlate with the advanced functional decline and immobility that support hospice eligibility. A Braden <=9 accompanied by progression to Stage 3-4 pressure injury is cited in Palmetto L34547 (Neurological) as a supporting finding.",
        "worked_examples": [
            {
                "label": "Pt R - Advanced dementia, bedbound",
                "body": "Sensory 2, Moisture 2 (incontinence), Activity 1 (bedfast), Mobility 1 (completely immobile), Nutrition 2 (probably inadequate), Friction 1 (problem). **Braden = 9, severe risk.** Combined with existing Stage 2 sacral pressure injury, documents immobility/skin-decline trajectory."
            },
        ],
        "picture_fit": "Braden is a risk tool, not a prognostic tool. A low Braden flags skin-risk but does not by itself support hospice eligibility - it is a byproduct of the immobility and nutritional decline already documented elsewhere. Include Braden in the picture to round out the 'bedbound plus cachectic' narrative.",
        "pitfalls": "- Braden can improve rapidly with good hospice skincare - don't treat a rising Braden as 'patient got better.'\n- Underestimates risk in elderly with fragile skin even at Braden >=13.",
        "references": "- Bergstrom N, Braden BJ. Nursing Research 1987;36:205-10\n- NPUAP/EPUAP Pressure Injury Guidelines (2019 update)",
    },

    {
        "acronym": "Morse",
        "full_name": "Morse Fall Scale",
        "category": "Fall Risk / Safety",
        "source": "Morse JM, Morse RM, Tylko SJ. Development of a scale to identify the fall-prone patient. Canadian Journal on Aging 1989;8:366-377.",
        "summary": "Six-item fall risk assessment for hospitalized and institutionalized patients. Quick (<3 min), validated, widely used in acute and long-term care. In hospice, documents the fall-risk context driving care plan intensity and 24-hour needs.",
        "what_it_measures": "Probability of fall within the current care episode based on fall history, comorbid diagnoses, ambulatory aid use, IV line presence, gait, and mental status.",
        "scoring": "- **Fall history:** 0 or 25\n- **Secondary diagnosis:** 0 or 15\n- **Ambulatory aid:** none/bedrest/nurse-assisted = 0, crutches/cane/walker = 15, furniture-holding = 30\n- **IV access:** 0 or 20\n- **Gait:** normal/bedbound/wheelchair = 0, weak = 10, impaired = 20\n- **Mental status:** oriented to ability = 0, overestimates or forgets limits = 15\n\nTotal: 0-125.",
        "interpretation": "- **0-24:** Low risk - standard precautions\n- **25-50:** Moderate risk - standard precautions with reminders\n- **>=51:** High risk - fall prevention interventions",
        "when_to_use": "Admission and weekly for mobile or transitional hospice patients. Less relevant for bedbound patients (automatic high risk).",
        "hospice_relevance": "Fall incidents are captured in the MCS (Medical Complexity Score) Amerix composite. Persistent high Morse with a new fall event adds to the Irreversibility Score (IRS) if a fracture results.",
        "worked_examples": [
            {
                "label": "Pt S - 78M with Parkinson's, uses walker",
                "body": "1 fall in past 3 months (25), Parkinson's (15), walker (15), no IV (0), impaired gait (20), forgets limits (15). **Morse = 90, high risk.** Triggers care plan updates, bedside alarm, supervised transfers."
            },
        ],
        "picture_fit": "Morse alone is an operational tool, not hospice-eligibility evidence. It contributes to the picture when combined with falls that caused fractures, hospitalizations, or accelerating functional decline.",
        "pitfalls": "- Morse validated in acute care; home-hospice context is different - use as a reasonable screen, not a precise predictor.\n- Weekly rescore misses subacute changes.",
        "references": "- Morse JM et al. Can J Aging 1989;8:366-77",
    },

    {
        "acronym": "ECOG",
        "full_name": "Eastern Cooperative Oncology Group Performance Status",
        "category": "Performance Status / Oncology",
        "source": "Oken MM et al. American Journal of Clinical Oncology 1982;5:649-655. Also called the WHO or Zubrod score.",
        "summary": "Simple 6-point scale (0-5) measuring functional ability and self-care. Standard in oncology for treatment decisions. Correlates strongly with survival across cancer types.",
        "scoring_table": {
            "headers": ["ECOG", "Description"],
            "rows": [
                ["0", "Fully active, no restrictions"],
                ["1", "Restricted in strenuous activity but ambulatory, able to do light work"],
                ["2", "Ambulatory, capable of self-care, unable to work; up >50% of waking hours"],
                ["3", "Limited self-care, confined to bed/chair >50% of waking hours"],
                ["4", "Completely disabled, no self-care, totally bed/chair confined"],
                ["5", "Dead"],
            ],
        },
        "interpretation": "- **ECOG 0-1:** Good functional status; not hospice-eligible on function alone.\n- **ECOG 2:** Intermediate; palliative considerations begin.\n- **ECOG 3:** Limited function; often hospice-appropriate in cancer with progressing disease.\n- **ECOG 4:** Bedbound/completely disabled; strongly supports hospice in cancer with progression.",
        "when_to_use": "Any cancer patient at admission and recert. Used alongside PPS/KPS; ECOG is simpler but less granular.",
        "hospice_relevance": "Cancer hospice eligibility often rests on: progression despite (or no longer receiving) anti-cancer therapy + ECOG 3+. Palmetto does not publish cancer-specific hospice LCDs (cancer eligibility is governed by the CMS MBPM Ch 9 disease-progression standard), but ECOG is the standard functional anchor.",
        "worked_examples": [
            {
                "label": "Pt T - Metastatic pancreatic cancer, off chemo",
                "body": "Bedbound ~70% of day, needs help with all ADLs, cachectic. **ECOG 4.** Combined with progressive disease on imaging and declining weight, strongly supports hospice eligibility."
            },
        ],
        "picture_fit": "ECOG captures functional status only - the 'life' side. The 'death' side (progressing disease, refractory symptoms, caregiver burden) must accompany it. In cancer, a high ECOG + evidence of disease progression + declining trajectory = hospice-appropriate.",
        "pitfalls": "- ECOG can transiently worsen from acute illness; reassess post-treatment.\n- In non-cancer, prefer PPS/KPS (more granular) or CFS.",
        "references": "- Oken MM et al. Am J Clin Oncol 1982;5:649-55",
    },

    {
        "acronym": "GAD-7",
        "full_name": "Generalized Anxiety Disorder 7-Item Scale",
        "category": "Mental Health / Anxiety Screening",
        "source": "Spitzer RL, Kroenke K, Williams JBW, Lowe B. A brief measure for assessing generalized anxiety disorder: the GAD-7. Archives of Internal Medicine 2006;166:1092-1097.",
        "summary": "Self-report screener for generalized anxiety. Seven items, each scored 0-3, total 0-21. Ultra-brief GAD-2 uses only the first two items. Core of the PHQ-4 combined screener.",
        "scoring": "Each of 7 items rated 0 (not at all) to 3 (nearly every day) over the past 2 weeks. Items cover: feeling nervous, unable to control worrying, worrying about different things, trouble relaxing, restlessness, irritability, feeling afraid. Total 0-21.",
        "interpretation_table": {
            "headers": ["GAD-7", "Severity", "Action"],
            "rows": [
                ["0-4", "Minimal", "No intervention"],
                ["5-9", "Mild", "Monitor, consider psychoeducation"],
                ["10-14", "Moderate", "Possible clinically significant anxiety; consider treatment"],
                ["15-21", "Severe", "Likely clinically significant; treat"],
            ],
        },
        "when_to_use": "Admission and recertification in patients able to self-report. In advanced dementia or delirium, replace with observer tools (PAINAD, RASS-derived).",
        "hospice_relevance": "GAD identifies anxiety requiring intervention - critical for symptom control, level-of-care decisions, and CAHPS patient-experience scores. A persistently high GAD-7 despite treatment is evidence of refractory symptom burden.",
        "worked_examples": [
            {
                "label": "Pt U - End-stage COPD with episodic dyspnea anxiety",
                "body": "GAD-7 = 16 (severe) at admission, persists at 12 after 2 weeks of scheduled lorazepam. Indicates inadequate anxiety control, triggers care plan escalation and possible change in pharmacologic approach."
            },
        ],
        "picture_fit": "GAD supports care planning and symptom management narratives; it is not an eligibility tool by itself. High refractory anxiety is one of many symptoms that can support GIP-level-of-care arguments.",
        "pitfalls": "- Anxiety in end-stage respiratory illness is often dyspnea-driven, not primary anxiety - treat the dyspnea first.\n- GAD-2 is less specific than GAD-7; use GAD-7 when possible.",
        "references": "- Spitzer RL et al. Arch Intern Med 2006;166:1092-7",
    },

    {
        "acronym": "PHQ-4",
        "full_name": "Patient Health Questionnaire 4",
        "category": "Mental Health / Depression + Anxiety",
        "source": "Kroenke K, Spitzer RL, Williams JBW, Lowe B. An ultra-brief screening scale for anxiety and depression: the PHQ-4. Psychosomatics 2009;50:613-621.",
        "summary": "Ultra-brief (4-item) combined anxiety (GAD-2 items) and depression (PHQ-2 items) screener. Takes under a minute. Highly sensitive for both conditions as a first-pass screen.",
        "scoring": "Each item 0-3 (same frequency anchors as GAD-7/PHQ-9). Items: feeling nervous, can't stop worrying (GAD-2); little interest/pleasure, feeling down (PHQ-2). Total 0-12. Subscale totals 0-6.",
        "interpretation_table": {
            "headers": ["Score", "Severity"],
            "rows": [
                ["0-2", "None"],
                ["3-5", "Mild"],
                ["6-8", "Moderate"],
                ["9-12", "Severe"],
            ],
        },
        "when_to_use": "Admission universal screen. Positive score (>=3 on either subscale) triggers full GAD-7 or PHQ-9.",
        "hospice_relevance": "Depression and anxiety are common in terminal illness and impact symptom perception, caregiver burden, and care plan. PHQ-4 is a cheap universal screener; positive findings lead to targeted treatment.",
        "worked_examples": [
            {
                "label": "Pt V - New hospice admission",
                "body": "PHQ-4 = 7 (GAD-2 = 4, PHQ-2 = 3). Prompts follow-up GAD-7 and PHQ-9; initial psychosocial referral."
            },
        ],
        "picture_fit": "PHQ-4 is a screening tool, not diagnostic and not hospice-eligibility. Supports comprehensive symptom assessment and care planning.",
        "pitfalls": "- Positive screen is not a diagnosis - follow up.\n- In severe cognitive impairment, self-report unreliable.",
        "references": "- Kroenke K et al. Psychosomatics 2009;50:613-21",
    },

    {
        "acronym": "TUG",
        "full_name": "Timed Up and Go Test",
        "category": "Mobility / Fall Risk / Functional Measure",
        "source": "Podsiadlo D, Richardson S. The timed 'Up & Go': a test of basic functional mobility for frail elderly persons. JAGS 1991;39:142-148.",
        "summary": "Performance-based test: time the patient to rise from standard chair, walk 3 meters, turn, return, sit. Assesses mobility, balance, and fall risk. Quick (<3 min), equipment-minimal.",
        "scoring": "Time in seconds from 'go' to fully seated. Usual walking aids permitted. One practice trial, then timed.",
        "interpretation_table": {
            "headers": ["Time (sec)", "Interpretation"],
            "rows": [
                ["<10", "Normal mobility"],
                ["10-19", "Mostly independent"],
                ["20-29", "Variable mobility"],
                [">=30", "Impaired mobility, high fall risk"],
            ],
        },
        "when_to_use": "Admission and serially for ambulatory hospice patients. Not applicable to bedbound patients.",
        "hospice_relevance": "Serial TUG decline (e.g., 18 -> 28 sec over 60 days) quantifies functional decline trajectory. Useful in frailty and Parkinson's hospice narratives.",
        "worked_examples": [
            {
                "label": "Pt W - 80M with Parkinson's, 6-month recert",
                "body": "Admission TUG 22 sec (variable). Current TUG 38 sec with one near-fall. Documented functional decline supports continued eligibility."
            },
        ],
        "picture_fit": "TUG is an objective decline signal when serial. For bedbound patients it doesn't apply - use other metrics.",
        "pitfalls": "- Requires patient cooperation; not valid in significant cognitive impairment.\n- Influenced by acute illness.",
        "references": "- Podsiadlo D, Richardson S. JAGS 1991;39:142-8",
    },

    {
        "acronym": "MDS-MRI-R",
        "full_name": "MDS Mortality Risk Index - Revised",
        "category": "Prognosis / Nursing Home Residents",
        "source": "Porock D, Oliver DP, Zweig S, et al. Predicting death in the nursing home: development and validation of the 6-month Minimum Data Set mortality risk index. JAGS 2005;53:491-496.",
        "summary": "Risk score using 12 MDS (Minimum Data Set) variables to predict 6-month mortality in nursing home residents. Tailored to the long-term-care population.",
        "scoring": "12 variables scored from MDS data: admission <3 months, weight loss, renal failure, CHF, poor appetite, male sex, dehydration, shortness of breath, cancer, age bands, cognitive decline, ADL dependence score.",
        "interpretation": "Score bands correlate with 6-month mortality approximately: low-risk <20%, intermediate 20-50%, high >50%. Exact thresholds depend on validation cohort.",
        "when_to_use": "Nursing home hospice evaluations where MDS data are already collected. Streamlines prognostic documentation.",
        "hospice_relevance": "Specifically designed for the population where hospice determinations are most contested. High MDS-MRI-R combined with disease-specific decline is very strong documentary support.",
        "worked_examples": [
            {
                "label": "Pt X - 87F in SNF, dementia + CHF",
                "body": "Recent admission, weight loss yes, poor appetite yes, ADL score maximal, cognitive decline - MDS-MRI-R in high-risk range. Supports hospice eligibility in the NH context."
            },
        ],
        "picture_fit": "Best used in settings where MDS is already being collected. Do not attempt to collect MDS specifically for MDS-MRI-R calculation - use alternative tools.",
        "pitfalls": "- MDS versions change; use current scoring definitions.\n- Requires accurate, current MDS data.",
        "references": "- Porock D et al. JAGS 2005;53:491-6",
    },

    {
        "acronym": "Mitchell MRI",
        "full_name": "Mortality Risk Index for Advanced Dementia (Mitchell)",
        "category": "Prognosis / Advanced Dementia",
        "source": "Mitchell SL, Kiely DK, Hamel MB, et al. Estimating prognosis for nursing home residents with advanced dementia. JAMA 2004;291:2734-2740.",
        "summary": "Risk score specifically for nursing home residents with advanced dementia. Uses 12 MDS-derived predictors. Basis for ADEPT (Advanced Dementia Prognostic Tool). Designed to address the documented under-referral of advanced dementia patients to hospice.",
        "scoring": "**Variable points:**\n- Length of stay <90 days: 1\n- Age >=83: 1.9\n- Male sex: 1.9\n- Shortness of breath: 1.9\n- Pressure ulcer stage >=2: 1.7\n- Total ADL dependence: 1.9\n- Bedfast: 1.5\n- Insufficient oral intake: 2.8\n- Bowel incontinence: 1.9\n- BMI <18.5: 1.8\n- Weight loss: 1.6\n- CHF: 1.8\n\nTotal range varies; higher = higher mortality.",
        "interpretation": "Mortality risk groups by total score:\n- **0:** 6-month mortality approximately 9%\n- **1-2:** 11%\n- **3-5:** 23%\n- **6-8:** 40%\n- **9-11:** 57%\n- **>=12:** 70%",
        "when_to_use": "Nursing home residents with advanced dementia (FAST 7+) being evaluated for hospice. Mitchell MRI predicts 6-month mortality specifically - the hospice eligibility horizon.",
        "hospice_relevance": "Direct support for Palmetto L34567 (Alzheimer's hospice) eligibility. A Mitchell MRI >=6 combined with FAST 7c and a precipitating event (aspiration, hip fracture, recurrent UTI, sepsis) is strong eligibility documentation.",
        "worked_examples": [
            {
                "label": "Pt Y - 89M SNF dementia, FAST 7c",
                "body": "LOS 60 days (1), age 89 (1.9), male (1.9), stage 2 sacral ulcer (1.7), total ADL dep (1.9), bedfast (1.5), eats <50% (2.8), bowel incontinent (1.9), BMI 17 (1.8), 10% weight loss (1.6). **Total 18.** 6-month mortality >70%. Supports hospice eligibility very strongly."
            },
        ],
        "picture_fit": "Mitchell MRI is the most-specific tool for advanced dementia prognosis. Pair with FAST stage and LCD L34567 criteria (aspiration, multiple UTIs, sepsis, stage 3-4 ulcers, weight loss, dysphagia) for a complete picture.",
        "pitfalls": "- Designed for NH setting; applicability to home-based advanced dementia less validated.\n- Overlaps with L34567 criteria; treat as complementary quantification.",
        "references": "- Mitchell SL et al. JAMA 2004;291:2734-40\n- Palmetto LCD L34567",
    },

]
