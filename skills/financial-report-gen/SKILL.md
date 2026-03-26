---
name: financial-report-gen
description: >
  Generate formatted Word/PDF financial reports. Pulls data from earnings,
  Google Sheets, and analysis. Emails to Eric with proper formatting.
---

# Financial Report Generator

## When to Use
- After earnings analysis is complete
- Eric requests a formatted report
- Quarterly competitive comparison needed

## Output Formats
- Word (.docx) — primary format per USER.md
- PDF (optional)
- Google Sheets update (optional)

## Template Sections
1. Executive Summary (1 paragraph)
2. Revenue & ARR Analysis (table + commentary)
3. Margin Trends (GAAP gross, operating, net)
4. Cash Flow Analysis (FCF, operating cash flow)
5. Valuation Multiples (vs peers)
6. Product & Use-Case Highlights
7. Risks & Considerations

## Email Delivery
- To: ericfbrown1@gmail.com, Eric.brown@cohesity.com
- CC: ericfbrown1@gmail.com
- Footer: "Sent by Jarvis - AI assistant to Eric Brown"
- Use: gog gmail send (primary) or Zapier MCP (fallback)

## Status: SKELETON — Implementation needed
