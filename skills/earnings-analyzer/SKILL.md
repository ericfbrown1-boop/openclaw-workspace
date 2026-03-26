---
name: earnings-analyzer
description: >
  Automated SEC earnings analysis for Cohesity, Rubrik, Commvault, and Veeam.
  Pulls 10-Q/10-K filings, calculates YoY ARR/revenue growth, margins,
  valuation multiples. Outputs Word doc + email delivery.
---

# Earnings Analyzer

## When to Use
- Eric asks for financial analysis of any public company
- Quarterly earnings are released for Rubrik, Commvault, or Veeam
- Daily briefing needs competitive financial data

## Workflow
1. Pull latest earnings from SEC EDGAR or company IR page
2. Extract: revenue, ARR, YoY growth, GAAP margins, cash flow
3. Compare to prior 4 quarters (table format)
4. Calculate valuation multiples (revenue, ARR, non-GAAP operating income)
5. Generate Word document
6. Email to ericfbrown1@gmail.com + Eric.brown@cohesity.com

## Data Sources
- SEC EDGAR API (10-Q, 10-K, 8-K filings)
- Company investor relations pages
- Yahoo Finance / Google Finance for stock data

## Output Format
- Word document (.docx) with tables and analysis
- Google Sheets update (optional)

## Status: SKELETON — Implementation needed
