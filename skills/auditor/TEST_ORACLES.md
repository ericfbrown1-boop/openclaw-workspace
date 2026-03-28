# Test Oracle Schemas — Verification Standards

Every task must define expected outcomes BEFORE implementation begins.
Agents use these schemas to verify their own work and validate handoffs.

## Universal Oracle: Task Completion

Every task in `tasks.json` must pass ALL of these before reaching 100%:

```json
{
  "oracle": "task_completion",
  "checks": [
    {"name": "phase_compliance", "rule": "task.phase history includes all 4 phases (understand, plan, implement, verify)"},
    {"name": "success_criteria_defined", "rule": "task.successCriteria is non-empty array"},
    {"name": "all_criteria_met", "rule": "every item in successCriteria has passed=true"},
    {"name": "proof_exists", "rule": "code tasks: completedCommit is valid SHA; report tasks: deliverableEmailId exists"},
    {"name": "no_regressions", "rule": "pre-existing tests still pass after changes"}
  ]
}
```

---

## Oracle: Code Tasks

```yaml
name: code_task
verify_before_handoff:
  - import_check: "python3 -c 'import <module>' succeeds for every new/modified file"
  - lint_clean: "ruff check --select E,F,W <files> returns 0 errors"
  - tests_pass: "pytest / npm test / project test command exits 0"
  - docker_builds: "docker build -t <name> . completes without error"
  - health_check: "curl -fsS http://localhost:<port>/health returns HTTP 200"
  - no_secrets: "detect-secrets scan <files> finds no new secrets"  # pragma: allowlist secret
  - git_pushed: "git push origin <branch> succeeds"
verify_after_deploy:
  - smoke_test: "curl -fsS https://<deployed-url>/health returns HTTP 200"
  - response_valid: "API response matches expected JSON schema"
  - no_error_logs: "No ERROR/CRITICAL in logs within 5 min of deploy"
```

## Oracle: Research Tasks

```yaml
name: research_task
verify_before_delivery:
  - sources_cited: "Every claim has at least 1 source (URL, document, or data point)"
  - cross_checked: "Key findings verified against 2+ independent sources"
  - date_relevant: "All data is from within the last 90 days (or explicitly noted as older)"
  - format_correct: "Output matches requested format (Word doc, markdown, email)"
  - delivered: "Email sent via gog or Zapier with correct recipients and CC"
```

## Oracle: Report/Deliverable Tasks

```yaml
name: report_task
verify_before_delivery:
  - outline_reviewed: "Report outline was approved before full writing"
  - all_sections_present: "Every section from the outline appears in the final doc"
  - data_accurate: "Numbers match source data (spot-check 3 random figures)"
  - format_clean: "No placeholder text, no TODO markers, no broken tables"
  - email_sent: "gog gmail send succeeded, Gmail message ID captured"
  - cc_included: "ericfbrown1@gmail.com in CC per USER.md rules"
```

## Oracle: Error Diagnosis Tasks

```yaml
name: error_diagnosis
verify_before_closing:
  - root_cause_identified: "5-Whys analysis completed (minimum 3 levels)"
  - fix_implemented: "Code change or config change committed"
  - fix_verified: "The original error no longer reproduces"
  - regression_check: "Existing tests still pass after the fix"
  - incident_logged: "Entry added to memory/incidents.jsonl with full schema"
  - prevention_added: "KNOWN_FAILURES.md or relevant SKILL.md updated"
```

## Oracle: Monitoring Tasks

```yaml
name: monitoring_sweep
verify_per_sweep:
  - all_checks_ran: "Every step in the sweep checklist executed (no skips)"
  - failures_acted_on: "Every failed check has an action taken (not just logged)"
  - state_updated: "tasks.json, cron-state.json, auth-fallback-state.json reflect current reality"
  - alerts_sent: "Critical failures triggered Telegram/email notification within 1 minute"
  - incidents_logged: "All new failures logged to memory/incidents.jsonl"
```

## Oracle: Earnings Analysis Tasks

