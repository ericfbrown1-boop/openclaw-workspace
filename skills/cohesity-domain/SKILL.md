---
name: cohesity-domain
description: >
  Cohesity product and market domain knowledge. Data protection,
  backup/recovery, ransomware defense, cloud migration context.
  Competitor feature comparison.
---

# Cohesity Domain Knowledge

This is a reference document, not a script. Use this context when answering questions about Cohesity products, competitive positioning, market trends, or preparing materials for Eric.

## When to Use

- Competitive positioning questions or deal support
- Product feature comparisons (Cohesity vs Rubrik/Commvault/Veeam)
- Board or investor materials requiring market context
- Customer conversation prep for Eric
- Analyst briefing prep (Gartner, IDC, Forrester)
- Any prompt that references data protection, backup, or cyber resilience

## Company Overview

**Cohesity** — Founded 2013 by Mohit Aron (also co-founded Nutanix). Headquartered in San Jose, CA. Merged with Veritas data protection business in early 2024, creating the largest pure-play data protection vendor by installed base. Private (backed by Sequoia, SoftBank Vision Fund, CPPIB, among others). Last reported valuation ~$7B (pre-merger).

**CEO**: Sanjay Poonen (former VMware COO)
**CFO & COO**: Eric Brown

## Core Products

### Cohesity DataProtect
Primary backup and recovery platform. Runs on Cohesity DataCloud architecture.
- **SpanFS**: Distributed file system purpose-built for secondary data. Snap-tree architecture enables unlimited immutable snapshots with zero performance penalty.
- **Global deduplication**: Variable-length, inline dedup across all data sources.
- **Instant mass restore**: Boot hundreds of VMs directly from backup in minutes.
- **Workload coverage**: VMware, Hyper-V, AWS EC2, Azure VMs, SQL Server, Oracle, SAP HANA, NAS, M365, Salesforce, Kubernetes (via Kasten integration).

### Cohesity DataHawk
Threat protection and data classification add-on.
- **ML-based ransomware detection**: Anomaly detection on backup data entropy and change rates.
- **DataLock WORM**: Software-based write-once-read-many with CFTC/SEC compliance.
- **Threat intelligence**: IOC scanning integrated into backup workflows.
- **Data classification**: Automated PII/PHI/PCI discovery across backup data.

### Cohesity FortKnox
SaaS-delivered cyber vaulting (isolated recovery environment).
- Air-gapped cloud vault with Cohesity-managed infrastructure.
- Quorum-based access controls (multi-person authorization for vault operations).
- Clean room recovery for forensic investigation.

### Cohesity SmartFiles
Unstructured data management for file and object workloads.
- Tiering policies (hot/warm/cold to cloud).
- NFS/SMB/S3 protocol support.

## Competitive Comparison

### Data Protection Platform Comparison

| Capability              | Cohesity DataProtect      | Rubrik Security Cloud     | Commvault Cloud           | Veeam B&R v12+           |
|-------------------------|---------------------------|---------------------------|---------------------------|---------------------------|
| Architecture            | Web-scale, SpanFS         | Atlas distributed FS      | MediaAgent-based          | Proxy-based               |
| Immutable snapshots     | Native (SpanFS snap-tree) | Native (Atlas)            | Add-on (WORM storage)     | Hardened Linux repo       |
| SaaS delivery           | DataProtect as-a-Service  | Rubrik Cloud Vault        | Metallic SaaS             | Veeam Data Cloud          |
| Cyber vault             | FortKnox (SaaS)           | Cloud Vault               | ThreatWise + Air Gap      | Veeam Vault (new)         |
| ML anomaly detection    | DataHawk (integrated)     | Radar (integrated)        | Threat Scan (add-on)      | Inline malware scan       |
| Data classification     | DataHawk                  | Sensitive Data Monitoring | Risk Analysis             | Limited                   |
| Kubernetes backup       | Kasten K10 (acquired)     | Native K8s support        | Limited                   | Kasten partnership        |
| M365 protection         | Native + DMaaS            | Native SaaS               | Metallic                  | VBO (Veeam Backup for M365)|
| Global scale-out        | Unlimited nodes            | Cluster-based             | Horizontal MediaAgents    | Scale-up per proxy        |
| Deployment model        | Appliance, VM, cloud      | Appliance, VM, SaaS       | Software, SaaS            | Software, appliance       |

### Key Differentiators — Cohesity Advantages

