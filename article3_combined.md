---
title: "Security-First Approach To Defend And Rapidly Recover From Ransomware Attacks"
subtitle: "Approche Axée sur la Sécurité pour se Défendre et Récupérer Rapidement des Attaques Ransomware"
---

**Source:** https://www.cohesity.com/blogs/defend-against-ransomware-attacks-a-security-first-approach/

\newpage

# ENGLISH VERSION

# Security-First Approach To Defend And Rapidly Recover From Ransomware Attacks

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

\newpage

# VERSION FRANÇAISE

# Approche Axée sur la Sécurité pour se Défendre et Récupérer Rapidement des Attaques Ransomware

Pour combattre le paysage des cybermenaces en évolution, les entreprises à l'échelle mondiale augmentent leurs investissements en sécurité des données. Les dépenses mondiales en cybersécurité ont grimpé de 3,5 milliards de dollars en 2004 à 124 milliards de dollars en 2019. Ce bond de 35x devrait dépasser 1 billion de dollars d'ici 2021.

Malgré des investissements importants en sécurité des données, les organisations de toutes tailles (grandes multinationales aux gouvernements d'État et de ville) connaissent une augmentation rapide de la fréquence et de l'intensité des attaques ransomware. L'impact de ces attaques peut être paralysant et peut être principalement attribué à une combinaison de vulnérabilités logicielles non résolues et d'actions/erreurs humaines internes, ainsi qu'à des tactiques sophistiquées qui intègrent de nombreuses techniques pour passer inaperçues pendant un certain temps afin de se propager dans tout un environnement avant de se manifester.

En 2019, les violations cybernétiques ont coûté à l'économie mondiale 2,1 billions de dollars, et 11,5 milliards de dollars provenaient d'attaques ransomware. Les agences d'application de la loi, y compris Europol, ont souligné que le ransomware reste la menace principale dans le monde. Pourtant, comme l'a rapporté Forrester Research, seulement 21 pour cent des organisations interrogées ont confirmé avoir des plans d'urgence pour se remettre d'attaques ransomware, et seulement 11 pour cent des répondants au sondage ont déclaré qu'ils étaient confiants de récupérer leurs données dans les trois jours suivant une attaque.

## Alors Pourquoi les Organisations ne Peuvent-elles pas se Défendre contre le Ransomware ?

Pour assurer un paiement, les cybercriminels n'attaquent pas seulement l'environnement de production mais ciblent de plus en plus les données et l'infrastructure de sauvegarde—paralysant efficacement la « police d'assurance » sur laquelle les organisations comptent lorsque le désastre frappe. Les attaquants exploitent souvent les faiblesses associées aux solutions de sauvegarde héritées architecturées avant l'avènement de l'industrie du ransomware. Avant de chiffrer l'environnement de production, les malwares sophistiqués sont connus pour détruire les copies shadow et les données de point de restauration. En raison de son architecture sous-jacente, ces malwares font de l'infrastructure de sauvegarde héritée une proie facile plutôt qu'une défense contre les attaques ransomware.

La formation continue des employés en cybersécurité et l'investissement dans les outils de sécurité sont importants. Les organisations doivent également déployer une solution de sauvegarde moderne et robuste qui aide à protéger les données de sauvegarde contre les attaques ransomware et à récupérer rapidement pour réduire les temps d'arrêt.

La solution anti-ransomware complète de Cohesity va au-delà de la détection. Suivant un cycle de vie d'attaque typique, Cohesity offre une solution de bout en bout qui aide les entreprises à :

- Réduire leur surface d'attaque
- Protéger les données de sauvegarde avec une architecture immuable unique et une gestion des données basée sur des politiques faciles
- Détecter les anomalies qui signalent des attaques potentielles avec l'apprentissage automatique
- Visibilité approfondie pour s'assurer que les sauvegardes sont propres et ne réinjecteront pas de vulnérabilités lors de la restauration
- Et surtout, récupération rapide pour réduire les temps d'arrêt

## Réduire la Surface d'Attaque

Les clients Cohesity réduisent leur empreinte de données en consolidant divers composants de sauvegarde, reprise après sinistre, services de fichiers, stockage d'objets, dev/test et analytique sur une plateforme web-scale unique. Les clients réduisent encore leur empreinte de données et leur surface d'attaque avec la déduplication globale à longueur variable de Cohesity entre les sources de données et la compression. Cela aide les entreprises à réduire leur exposition aux cybercriminels.

## Empêcher la Sauvegarde de Devenir une Cible de Ransomware

Une solution de sauvegarde moderne avec une approche de défense multicouche est nécessaire pour se défendre contre les attaques ransomware sophistiquées, qui comprennent :

- **Système de Fichiers Immuable :** Au cœur de Cohesity se trouve le système de fichiers immuable, SpanFS, qui conserve les travaux de sauvegarde dans des snapshots immuables basés sur le temps. Le travail de sauvegarde original est conservé dans un état immuable et n'est jamais rendu accessible, ce qui l'empêche d'être monté par un système externe. La seule façon de monter la sauvegarde en mode lecture-écriture est de cloner cette sauvegarde originale, ce qui est fait automatiquement par le système. Bien que le ransomware puisse supprimer des fichiers dans la sauvegarde montée (lecture-écriture), il ne peut pas affecter le snapshot immuable.

- **DataLock :** DataLock est un WORM pour les snapshots de sauvegarde qui offre une autre couche de protection contre les attaques ransomware. Disponible depuis Cohesity Pegasus 6.1, cette capacité permet aux responsables de la sécurité de créer et d'appliquer une politique « DataLock » à des travaux sélectionnés et d'atteindre un ordre supérieur d'immutabilité pour les données protégées—quelque chose que les responsables de la sécurité et les administrateurs ne peuvent pas modifier/supprimer. Cette fonctionnalité s'intègre avec RBAC, éliminant le besoin d'outils tiers.

- **Authentification Multifacteur :** Autant nous voulons que les mots de passe offrent une protection garantie, les mots de passe sont compromis tout le temps. Cohesity offre une authentification multifacteur, qui est la meilleure façon de se prémunir contre les schémas de phishing et autres piratages de mots de passe.

- **Air Gap Basé sur des Politiques :** Rien n'est certain à 100% (autre que les impôts et la mort) ; par conséquent, la réplication de vos données mission-critiques vers un autre cluster/site immuable Cohesity ajoute une couche supplémentaire de protection contre les attaques ransomware. Contrairement aux solutions/approches héritées, où une solution air-gap pourrait être compromise en raison de la réplication de données chiffrées/affectées par ransomware vers le système en air-gap, la réplication de données vers un autre cluster/site Cohesity n'affecte pas la copie air-gap en raison du système de fichiers immuable sur ce site également.

## Détection de Ransomware Basée sur l'Apprentissage Automatique et Recommandation Actionnable

Dans un monde parfait, nous ne devrions pas avoir à nous soucier des attaques ransomware, mais malheureusement, ce n'est pas notre monde aujourd'hui. Dans une situation où votre environnement principal, vos utilisateurs et votre infrastructure d'application sont compromis, Cohesity Helios peut vous aider à sortir de cette impasse. Avec sa dernière détection d'anomalies, Helios, notre solution basée sur SaaS et pilotée par machine, fournira des yeux et une visibilité lorsque vous n'êtes pas capable de le faire. Avec SmartAssist, Helios alertera non seulement l'administrateur IT mais aussi l'équipe de support de Cohesity lorsque le taux de changement de données des fichiers primaires est hors de la norme. Les anomalies seront détectées en faisant correspondre les changements de données plus importants aux modèles normaux, y compris :

- Taux de changement quotidien sur les données logiques
- Taux de changement quotidien sur les données stockées (post-déduplication)
- Modèle basé sur l'ingestion de données historiques
- Entropie (caractère aléatoire des données)

En plus de surveiller le taux de changement des données de sauvegarde pour détecter une attaque ransomware potentielle, les algorithmes d'apprentissage automatique de Cohesity aident également à localiser une copie propre des données qui peut être utilisée pour la récupération.

## Visibilité Approfondie pour une Récupération Propre

Quelle est la valeur d'une restauration de données si elle entraîne la réinjection de vulnérabilités logicielles et de menaces cybernétiques dans l'environnement de production IT… les mêmes failles que les cybercriminels ont précédemment exploitées pour accéder facilement à votre environnement IT hautement fortifié ?

Cohesity CyberScan donne aux opérateurs de sauvegarde une visibilité approfondie sur l'état de santé et le statut de récupérabilité de leurs snapshots. Au lieu de restaurer aveuglément à partir de n'importe quel snapshot, CyberScan montre l'indice de vulnérabilité de chaque snapshot et des recommandations actionnables pour traiter ces vulnérabilités logicielles. La solution est conçue pour aider les organisations à récupérer proprement et de manière prévisible après une attaque ransomware sans compromettre ou réinjecter de vulnérabilités dans l'environnement de production IT.

## Récupération Rapide pour Réduire les Temps d'Arrêt

L'exigence la plus importante après une attaque ransomware est d'avoir la capacité de récupérer rapidement les données compromises. Contrairement à toute solution disponible dans l'industrie aujourd'hui, Cohesity offre la capacité de localiser les données dans votre empreinte mondiale, y compris dans le cloud public. Vos applications et données sont instantanément restaurées en utilisant la restauration massive instantanée de Cohesity en offrant :

- **Évolutivité Illimitée :** Une plateforme web-scale qui permet aux administrateurs IT de faire croître leur cluster Cohesity de trois à un nombre illimité de nœuds avec la capacité de stocker des snaps et des clones illimités sans impact sur les performances.

- **Recherche Globale Actionnable :** Contrairement aux solutions héritées qui s'appuient sur des produits de recherche tiers, la capacité de recherche globale unique de Cohesity, similaire à Google, vous permet de localiser rapidement les données et les fichiers infectés et de prendre les mesures correctives appropriées. Cela inclut la recherche d'un fichier malveillant dans toutes les charges de travail et la prise de mesures nécessaires pour le contenir.

- **MegaFile :** Une approche brevetée pour distribuer intelligemment les fichiers sur tous les nœuds d'un cluster. Un aspect de l'architecture de Cohesity, MegaFile divise les gros fichiers en morceaux plus petits pour une sauvegarde et une récupération parallèles sur les nœuds. La taille spécifique de ces morceaux est unique, optimisée pour maximiser les performances.

- **Restauration Massive Instantanée :** Lorsque le ransomware frappe, vous ne traitez pas un, deux ou quelques VM/fichiers, mais plutôt un scénario de reprise après sinistre dans lequel l'administrateur IT doit récupérer des centaines de VM. Contrairement à d'autres solutions de sauvegarde, traditionnelles ou modernes, cela peut prendre des jours, voire des semaines pour récupérer. Avec la restauration massive instantanée de Cohesity, les administrateurs IT peuvent récupérer des centaines de VM instantanément, à grande échelle, à n'importe quel moment dans le temps.

Le ransomware est si courant qu'il est pratiquement devenu un nom familier. Pourtant, le ransomware reste une menace redoutable pour les entreprises qui ont besoin d'une solution moderne qui offre plus que la simple capacité de détecter une menace.
