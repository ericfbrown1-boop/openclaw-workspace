# Claude Product Diary

**Owner:** Jarvis (maintained on behalf of Eric Brown)  
**Purpose:** Daily log of Claude / Claude Code / Anthropic platform updates and their direct relevance to Eric's use cases as CFO & COO of Cohesity.  
**Started:** 2026-04-14

## Structure

Each entry is a dated Markdown file: `YYYY-MM-DD.md`

## Eric's Core Use Cases (reference for relevance mapping)

1. **FinancialReportApp** — Earnings analysis pipeline (crawl → tag → synthesize → docx → email)
2. **Competitive Intel** — Daily monitoring of Rubrik, Commvault, Veeam, CrowdStrike
3. **Project Ajax / NemoClaw** — Enterprise AI server deployment at Cohesity
4. **Jarvis Pipeline** — Multi-agent SDLC (Research → Plan → Audit → Code → Quality)
5. **Salesforce/Snowflake analytics** — CFO/COO pipeline reviews, ARR/NRR metrics
6. **Contract analysis** — Risk review, unusual terms, missing clauses
7. **Tax automation** — Multi-property tracking, Form F, rental depreciation
8. **Daily briefings** — 6 AM PT summary across all intelligence streams

## Format Per Entry

Each daily entry captures:
- **What shipped** (product/API/Claude Code updates)
- **Eric's relevance score** (HIGH / MEDIUM / LOW per use case)
- **Specific action** (what Jarvis should build/change and estimated effort)
- **Status** (Idea → Planned → In Progress → Done)

## Integration

- Entries are indexed by the Librarian for agent prior-art lookup
- The 6 AM daily briefing includes a "Claude Product Updates" section sourced from this diary
- New entries are generated automatically by the Anthropic Ecosystem Daily Watch cron (8 AM)
  and enriched during the 6 AM briefing research phase
