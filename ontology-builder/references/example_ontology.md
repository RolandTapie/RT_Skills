# Ontologie — Contrats fournisseurs

Ontologie générée à partir de 6 documents sources (modèles de contrats, cahiers des charges, procédures internes d'achat).

## Vue d'ensemble

Cette ontologie modélise le cycle de vie d'un contrat fournisseur : les acteurs impliqués (fournisseurs, signataires) et les documents contractuels qui les lient (contrats, avenants). Elle couvre la contractualisation (qui signe quoi, avec qui) et l'exécution (qui livre dans le cadre de quel contrat, et quand).

Exemple compact à but illustratif — une ontologie réelle générée par ce skill couvre généralement davantage de groupes et de types, proportionnellement à la richesse du corpus source.

## Groupes d'entités

### Groupe : Acteurs
Personnes physiques ou morales impliquées dans un contrat.

- **Fournisseur**
  - Propriétés :
    - raisonSociale (string) — nom légal de l'entreprise fournisseuse
    - numeroTVA (string) — identifiant fiscal
    - noteFiabilite (enum) — évaluation interne du fournisseur (valeurs possibles : "fiable", "sous-surveillance", "à risque")
- **Signataire**
  - Propriétés :
    - nom (string) — nom de la personne
    - fonction (string) — poste occupé au moment de la signature
    - delegationSignature (boolean) — si la signature s'exerce par délégation

### Groupe : Documents contractuels
Pièces écrites qui encadrent juridiquement la relation avec le fournisseur.

- **Contrat**
  - Propriétés :
    - numeroContrat (string) — identifiant interne du contrat
    - dateSignature (date) — date d'entrée en vigueur
    - montantTotal (float) — montant total engagé en euros
    - statut (enum) — état du contrat (valeurs possibles : "en négociation", "actif", "résilié", "expiré")
- **Avenant**
  - Propriétés :
    - numeroAvenant (integer) — numéro d'ordre de l'avenant
    - dateEffet (date) — date de prise d'effet de la modification

## Groupes de relations

### Groupe : Contractualisation
Comment les acteurs et les documents contractuels se lient entre eux.

- **signe** : Signataire → Contrat
  - Propriétés :
    - dateSignatureEffective (date) — date réelle de signature (peut différer de dateSignature si signature différée)
- **estPartieAu** : Fournisseur → Contrat
  - Propriétés :
    - (aucune)
- **modifie** : Avenant → Contrat
  - Propriétés :
    - motifModification (string) — raison métier de l'avenant

### Groupe : Exécution
Comment un contrat se traduit en prestations livrées.

- **livrePar** : Fournisseur → Contrat
  - Propriétés :
    - dateLivraison (date) — date de livraison de la prestation concernée
    - conformite (boolean) — si la livraison a été jugée conforme au cahier des charges
