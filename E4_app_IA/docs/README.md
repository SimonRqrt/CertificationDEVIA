# Documentation E4 - Développer une Application IA Coach

## 📁 Structure de la documentation

```
E4_app_IA/docs/
├── README.md                           # Ce fichier - index général
│
├── 📋 DOCUMENTATION PUBLIQUE (versionnée)
├── architecture_technique.md          # C15 - Architecture microservices
├── diagramme_flux_donnees.md          # C15 - Flux de données détaillés  
├── diagramme_sequence_poc.md          # C15 - Séquences POC validation
├── flowchart_pilotage_monitoring.md   # C16 - Processus Agile et monitoring
├── documentation_accessible.html      # C17 - Doc technique WCAG 2.1 AA
│
├── 🔒 DOCUMENTATION INTERNE (gitignore)
├── wireframes_mermaid.md              # C14 - Maquettes et wireframes
├── specifications_fonctionnelles_c14.md # C14 - Specs fonctionnelles
├── user_stories_wcag_c14.md           # C14 - User stories accessibilité
├── checklist_wcag_conformite.md       # C17 - Validation accessibilité
├── audit_eco_conception.md            # C17 - Audit Green IT
│
└── 📊 FICHIERS DE TRAVAIL (gitignore)
    ├── backlog_agile.csv              # C16 - Backlog Kanban
    └── *.csv                          # Exports et données temporaires
```

## 🎯 Correspondance grille d'évaluation

| Critère | Document | Statut |
|---------|----------|--------|
| **C14** - Analyser le besoin d'application |
| C14.1 - Modélisation données Merise | ↗️ `../E1_gestion_donnees/docs/modelisation_merise.md` | ✅ Complet |
| C14.2 - Parcours utilisateurs/wireframes | `wireframes_mermaid.md` | ✅ Complet |
| C14.3 - Spécifications fonctionnelles | `specifications_fonctionnelles_c14.md` | ✅ Complet |
| C14.4-5 - User stories + WCAG | `user_stories_wcag_c14.md` | ✅ Complet |
| **C15** - Concevoir le cadre technique |
| C15.1 - Spécifications techniques | `architecture_technique.md` | ✅ Complet |
| C15.2 - Diagramme flux données | `diagramme_flux_donnees.md` | ✅ Complet |
| C15.3 - POC et séquences | `diagramme_sequence_poc.md` | ✅ Complet |
| **C16** - Coordonner méthode Agile |
| C16.1-4 - Processus et pilotage | `flowchart_pilotage_monitoring.md` | ✅ Complet |
| C16.5 - Backlog et Kanban | `backlog_agile.csv` | ✅ Complet |
| **C17** - Développer composants techniques |
| C17.8 - Éco-conception | `audit_eco_conception.md` | ✅ Complet |
| C17.12 - Documentation accessible | `documentation_accessible.html` | ✅ Complet |
| C17.12 - Conformité WCAG | `checklist_wcag_conformite.md` | ✅ Complet |

## 📋 Organisation Documentation vs Git

### 📋 Documentation Publique (versionnée)
Ces fichiers constituent la documentation technique officielle du projet :
- **Architecture technique** : Schemas microservices, technologies, contraintes
- **Diagrammes techniques** : Flux de données, séquences POC, monitoring
- **Documentation accessible** : Version WCAG 2.1 AA pour toutes les parties prenantes

### 🔒 Documentation Interne (gitignore)
Ces fichiers contiennent les détails de conception et validation internes :
- **Wireframes et maquettes** : Conception interfaces utilisateur
- **Spécifications détaillées** : Analyse fonctionnelle approfondie  
- **Audits et checklists** : Validations qualité et conformité
- **User stories** : Détails métier et critères d'acceptation

### 📊 Fichiers de Travail (gitignore)
Les exports CSV, backlogs et données temporaires ne sont pas versionnés pour éviter le bruit dans l'historique Git.

## 🎯 Avantages de cette Organisation

1. **Séparation claire** : Public vs interne, technique vs métier
2. **Historique Git propre** : Seuls les fichiers essentiels sont versionnés
3. **Accessibilité** : Documentation technique conforme WCAG 2.1 AA
4. **Maintenance** : Structure cohérente avec la grille d'évaluation E4

## 📚 Guide d'Utilisation

- **Développeurs** : Consultez les diagrammes techniques publics
- **Product Owners** : Référez-vous aux spécifications internes
- **Auditeurs** : Documentation accessible HTML + checklists conformité
- **Équipe Agile** : Backlog CSV et flowcharts de pilotage

---

*Documentation E4 complète - Certification Développeur IA* | *WCAG 2.1 AA Conforme*