```yaml
name: earnings_analysis
verify_before_delivery:
  - filing_source: "10-Q/10-K filing date and period clearly stated"
  - metrics_complete: "Revenue, ARR, margins (gross/operating/net), cash flow all present"
  - yoy_comparison: "At least 4 prior quarters shown for trend analysis"
  - multiples_calculated: "EV/Revenue, EV/ARR computed with current market data"
  - guidance_included: "Next quarter guidance midpoint and implied growth rate"
  - word_doc_generated: "python-docx output opens without error"
  - emailed: "Sent to ericfbrown1@gmail.com + Eric.brown@cohesity.com"
```

## Oracle: Competitive Intelligence Tasks

```yaml
name: competitive_intel
verify_before_delivery:
  - all_competitors_covered: "Rubrik, Commvault, Veeam all included"
  - stock_data_fresh: "RBRK and CVLT prices from today (not cached)"
  - news_relevant: "All items from within last 7 days"
  - actionable: "At least 1 item flagged as 'action needed' or 'FYI for Eric'"
  - format_briefing_ready: "Output is markdown, under 500 words, suitable for email section"
```

## How Agents Use Oracles

1. **Planner**: Includes relevant oracle in PLAN.md `successCriteria` field
2. **Coder/Researcher**: Self-checks against oracle BEFORE writing HANDOFF.md
3. **Tester**: Validates oracle checks programmatically where possible
4. **Quality**: Confirms all oracle checks passed during review
5. **Monitor**: Verifies tasks marked 100% actually satisfy their oracle
6. **External Auditor**: Uses oracle as the acceptance checklist for sign-off

## Oracle: Docker-Deployed App (NEW 2026-03-27)
**Origin:** FinancialReportApp RCA — silent failures in env vars, parsers, and output content.

```yaml
name: docker_deployed_app
verify_on_deploy:
  - env_vars_valid: "docker exec <container> env | grep KEY → each key matches expected prefix and length (>80 chars for API keys)"
  - no_inline_comments: ".env file has NO inline comments (# on same line as value)"
  - startup_validation: "Container validates env vars on startup and fails fast if invalid"
  - api_connectivity: "Container can reach external APIs (Anthropic, Google, etc.) — test with actual API call, not just DNS"
  - parser_schemas_separate: "Each data schema has its own parser; no shared parser with wrong fallback shapes"
verify_output_quality:
  - content_not_defaults: "Deliverable contains <3 instances of 'not available', 'not found', or placeholder text"
  - content_sufficient: "Main content section (e.g., executive_summary) is >100 characters of real analysis"
  - structured_output_used: "LLM calls use output_format/JSON mode when available, not free-text parsing"
  - silent_fallback_counted: "Pipeline logs WARNING for every fallback to default; >3 defaults = pipeline FAIL"
  - e2e_smoke_test: "Full pipeline executed with real input, output artifact opened and content verified"
verify_data_flow:
  - synthesis_keys_present: "All expected fields (executive_summary, quarterly_results, guidance, etc.) exist at top level of merged dict"
  - no_nested_wrapping: "Data from LLM is merged at top level, not nested under a wrapper key like 'synthesis' or 'data'"
  - parse_error_recovered: "If _parseError occurs, _rawResponse is re-parsed before using fallback"
```

## Oracle: LLM Pipeline (NEW 2026-03-27)
**Origin:** FinancialReportApp RCA — parser silently swallowed synthesis output.

```yaml
name: llm_pipeline
verify_before_handoff:
  - schema_validated: "LLM output matches expected Pydantic model or JSON schema"
  - no_parse_errors: "No _parseError flags in final output dict"
  - required_fields_present: "All fields consumed by downstream components exist and are non-empty"
  - raw_response_preserved: "On parse failure, raw LLM text is logged/stored for debugging"
  - fallback_shape_correct: "Parser fallback returns dict shaped like the expected output (not a different schema)"
  - cost_logged: "Token usage and estimated cost logged for every LLM call"
```
