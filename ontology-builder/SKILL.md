---
name: ontology-builder
description: Génère un document d'ontologie Markdown (types d'entités et de relations, regroupés par domaine métier, avec propriétés typées) à partir d'un corpus de documents — le squelette exact dont un pipeline d'extraction de graphe de connaissances (LLM → triplets → Neo4j ou tout autre graph store) a besoin pour guider ses extractions. Utilise ce skill dès que l'utilisateur veut "générer une ontologie", "créer un schéma d'entités/relations", "construire une taxonomie pour l'extraction de graphe", préparer/amorcer un graph RAG, définir les types de nœuds et relations avant d'ingérer des documents dans Neo4j (ou tout graph store), ou plus généralement structurer un corpus en catégories/relations avant du knowledge graph extraction — même si l'utilisateur ne prononce pas le mot "ontologie" explicitement (ex. "il me faut un schéma pour dire au LLM quelles entités extraire de ces PDF", "prépare la liste des types de nœuds et relations pour mon graphe"). Ne PAS utiliser ce skill pour faire l'extraction du graphe elle-même (produire les triplets, peupler Neo4j) — il produit uniquement le document de référence en amont.
---

# ontology-builder

## Ce que fait ce skill, et ce qu'il ne fait pas

Ce skill produit **un seul artefact** : un fichier Markdown qui définit, pour un corpus de documents donné, les types d'entités et de relations qu'un pipeline d'extraction de graphe de connaissances doit reconnaître — organisés par domaine métier, avec des propriétés typées. Ce document sert ensuite de référence injectée dans le prompt d'un LLM d'extraction en aval (le tien ou celui d'un pipeline existant).

Il ne fait **pas** l'extraction elle-même : pas d'appel à une base de graphe, pas de génération de triplets, pas de peuplement de Neo4j ou d'un autre graph store. Une fois le fichier écrit, ce skill s'arrête — libre à toi ou au pipeline cible de le consommer ensuite.

**Limite à connaître et à signaler à l'utilisateur** : ce skill définit des propriétés typées (nom + type + description) pour chaque type d'entité et de relation, parce que c'est la structure la plus utile pour guider une extraction de qualité. Mais tous les pipelines d'extraction de graphe existants ne savent pas forcément persister des propriétés arbitraires par type (beaucoup ne stockent qu'un label + une catégorie sur les nœuds, un type sur les relations). Si tu génères une ontologie pour un pipeline dont tu ne connais pas les capacités de stockage, dis-le explicitement à l'utilisateur : les propriétés définies ici sont un guide de qualité pour l'extraction, mais leur persistance réelle dépend du pipeline cible et peut nécessiter une extension de son code (parsing + upsert) qui n'est pas dans le périmètre de ce skill.

## Étape 0 — Rassembler les paramètres

Il te faut deux chemins avant de commencer :
1. **Le chemin source** : le dossier contenant les documents de la collection à analyser. Si l'utilisateur ne l'a pas donné explicitement, demande-le — ne devine jamais un dossier au hasard dans le projet.
2. **Le chemin de sortie**, dérivé du chemin source : `<chemin_source>/ontologie/ontologie.md`. C'est la convention par défaut de ce skill. Si le projet cible a une convention différente (par exemple un pipeline existant qui attend ses fichiers d'ontologie ailleurs, avec un nom différent, potentiellement plusieurs fichiers), demande confirmation avant d'écrire — ne suppose jamais que `<chemin_source>/ontologie/ontologie.md` convient sans le vérifier si un pipeline cible avec ses propres conventions est mentionné par l'utilisateur.

## Étape 1 — Vérifier l'existence d'une ontologie déjà présente