1. **SpanFS architecture**: Purpose-built distributed FS beats bolt-on immutability. Unlimited snapshots with zero performance degradation.
2. **Merged Veritas installed base**: Largest customer footprint in data protection. Massive upsell/cross-sell opportunity.
3. **FortKnox SaaS vault**: True air-gapped isolation managed by Cohesity. Competitors require customer-managed infrastructure.
4. **DataLock WORM compliance**: SEC 17a-4(f) and CFTC compliant. Critical for financial services.
5. **Single platform convergence**: Backup, file/object, security, and classification on one platform. Competitors require multiple products.
6. **Kasten K10**: Market-leading Kubernetes data protection (acquired 2020).

### Key Differentiators — Competitor Advantages

- **Rubrik**: Pure SaaS story resonates with cloud-first buyers. Strong brand in cyber resilience. Public company currency for M&A.
- **Commvault**: Deepest workload coverage (legacy + modern). Strong in regulated industries. Metallic SaaS growth.
- **Veeam**: Lowest TCO for SMB/mid-market. Massive partner ecosystem. Easy to deploy and manage.

## Market Context

### Gartner Magic Quadrant — Enterprise Backup & Recovery (2024)
- **Leaders**: Cohesity, Rubrik, Commvault, Veeam
- All four are in Leaders quadrant; differentiation is on vision vs. execution axes.
- Cohesity recognized for platform breadth and security integration.

### IDC MarketScape — Data Replication & Protection (2024)
- Cohesity positioned as Leader.
- Called out for convergence of data protection + security + management.

### Forrester Wave — Data Resilience Solutions (2024)
- Cohesity Strong Performer / Leader tier.
- Highlighted FortKnox and DataHawk as differentiators.

### Market Size
- **Data protection TAM**: ~$15-18B (2025), growing 10-12% CAGR.
- **Cyber resilience sub-segment**: Fastest growing at 20%+ CAGR.
- **SaaS/DMaaS**: Transition from on-prem to SaaS accelerating (30%+ of new bookings).

## Financial Context (Public Competitors)

### Rubrik (RBRK) — IPO April 2024
- FY2025 revenue run-rate: ~$900M+ (subscription ARR ~$1B)
- Growth: 35%+ YoY revenue growth
- Margins: Still GAAP unprofitable; non-GAAP operating margin improving
- Valuation: Premium multiple (15-20x EV/Revenue) reflecting growth + security positioning

### Commvault (CVLT)
- FY2025 revenue: ~$1B (subscription ARR ~$800M+)
- Growth: 15-20% YoY total revenue; subscription growing faster
- Margins: GAAP profitable; 20%+ operating margin
- Valuation: ~8-10x EV/Revenue; value story vs. Rubrik's growth story

### Veeam (Private — Insight Partners)
- Estimated ARR: $1.5B+ (largest by ARR in data protection)
- Growth: ~20% YoY
- IPO candidate (repeatedly rumored)

## Key Industry Trends

1. **Cyber resilience over backup**: Buyers frame purchases as security, not infrastructure.
2. **SaaS-first**: New deployments increasingly SaaS; on-prem still dominant installed base.
3. **AI/ML in data protection**: Anomaly detection, automated recovery, data classification.
4. **Consolidation**: Cohesity-Veritas merger signals vendor consolidation trend.
5. **Ransomware driving urgency**: CISO budget unlocked for immutable backup and clean rooms.
6. **Cloud-native workloads**: Kubernetes, serverless, and PaaS backup are emerging requirements.
7. **Data governance overlap**: DSPM and data classification blurring lines between backup and security vendors.

## Terminology Quick Reference

| Term           | Definition                                                    |
|----------------|---------------------------------------------------------------|
| ARR            | Annual Recurring Revenue                                       |
| NRR            | Net Revenue Retention (expansion - churn)                     |
| RPO            | Recovery Point Objective (max data loss tolerance)            |
| RTO            | Recovery Time Objective (max downtime tolerance)              |
| WORM           | Write Once Read Many (immutable storage compliance)           |
| Air gap        | Physical or logical isolation from production network         |
| Cyber vault    | Isolated recovery environment for ransomware scenarios        |
| DMaaS          | Data Management as a Service                                  |
| SpanFS         | Cohesity's distributed file system                            |
| DSPM           | Data Security Posture Management                              |
| TAM            | Total Addressable Market                                      |
| MQ             | Gartner Magic Quadrant                                        |
