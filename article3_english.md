# Security-First Approach To Defend And Rapidly Recover From Ransomware Attacks

**Source:** https://www.cohesity.com/blogs/defend-against-ransomware-attacks-a-security-first-approach/

To combat the evolving cyber threat landscape, enterprises globally are increasing their data security investments. The global spend on cybersecurity skyrocketed from $3.5 billion in 2004 to $124 billion in 2019. This 35x jump is expected to exceed $1 trillion by 2021.

Despite significant investments in data security, organizations of all sizes (large multinationals to state and city governments) are experiencing a rapid increase in frequency and intensity of ransomware attacks. The impact of these attacks can be crippling and mostly can be attributed to a combination of unresolved software vulnerabilities and internal human actions/errors, along with sophisticated tactics that incorporate numerous techniques to go undetected for some time to spread throughout an environment before manifesting.

In 2019, cyber breaches cost the global economy $2.1 trillion, and $11.5 billion of that was from ransomware attacks. Law enforcement agencies, including Europol pointed out that ransomware remains the top threat worldwide. Yet as reported by Forrester Research, only 21 percent of surveyed organizations confirmed they have contingency plans to recover from ransomware attacks, and only 11 percent of survey respondents said that they were confident to recover their data within three days of an attack.

## So Why Are Organizations Unable to Defend Against Ransomware?

To ensure a payout, cyber criminals are not just attacking the production environment but increasingly targeting backup data and infrastructure—effectively hobbling the "insurance policy" organizations depend upon when disaster strikes. The attackers are often exploiting weaknesses associated with legacy backup solutions architectured before the advent of the ransomware industry. Before encrypting the production environment, sophisticated malware is known to destroy shadow copies and restore-point data. Due to its underlying architecture these malware make legacy backup infrastructure easy prey rather than a defense against ransomware attacks.

Continued employee cybersecurity education and investment in security tools is important. Organizations also need to deploy a modern, robust backup solution that helps protect backup data against ransomware attacks and rapidly recover to reduce downtime.

Cohesity's comprehensive anti-ransomware solution goes beyond detection. Following a typical attack lifecycle, Cohesity offers an end-to-end solution that helps enterprises:

- Reduce their attack surface
- Protect backup data with unique immutable architecture and easy policy-based data management
- Detect anomalies that signal potential attacks with machine learning
- Deep visibility to ensure the backups are clean and won't re-inject vulnerabilities while restoring
- And most importantly, rapidly recovery to reduce downtime

## Reduce Attack Surface

Cohesity customers reduce their data footprint by consolidating various backup components, disaster recovery, file services, object storage, dev/test and analytics on one web-scale platform. Customers further reduce their data footprint and attack surface with Cohesity's global variable-length dedupe across data sources and compression. This helps enterprises to reduce their exposure to cyber criminals.

## Prevent Backup from Becoming a Ransomware Target

A modern backup solution with multi-layered defence approach is needed to defend against sophisticated ransomware attacks, which include:

- **Immutable File System:** At its core, Cohesity's immutable file system, SpanFS, keeps the backup jobs in time-base immutable snapshots. The original backup job is kept in an immutable state and is never made accessible, which prevents it from being mounted by an external system. The only way to mount the backup in read-write mode is to clone that original backup, which is done automatically by the system. Although ransomware may be able to delete files in the mounted (read-write) backup, it cannot affect the immutable snapshot.

- **DataLock:** DataLock is a WORM for backup snapshots that offers another layer of protection against ransomware attack. Available since Cohesity Pegasus 6.1, this capability enables security officers to create and apply a "DataLock" policy to selected jobs and achieve a higher order of immutability for protected data—something that security officers and admins cannot modify/delete. This feature integrates with RBAC, eliminating the need for third-party tools.

- **Multi-Factor Authentication:** As much as we want passwords to offer guaranteed protection, passwords get compromised all the time. Cohesity offers multi-factor authentication, which is the best way to mitigate against phishing schemes and other password hacks.

- **Policy-Based Air Gap:** Nothing is 100% certain (other than taxes and death); hence replicating your mission-critical data to another Cohesity immutable cluster/site adds an additional layer of protection against ransomware attacks. Unlike legacy solutions/approaches, where an air-gapped solution could be compromised because of replication of encrypted/ransomware affected data to the system in air-gap, replicating data to another Cohesity cluster/site does not affect the air-gapped copy because of the immutable file system on that site as well.

## Machine Learning-Based Ransomware Detection and Actionable Recommendation

In a perfect world, we shouldn't have to worry about ransomware attacks, but unfortunately, that's not our world today. In a situation where your primary environment, users, and application infrastructure is compromised, Cohesity Helios can help you out of that jam. With its latest anomaly detection, Helios, our SaaS-based, machine-drive solution, will provide eyes and visibility when you're not able to. With SmartAssist, Helios will alert not just the IT admin but also Cohesity's support team when the primary files data-change rate is out of the norm. Anomalies will be detected based on matching any larger data changes against the normal patterns, including:

- Daily change rate on logical data
- Daily change rate on stored data (post-dedupe)
- Pattern based on historical data ingest
- Entropy (randomness of data)

Besides monitoring the backup data change rate to detect a potential ransomware attack, Cohesity's machine learning algorithms also help locate a clean copy of the data that can be used for recovery.

## Deep Visibility for a Clean Recovery

How good is data restore if it results in re-injecting software vulnerabilities and cyber threats backup into the IT production environment… the same holes that cybercriminals previously exploited to easily access your highly fortified IT environment?

Cohesity CyberScan, gives backup operators deep visibility into their snapshot's health and recoverability status. Instead of blindly restoring from any snapshot, CyberScan shows each snapshot's vulnerability index and actionable recommendation to address those software vulnerabilities. The solution is designed to help organizations cleanly and predictably recover after a ransomware attack without compromising or re-injecting any vulnerabilities back into the IT production environment.

## Rapid Recovery to Reduce Downtime

The most important requirement after a ransomware attack is having the ability to quickly recover compromised data. Unlike any solution available in the industry today, Cohesity offers the ability to locate data across your global footprint, including in the public cloud. Your apps and data are instantly brought back using Cohesity's instant mass restore by offering:

- **Unlimited Scalability:** A web-scale platform that allows IT admins to grow their Cohesity cluster from three to unlimited nodes with the ability to store unlimited snaps and clones without any performance impact.

- **Global Actionable Search:** Unlike legacy solutions that rely on third-party search products, Cohesity's unique, Google-like global search capability that allows you to quickly locate data and infected files and take appropriate corrective actions. This includes finding a malicious file across all workloads and taking necessary action to contain it.

- **MegaFile:** A patented approach to intelligently distribute files across all nodes in a cluster. An aspect of Cohesity's architecture, MegaFile breaks large files into smaller chunks for parallel backup and recovery across nodes. The specific size of these chunks is unique, optimized to maximize performance.

- **Instant Mass Restore:** When ransomware strikes, you are not dealing with one, two, or a few VMs/files, but rather a disaster recovery scenario in which the IT admin needs to recover hundreds of VMs. Unlike other backup solutions, traditional or modern alike, it can take days, if not weeks to recover. With Cohesity's instant mass restore, IT admins can recover hundreds of VMs instantly, at scale, to any point in time.

Ransomware is so common it has practically become a household name. Yet ransomware remains a daunting threat to enterprises in need of a modern solution that offers more than the ability to simply detect a threat.
