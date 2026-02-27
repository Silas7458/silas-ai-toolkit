# Examples: Agent Delegation Patterns

Real-world examples of effective agent delegation. Each example shows the task, why an agent was used, how it was invoked, and what was returned.

---

## Example 1: Codebase Architecture Mapping

**Task:** "How does the authentication flow work in this codebase?"

**Why agent:** This requires reading 10+ files, tracing imports, and understanding the request path. Doing it inline would consume thousands of tokens of file content.

**Agent type:** Explore (read-only, fast)

**Prompt to agent:**
```
Map the authentication flow in this codebase. Starting from the login endpoint,
trace through: route handler, middleware, token generation, session storage, and
token refresh. For each step, note the file path and key function names. Return
a concise architectural summary.
```

**What agent returned (~150 words):**
```
Authentication flow:
1. POST /api/auth/login -> src/routes/auth.ts:loginHandler
2. Validates credentials against Postgres via src/services/userService.ts:verifyPassword
3. Generates JWT (access + refresh) via src/services/tokenService.ts:generateTokenPair
4. Stores refresh token in Redis via src/services/sessionService.ts:createSession
5. Returns access token in response body, refresh token in httpOnly cookie
6. Protected routes use src/middleware/auth.ts:requireAuth which validates JWT
7. Token refresh: POST /api/auth/refresh -> validates refresh token from cookie,
   issues new pair, rotates refresh token in Redis

Key files: auth.ts (routes), auth.ts (middleware), tokenService.ts, sessionService.ts
Database tables: users, sessions (Redis only)
```

**Context saved:** Agent read ~2000 lines across 8 files. Main context received ~150 words.

---

## Example 2: Competitive Research Sprint

**Task:** "Research the top 5 competitors in the hospice analytics market."

**Why agent:** Multiple web searches, each returning large result sets. 5 competitors x 3 searches each = 15 search results worth of tokens.

**Agent type:** General-purpose (needs web search)

**Pattern:** 3 agents fired in parallel

**Agent 1 prompt:**
```
Research competitors A and B in the hospice analytics market. For each, find:
pricing model, key features, target customer size, market position, any recent
news. Return a structured summary for each.
```

**Agent 2 prompt:**
```
Research competitors C and D in the hospice analytics market. Same criteria:
pricing, features, target customers, market position, recent news.
```

**Agent 3 prompt:**
```
Research competitor E and the overall hospice analytics market. For competitor E:
same criteria. For the market: total addressable market size, growth rate,
key trends, regulatory factors. Return structured summaries.
```

**Synthesis (done in main context):**
After all 3 agents return, you synthesize their summaries into a unified competitive analysis. Total main context cost: ~500 words of summaries instead of ~15,000 tokens of raw search results.

---

## Example 3: Document Build

**Task:** "Create an Excel spreadsheet with quarterly revenue data for the last 3 years."

**Why agent:** Building a document requires: writing a Python script, executing it, reading any errors, fixing the script, re-executing, and verifying the output. This write-run-fix loop can take 5-10 iterations and generates substantial context.

**Agent type:** General-purpose (needs write + execute)

**Prompt to agent:**
```
Create a Python script that generates an Excel file (.xlsx) at
[YOUR_DELIVERABLES_DIR]/2026-02-26-quarterly-revenue.xlsx with these columns:
- Quarter (Q1 2024 through Q4 2026)
- Revenue
- Expenses
- Net Income
- Growth Rate (quarter over quarter)

Populate with realistic sample data showing a growth trend.
Format currency columns with $ and 2 decimal places.
Add a header row with bold formatting.
Execute the script and confirm the file exists and has the expected number of rows.
```

**What agent returned:**
```
Done. File created at [path].
- 12 rows (Q1 2024 through Q4 2026)
- 5 columns with currency formatting
- Revenue grows from $125,000 to $312,000 over the period
- Script required 2 iterations (first had an openpyxl import issue, fixed on second run)
```

**Context saved:** The entire write-debug-fix loop (script code, error output, fix, re-run output) stayed in the agent's context. Main context received 4 lines.

---

## Example 4: Large File Analysis

**Task:** "What are the error patterns in this 2000-line log file?"

**Why agent:** Reading 2000 lines into main context is wasteful when you only need a summary of patterns.

**Agent type:** General-purpose

**Prompt to agent:**
```
Read the log file at /var/log/app/production.log (last 2000 lines).
Identify: the top 5 most frequent error types, their frequency, the time
range they cover, and any patterns (e.g., errors clustering at specific times
or after specific events). Return a concise analysis.
```

**What agent returned:**
```
Log analysis (2000 lines, covering 2026-02-25 00:00 to 2026-02-26 12:00):

Top 5 errors:
1. ConnectionTimeout (PostgreSQL) - 47 occurrences, clustered at 02:00-03:00 UTC (maintenance window?)
2. RateLimitExceeded (Stripe API) - 23 occurrences, spread evenly, correlate with batch payment processing
3. ValidationError (user input) - 19 occurrences, all from /api/forms/submit endpoint
4. OutOfMemory (worker process) - 8 occurrences, all between 14:00-16:00 UTC (peak traffic)
5. FileNotFound (asset serving) - 6 occurrences, all reference /assets/legacy/* paths

Pattern: The connection timeouts correlate exactly with scheduled database maintenance.
The OOM errors are traffic-related and may need worker scaling.
```

**Context saved:** 2000 lines of raw logs stayed in agent context. Main context received ~150 words of actionable analysis.

---

## Example 5: Multi-File Code Review

**Task:** "Review the changes in this PR -- 15 files changed, 800 lines added."

**Why agent:** Reading 800+ lines of diffs inline would dominate the context window.

**Agent type:** code-reviewer (specialized, read-only)

**Prompt to agent:**
```
Review the changes in the current git diff (staged changes). Focus on:
- Logic errors or bugs
- Security concerns
- Performance issues
- Code style inconsistencies
Rate each finding by confidence (HIGH/MEDIUM/LOW). Skip LOW confidence findings.
```

**What agent returned:**
```
Review of 15 files, 823 lines changed:

HIGH confidence:
1. src/api/payment.ts:142 -- SQL injection vulnerability. User input `orderId`
   interpolated directly into query string. Use parameterized query.
2. src/services/cache.ts:89 -- Cache TTL set to 0 (no expiry). Likely a typo,
   should be 3600 (1 hour) based on the comment above.

MEDIUM confidence:
3. src/middleware/cors.ts:15 -- CORS origin set to "*" in production config.
   Should be restricted to known domains.
4. src/utils/retry.ts:34 -- Exponential backoff has no max delay cap. Could
   wait indefinitely on persistent failures. Add a maxDelay parameter.

No LOW confidence findings reported.
Summary: 2 critical issues (SQL injection, cache TTL), 2 moderate issues.
```

**Context saved:** 800 lines of diffs stayed in agent context. Main context received a focused, prioritized review.

---

*These patterns are composable. Combine them as needed -- e.g., a research sprint (parallel agents) followed by a document build (single agent) using the research results.*