Avant de générer quoi que ce soit, vérifie si `<sortie>/ontologie.md` (ou tout autre fichier dans le dossier `ontologie/`) existe déjà. Si oui, **arrête-toi et demande explicitement** à l'utilisateur ce qu'il souhaite :
- **Écraser** — régénérer entièrement à partir du corpus actuel, sans tenir compte de l'existant.
- **Fusionner / étendre** — lire l'ontologie existante, la garder comme base, et ne proposer que des ajouts (nouveaux groupes, nouveaux types, nouvelles propriétés) sans modifier ce qui est déjà là. Dans ce cas, présente les ajouts proposés avant de les écrire, pour que l'utilisateur puisse les valider.
- **Annuler** — ne rien faire.

Ne jamais écraser silencieusement un fichier existant : une ontologie déjà en place a probablement été relue et ajustée manuellement, et ce travail ne doit pas disparaître sans confirmation explicite.

## Étape 2 — Inventorier et lire le corpus

Utilise Glob pour lister tous les fichiers du dossier source (attends-toi à un mélange de formats). Pour chaque fichier :
- `.md`, `.txt` → lis-le directement avec Read.
- `.pdf` → lis-le directement avec Read (le tool le supporte nativement).
- `.docx` et autres formats bureautiques (`.doc`, `.odt`, `.rtf`, `.pptx`...) → convertis-le d'abord en texte avec `scripts/convert_to_text.py` (voir ci-dessous), puis lis le résultat.

```bash
python scripts/convert_to_text.py "<fichier_source>" -o "<fichier_texte_temporaire>.md"
```

