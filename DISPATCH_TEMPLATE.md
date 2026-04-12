# DISPATCH_TEMPLATE.md — Mandatory Fields for Every Agent Dispatch
> **L1:** Every agent dispatch must include: task, agent, host, objective, files to read, existing patterns, verification command, success/failure criteria, complexity level.

**Every task dispatch from Jarvis to ANY subagent MUST include these fields. Dispatches missing `verification_command` are INVALID.**

## Required Fields

```
TASK: <one-line description>
AGENT: <agentId>
HOST: <macbook | powerspec>

OBJECTIVE: <what the agent must produce>
OUTPUT_FORMAT: <file path, email, tasks.json update, etc.>
FILES_TO_READ_FIRST: <list of files agent must read before starting>
EXISTING_PATTERNS: <reference files showing the style/pattern to follow>
DIAGRAMS: <list diagrams in PLAN.md, or "N/A — SIMPLE task (no plan required)">
  Example: System Architecture (graph TD), Process Flow (flowchart LR), ER Diagram (erDiagram)
  Rule: MODERATE or COMPLEX tasks MUST reference a PLAN.md with ≥2 Mermaid diagrams.
        Jarvis rejects Coder dispatches where PLAN.md has no diagrams.

VERIFICATION_COMMAND: <exact command that proves the task is done>
  Example: curl -fsS http://localhost:3000/terminal -w "%{http_code}" | grep 200
  Example: cd backend && npm test
  Example: git log -1 --oneline | grep "feat:"

SUCCESS_CRITERIA: <what "done" looks like — measurable>
FAILURE_CRITERIA: <what triggers a rejection back to the agent>

TASK_COMPLEXITY: <SIMPLE | MODERATE | COMPLEX>
  SIMPLE (< 5 min, single file): Main session only. No subagent.
  MODERATE (5-30 min, multi-file): Single subagent.
  COMPLEX (> 30 min, multi-step): Multi-agent with plan. Max 3 concurrent.
```

## Rules
- Jarvis must fill ALL fields before spawning. No exceptions.
- If `verification_command` is empty, the dispatch is rejected.
- Monitor checks every running task in tasks.json for a `verificationCmd` field. Missing = incident.
- MODERATE/COMPLEX tasks: verify PLAN.md exists AND has ≥2 Mermaid diagrams before dispatching to Coder.
- SIMPLE tasks do NOT spawn subagents — Jarvis does them directly.
