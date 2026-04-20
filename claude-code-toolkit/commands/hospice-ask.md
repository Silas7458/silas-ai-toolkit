---
name: hospice-ask
description: "Ask a hospice regulatory / compliance question against the Hospice Compliance NotebookLM corpus + Perplexity web fallback. Usage: /hospice-ask <question>. Primary source is the Drive-fed Hospice regs corpus; Perplexity fills gaps and flags docs to ingest."
---

# /hospice-ask - Hospice Regulatory Q&A with Corpus + Web

Query the **Hospice Compliance** NotebookLM notebook (Drive-fed corpus of CMS manuals, CoPs, state surveys, client P&Ps) first. If the corpus is silent or thin, fall back to Perplexity. Always label which layer the answer came from. When Perplexity surfaces a PDF/manual not yet in the corpus, emit a "MISSING FROM CORPUS" line so Silas can download and drop it in `Hospice regs/`.

## Config (DO NOT hardcode these — read from config.json)

Read `C:/Users/silas/.hospice-regs/config.json` on every invocation:
- `notebook_id` - Hospice Compliance notebook UUID
- `account` - must be `executive.shelton@gmail.com`
- `drive_folder_id` - Hospice regs folder

## Step 1: Account Integrity Canary (MANDATORY)

Before querying, verify the correct Google account is authed to NotebookLM. Run:

```bash
npx notebooklm ls 2>&1 | grep -iE "amerix" | head -1
```

If this returns nothing or an AuthError, the wrong account is authed. STOP. Tell Silas: "NotebookLM auth is wrong / missing. Run `npx notebooklm login` with `executive.shelton@gmail.com`." Do not proceed with the query.

## Step 2: Query the Corpus

Query the Hospice Compliance notebook directly via the notebooklm-py API (matches `/recall` pattern):

```python
import asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')
from notebooklm.auth import extract_cookies_from_storage, fetch_tokens, AuthTokens
from notebooklm.client import NotebookLMClient

with open('C:/Users/silas/.hospice-regs/config.json') as f:
    cfg = json.load(f)
with open('C:/Users/silas/.notebooklm/storage-state.json') as f:
    storage = json.load(f)

cookies = extract_cookies_from_storage(storage)

async def ask(query):
    csrf_token, session_id = await fetch_tokens(cookies)
    tokens = AuthTokens(cookies=cookies, csrf_token=csrf_token, session_id=session_id)
    async with NotebookLMClient(auth=tokens) as client:
        return await client.chat.ask(cfg['notebook_id'], query)

result = asyncio.run(ask("USER_QUESTION_HERE"))
print(json.dumps({"answer": result.answer, "citations": getattr(result, 'citations', [])}, default=str))
```

Capture the `answer` and `citations` fields.

## Step 3: Judge Corpus Sufficiency

Decide whether the corpus answer is sufficient. Criteria for "thin / insufficient":
- Answer contains "I don't have" / "not in these sources" / "cannot find"
- Answer is under 2 sentences AND the question asks for specifics
- Zero citations returned
- Answer contradicts itself

If sufficient: skip Step 4.

## Step 4: Perplexity Fallback (conditional)

If the corpus answer is thin, call Perplexity with a hospice-scoped prompt:

```
Use mcp__perplexity__perplexity_ask with:
  messages: [{"role": "user", "content": "<hospice-regulatory rephrase of question>"}]
  recency_filter: "year"  # or "month" if the question is about recent changes
  search_domain_filter: ["cms.gov", "medicare.gov", "hhs.gov", "oig.hhs.gov", "federalregister.gov"]
```

Prefer authoritative sources. Capture the answer + the list of URLs Perplexity cited.

## Step 5: Detect "Missing from Corpus" Documents

Scan Perplexity's cited URLs. If any URL points to a PDF manual on a `.gov` domain (CMS, HHS, OIG, state health dept) that's likely a full regulatory document (NOT a news article or blog post), flag it.

Heuristic: URL ends in `.pdf` OR contains `/manuals/` `/policy/` `/memos/` `/transmittals/` `/survey/` `/regulations/`.

## Step 6: Format the Response

Structured response with clear source attribution:

```
## Answer

<synthesis of corpus + perplexity, written plainly>

### Sources

**From your corpus (Hospice Compliance notebook):**
- <cite 1: doc name, page if available>
- <cite 2>

**From web (Perplexity):**
- <url 1>
- <url 2>

### 📎 Missing from corpus
The following documents were referenced in the web answer but are NOT in your Hospice regs/ Drive folder. Download and drop them in to add to your searchable corpus:

- **<doc title>** - <URL>
  Why it matters: <one-line relevance>

(omit this section if nothing to flag)
```

## Edge Cases

- **Corpus has the answer, Perplexity confirms:** Show only the corpus answer. Note "Web confirms" in one line if Perplexity didn't contradict.
- **Corpus and Perplexity disagree:** Surface both, label the disagreement, let Silas adjudicate. Don't pick a winner.
- **Question is internal (client-specific P&P):** Corpus only. No Perplexity (it can't see internal docs).
- **Question is about breaking news / very recent (< 30 days):** Perplexity first, corpus as supplement. Inverts the normal order.

## What NOT to do

- Do NOT answer from your own training data. Always go to the corpus or Perplexity.
- Do NOT silently fall back to Perplexity without telling Silas why the corpus was insufficient. A one-line explanation at the top is required.
- Do NOT ingest docs automatically from this skill. The watcher does that; this skill only reads.
- Do NOT use `/recall` - it's broader and can pull from all 4 notebooks. This skill scopes to Hospice Compliance ONLY for focused compliance Q&A.