Le script tente `python-docx` en premier pour les `.docx` (installe-le avec `pip install python-docx` s'il manque), puis se rabat sur `pandoc` (binaire externe, à installer séparément si besoin) pour les autres formats. Si aucun des deux n'est disponible pour un fichier donné, le script te le dira clairement — dans ce cas, informe l'utilisateur du fichier ignoré plutôt que d'échouer silencieusement sur tout le corpus.

**Remarque sur l'encodage** : le fichier produit par le script est toujours de l'UTF-8 valide. Si tu passes par un terminal Windows et que les caractères accentués semblent corrompus dans une sortie console, c'est un problème d'affichage du terminal, pas du contenu — relis le fichier écrit avec Read plutôt que de faire confiance à ce qu'affiche la console.

Si le corpus est volumineux (plusieurs dizaines de documents), tu n'as pas besoin de tout lire mot à mot avec la même profondeur : priorise une lecture complète des documents qui semblent les plus structurants (sommaires, documents de référence, gros documents couvrant plusieurs sujets), et une lecture plus rapide des documents secondaires pour repérer des types d'entités/relations qui n'apparaîtraient pas ailleurs. L'objectif est la couverture des domaines métier réels du corpus, pas l'exhaustivité littérale de chaque phrase.

## Étape 3 — Détecter la langue et la convention de nommage

Détecte la langue dominante du corpus à partir de ce que tu viens de lire. Les noms de types d'entités et de relations dans le fichier de sortie doivent être écrits dans cette langue :
- Types d'entités en **PascalCase** (ex. `AgentContractuel`, `SupplierContract`).
- Types de relations en **camelCase** (ex. `aPourArticle`, `belongsTo`).

Si le corpus mélange plusieurs langues sans qu'une domine clairement, demande à l'utilisateur quelle langue utiliser plutôt que de deviner.

## Étape 4 — Regrouper par domaine métier et définir les types

C'est l'étape de raisonnement principale. Ne construis pas une liste plate de types — organise-les en **groupes thématiques** (domaines métier), un peu comme des chapitres qui rendraient la classification plus facile pour un lecteur humain *et* pour le LLM d'extraction qui consommera ce document plus tard : plutôt que de choisir un type dans une liste indifférenciée de 200 entrées, il choisit d'abord le bon groupe, puis le type le plus précis dedans.

Pour les **entités** :
- Identifie les domaines métier réels du corpus (les groupes ne sont jamais imposés à l'avance — ils émergent du contenu). Un domaine = un ensemble de types d'entités qui se répondent naturellement (ex. "Acteurs", "Documents contractuels", "Lieux"...).
- Pour chaque type d'entité, définis ses propriétés : nom, type de donnée (uniquement parmi `string`, `integer`, `float`, `boolean`, `date`, `enum` — n'invente pas d'autres types), et une description courte. Pour `enum`, énumère les valeurs possibles dans la description.
- Vise des types suffisamment précis pour être utiles à l'extraction (`AgentContractuel` plutôt que juste `Personne`), mais sans sur-fragmenter (ne crée pas un type différent pour chaque variation mineure si une seule propriété suffit à les distinguer).

Pour les **relations** :
- Regroupe-les aussi par domaine (souvent proche des domaines des entités, mais pas obligatoirement identique — ex. un groupe "Gouvernance" peut relier des entités de plusieurs groupes différents).
- Chaque type de relation a **exactement un couple** (type source → type cible) — jamais plusieurs couples pour un même nom. Si le corpus suggère qu'une même relation sémantique s'applique à plusieurs couples de types (ex. "s'applique à" pourrait relier une Disposition à un Agent OU à un Service), crée des noms de relation distincts pour chaque couple plutôt que d'assouplir le typage (ex. `sAppliqueAAgent` et `sAppliqueAService`). Ça demande un peu plus de types, mais ça évite l'ambiguïté qui fait dériver un LLM d'extraction en aval.
- Définis les propriétés de chaque relation de la même façon que pour les entités (nom + type fixe + description) — les relations en portent souvent moins que les entités, et beaucoup n'en ont aucune, ce qui est normal.

## Étape 5 — Rédiger le fichier

Lis `references/example_ontology.md` pour voir un exemple complet et concret du squelette attendu (un mini-corpus fictif sur les contrats fournisseurs, 2 groupes d'entités, 2 groupes de relations). Reproduis exactement cette structure de titres pour ton propre contenu :

```markdown
# Ontologie — <Nom de la collection>

Ontologie générée à partir de <N> documents sources (<brève description>).

## Vue d'ensemble
<Prose libre : domaines couverts, périmètre métier du corpus>

## Groupes d'entités

### Groupe : <NomDuDomaine>
<Description courte du domaine>

- **<NomTypeEntité>**
  - Propriétés :
    - <nomPropriété> (type) — <description courte>

## Groupes de relations

### Groupe : <NomDuDomaine>
<Description courte du domaine>

- **<nomRelation>** : <TypeEntitéSource> → <TypeEntitéCible>
  - Propriétés :
    - <nomPropriété> (type) — <description courte>
```

Écris le fichier à `<sortie>/ontologie.md` (crée le dossier `ontologie/` s'il n'existe pas).

## Étape 6 — Conclure

Une fois le fichier écrit, résume à l'utilisateur ce qui a été produit : nombre de groupes d'entités et de relations, nombre total de types, langue détectée. Rappelle la limite connue sur la persistance des propriétés (voir en haut de ce fichier) si le contexte de la conversation laisse penser que l'utilisateur va brancher cette ontologie sur un pipeline d'extraction existant dont les capacités de stockage ne sont pas confirmées. N'entreprends aucune action supplémentaire (pas de déclenchement d'extraction, pas d'appel à un pipeline externe) sauf demande explicite.

## Anti-patterns à éviter

- **Liste plate sans groupes** : même un corpus simple avec peu de types bénéficie d'au moins un groupe explicite — ça garde le document extensible si le corpus grossit plus tard.
- **Relations à domaine/codomaine multiple** : ne jamais écrire `relationX : TypeA|TypeB → TypeC` — toujours un type distinct par couple.
- **Types de propriété inventés** : rester strictement dans `string`, `integer`, `float`, `boolean`, `date`, `enum`.
- **Deviner le chemin de sortie d'un pipeline cible existant** : si l'utilisateur mentionne un pipeline qui consomme déjà des fichiers d'ontologie avec sa propre convention de chemin/nommage, vérifie cette convention avant d'écrire plutôt que d'imposer `<source>/ontologie/ontologie.md` par défaut.
- **Écraser une ontologie existante sans demander** : toujours passer par l'étape 1.
