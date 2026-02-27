# Examples: Research Sprint Pattern

The research sprint is a parallel agent pattern for gathering information across multiple domains simultaneously. Instead of running searches sequentially (burning context with each result), you fire multiple agents that each handle a research track and return focused summaries.

---

## When to Use

- User asks about a topic that spans multiple domains or competitors
- You need data from 5+ web searches
- Research tracks are independent (results do not depend on each other)
- Time matters -- parallel agents complete faster than sequential searches

---

## Pattern Structure

```
                    [Main Context]
                         |
              Define research tracks
                    /    |    \
                   /     |     \
            [Agent 1] [Agent 2] [Agent 3]
            Track A    Track B   Track C
                   \     |     /
                    \    |    /
                Summaries return
                         |
                    [Main Context]
                   Synthesize results
                         |
                    Report to user
```

---

## Step-by-Step

### Step 1: Define Research Tracks
Break the research question into 3-5 independent tracks. Each track should be specific enough for one agent to handle in a focused session.

**Example:** "Research the home health technology market"
- Track 1: Market size and growth (TAM, SAM, SOM, growth rates, forecasts)
- Track 2: Key players and competitive landscape (top 10 companies, market share, funding)
- Track 3: Technology trends (AI/ML adoption, interoperability, remote monitoring)
- Track 4: Regulatory environment (CMS changes, OASIS updates, compliance requirements)
- Track 5: Customer segments (enterprise vs SMB, buyer personas, pain points)

### Step 2: Fire Agents in Parallel
Launch all agents simultaneously. Each gets a focused prompt:

```
Agent 1: "Research the home health technology market SIZE. Find: total addressable
market (current and projected 5 years out), serviceable addressable market,
growth rate (CAGR), key drivers of growth, and any recent market reports with
specific numbers. Return a structured summary with sources."

Agent 2: "Research the key PLAYERS in the home health technology market. Find:
top 10 companies by revenue/market share, their primary products, recent funding
rounds, any M&A activity in the last 2 years, and competitive positioning.
Return a structured comparison table."

[... agents 3-5 similarly focused ...]
```

### Step 3: Collect Summaries
Each agent returns a ~200-500 word summary. Total context cost: ~1500-2500 words.

Compare this to running 15-20 web searches inline: ~15,000-20,000 tokens of raw search results.

### Step 4: Synthesize
In your main context, synthesize the agent summaries into a unified analysis. This is the high-value work -- connecting insights across domains -- and it benefits from having your full context available for reasoning.

### Step 5: Deliver
Present the synthesized analysis to the user, or feed it into a document-building agent for formal output.

---

## Real Example: Video Content Research

**User request:** "What are the top TikTok creators talking about regarding AI tools?"

**Track 1 agent:**
```
Search for "top TikTok creators AI tools 2026" and related queries.
Find: which creators are making AI tool content, their follower counts,
what specific tools they feature, and their general sentiment.
Return the top 10 creators with brief profiles.
```

**Track 2 agent:**
```
Search for "most popular AI tools on TikTok 2026" and related queries.
Find: which AI tools are trending on TikTok, download/usage numbers if
available, what categories they fall into (image gen, writing, coding, etc.),
and any viral trends around them. Return a ranked list with context.
```

**Track 3 agent:**
```
Search for "TikTok AI content trends 2026" and related queries.
Find: what formats are popular (tutorials, reviews, challenges, skits),
what audience engagement looks like, any platform-specific AI features
TikTok has launched, and how the algorithm treats AI content.
Return a trend analysis.
```

**Synthesis:** Combine creator profiles, tool rankings, and trend analysis into a unified briefing.

---

## Tips

- **Be specific in agent prompts.** "Research X" is too vague. "Find pricing data, market share, and recent funding for X" gives the agent clear targets.
- **Set output expectations.** "Return a structured summary" or "Return a comparison table" tells the agent what format you need.
- **Ask for sources.** Include "with sources" in the prompt so you can verify key claims.
- **Do not over-parallelize.** 3-5 agents is the sweet spot. More than that and the synthesis step becomes unwieldy.
- **Independent tracks only.** If Track B depends on Track A's results, run them sequentially, not in parallel.

---

*The research sprint is one of the highest-leverage agent patterns. It typically saves 10,000+ tokens of context while completing research 2-3x faster than sequential searches.*
