# 📋 Registre des Traitements de Données Personnelles

> **Application** : Coach IA Sportif (CertificationDEVIA)  
> **Responsable traitement** : Développeur IA (Simplon)  
> **Date création** : 02/08/2025  
> **Conformité** : RGPD (UE) 2016/679  
> **Révision** : Trimestrielle

---

## 🎯 **Vue d'ensemble des traitements**

### Synthèse des données personnelles traitées
- **Données d'identité** : Comptes utilisateurs (email, nom, prénom)
- **Données de santé** : Activités sportives Garmin (FC, GPS, performance)  
- **Données comportementales** : Sessions coaching IA, préférences
- **Données techniques** : Logs système, métriques performance

### Finalités principales
1. **Coaching sportif personnalisé** via intelligence artificielle
2. **Analyse performance** basée données physiologiques
3. **Amélioration service** par apprentissage IA
4. **Support technique** et résolution incidents

---

## 👤 **Traitement 1 : Gestion des comptes utilisateurs**

### Identification du traitement
- **Nom** : Système d'authentification et profils utilisateurs
- **Finalité** : Création compte, authentification, gestion profil sportif
- **Base légale** : Consentement (Art. 6.1.a RGPD)
- **Responsable** : Coach IA App
- **Sous-traitant** : Supabase (hébergement base données)

### Données personnelles traitées
- **Données obligatoires** :
  - Email (identifiant unique)
  - Mot de passe (hashé bcrypt)
  - Nom et prénom
- **Données optionnelles** :
  - Date de naissance (calcul zones FC)
  - Poids, taille (métriques performance)
  - Objectifs sportifs (personnalisation)

### Catégories de personnes concernées
- **Utilisateurs finaux** : Sportifs amateurs et confirmés
- **Âge minimum** : 16 ans (vérification à l'inscription)
- **Géolocalisation** : Union Européenne prioritairement

### Sources des données
- **Saisie directe** : Formulaire d'inscription (95%)
- **Import Garmin** : Synchronisation profil (optionnel)
- **Inférence IA** : Calcul automatique métriques (VMA, seuils)

### Destinataires des données
- **Internes** :
  - Module IA coaching (personnalisation)
  - Système d'authentification Django
  - Logs de sécurité (accès, tentatives)
- **Externes** :
  - Supabase PostgreSQL (stockage chiffré)
  - ⚠️ Aucun partage commercial ou publicitaire

### Durée de conservation
- **Compte actif** : Durée d'utilisation + 3 ans
- **Compte inactif** : Suppression automatique après 2 ans
- **Logs sécurité** : 1 an maximum
- **Données supprimées** : Suppression immédiate sur demande

### Mesures de sécurité
- **Chiffrement** : AES-256 base de données
- **Authentification** : JWT + refresh tokens
- **Accès** : Principe du moindre privilège
- **Audit** : Logs accès tracés et surveillés

---

## 🏃‍♂️ **Traitement 2 : Données d'activités sportives Garmin**

### Identification du traitement
- **Nom** : Synchronisation et analyse activités Garmin Connect
- **Finalité** : Coaching personnalisé basé historique sportif
- **Base légale** : Consentement explicite (Art. 6.1.a + Art. 9.2.a RGPD)
- **⚠️ Données de santé** : Fréquence cardiaque, effort, récupération

### Données personnelles traitées
- **Métriques physiologiques** :
  - Fréquence cardiaque (instantanée, moyenne, max)
  - Données GPS (parcours, altitude, vitesse)
  - Cadence de course, longueur de foulée
  - Temps de récupération estimé
- **Données d'activité** :
  - Type sport (course, vélo, natation)
  - Date, heure, durée session
  - Distance parcourue, dénivelé
  - Météo conditions (température, humidité)

### Catégories de personnes concernées
- **Sportifs volontaires** ayant donné consentement explicite
- **Utilisateurs Garmin** avec compte Connect actif
- **Résidents UE** principalement (serveurs EU)

### Sources des données
- **API Garmin Connect** : Authentification OAuth2
- **Montres connectées** : Garmin Forerunner, Fenix, Vivoactive
- **Applications tierces** : Strava sync (si autorisé)

### Finalités détaillées
1. **Analyse performance** : Progression, seuils, zones FC
2. **Plans d'entraînement** : Génération IA personnalisée
3. **Prévention blessures** : Détection surcharge
4. **Coaching contextuel** : Recommandations adaptées

### Durée de conservation
- **Données récentes** : 5 ans maximum (analyse tendances)
- **Données agrégées** : Anonymisation après 2 ans
- **Métadonnées GPS** : Pseudonymisation immédiate
- **Suppression** : Sur demande dans 30 jours max

### Mesures spécifiques données de santé
- **Chiffrement renforcé** : AES-256 + clés rotation 90j
- **Accès restreint** : Module IA uniquement, logs complets
- **Anonymisation** : Identifiants techniques, pas de noms
- **Audit médical** : Partenariat cardiologue pour validation

### Transferts internationaux
- **Supabase EU** : Serveurs Frankfurt (Allemagne)
- **OpenAI API** : ⚠️ Données pseudonymisées uniquement
- **Fallback SQLite** : Stockage local (aucun transfert)

---

## 🤖 **Traitement 3 : Sessions de coaching IA**

### Identification du traitement
- **Nom** : Conversations et recommandations agent IA
- **Finalité** : Coaching conversationnel personnalisé
- **Base légale** : Intérêt légitime (Art. 6.1.f RGPD)
- **IA concernée** : OpenAI GPT-4, Claude 3.5, LangChain RAG

### Données personnelles traitées
- **Messages utilisateur** : Questions, objectifs, ressenti
- **Réponses IA** : Plans entraînement, conseils, analyses
- **Métadonnées** : Timestamps, durée, satisfaction
- **Contexte** : Historique sportif pseudonymisé

### Catégories de personnes concernées
- **Utilisateurs actifs** ayant initié conversations
- **Consentement éclairé** : Information transparente sur IA
- **Droit opposition** : Arrêt coaching IA à tout moment

### Finalités spécifiques
1. **Génération plans** : Entraînement personnalisé
2. **Conseils performance** : Amélioration continue
3. **Motivation** : Encouragement et suivi psychologique
4. **Amélioration IA** : Apprentissage (données anonymisées)

### Durée de conservation
- **Sessions actives** : Durée conversation + contexte
- **Historique coaching** : 1 an (amélioration recommandations)
- **Données anonymisées** : 3 ans (amélioration modèles)
- **Logs techniques** : 6 mois (debug et performance)

### Mesures de sécurité IA
- **Pseudonymisation** : Aucun nom dans prompts OpenAI
- **Filtrage** : Suppression données sensibles avant API
- **Monitoring** : Détection hallucinations médicales dangereuses
- **Audit** : Révision échantillon conversations mensuelle

### Droits des personnes concernées
- **Accès** : Export JSON complet des conversations
- **Rectification** : Correction données profil source
- **Suppression** : Effacement conversations dans 48h
- **Opposition** : Arrêt coaching IA, conservation données sportives

---

## 📊 **Traitement 4 : Logs techniques et monitoring**

### Identification du traitement
- **Nom** : Journalisation système et métriques performance
- **Finalité** : Sécurité, debugging, optimisation technique
- **Base légale** : Intérêt légitime (Art. 6.1.f RGPD)
- **Durée** : Temporaire, finalité technique uniquement

### Données personnelles traitées
- **Identifiants techniques** : user_id, session_id (pseudonymes)
- **Adresses IP** : Géolocalisation approximative, sécurité
- **User-Agent** : Navigateur/app version (compatibilité)
- **Actions utilisateur** : Pages visitées, fonctions utilisées

### Finalités techniques
1. **Sécurité** : Détection intrusions, tentatives attaque
2. **Performance** : Optimisation temps réponse, cache
3. **Debugging** : Résolution bugs, amélioration UX
4. **Monitoring** : Alertes système, uptime

### Durée de conservation minimale
- **Logs applicatifs** : 30 jours maximum
- **Logs sécurité** : 90 jours (conformité)
- **Métriques performance** : Agrégation anonyme 1 an
- **IPs et identifiants** : Suppression automatique 7 jours

### Accès et sécurité
- **Accès restreint** : Administrateur système uniquement
- **Chiffrement** : Transport TLS 1.3, stockage AES-256
- **Pseudonymisation** : Hash irréversible user identifiers
- **Audit** : Logs d'accès aux logs (traçabilité complète)

---

## ⚖️ **Droits des personnes concernées**

### Information et transparence
- **Politique confidentialité** : Accessible, WCAG AA, langue claire
- **Consentement éclairé** : Cases non pré-cochées, granulaire
- **Information continue** : Notification changements par email

### Droits RGPD exercés
#### Droit d'accès (Art. 15)
- **Délai** : 30 jours maximum
- **Format** : JSON structuré + résumé humain
- **Contenu** : Toutes données + finalités + destinataires

#### Droit de rectification (Art. 16)
- **Interface** : Profil utilisateur modifiable
- **Propagation** : Mise à jour système IA automatique
- **Notification** : Confirmation modification par email

#### Droit à l'effacement (Art. 17)
- **Suppression complète** : Base données + backups + caches
- **Délai** : 48h pour données actives, 30j backups
- **Exceptions** : Données anonymisées recherche (Art. 89)

#### Droit à la portabilité (Art. 20)
- **Format** : JSON + CSV lisible machine
- **Contenu** : Profil + activités + conversations IA
- **Transfert direct** : API vers autres services (si technique)

#### Droit d'opposition (Art. 21)
- **Coaching IA** : Arrêt immédiat, conservation données
- **Marketing** : Opt-out complet (inexistant actuellement)
- **Intérêt légitime** : Évaluation cas par cas

### Procédures de recours
- **DPO Contact** : dev.ia.certification@simplon.co
- **Délai réponse** : 5 jours ouvrés (accusé réception)
- **Autorité contrôle** : CNIL (plainte.cnil.fr)
- **Recours judiciaire** : Tribunal de grande instance

---

## 🔒 **Mesures de sécurité transversales**

### Sécurité technique
- **Chiffrement** : AES-256 repos, TLS 1.3 transit
- **Authentification** : MFA administrateurs, JWT utilisateurs
- **Accès** : Principe moindre privilège, logs complets
- **Sauvegarde** : Chiffrement, géolocalisation EU, test restore

### Sécurité organisationnelle
- **Formation** : Sensibilisation RGPD équipe développement
- **Procédures** : Documentation incident, escalade DPO
- **Audits** : Contrôle sécurité trimestriel externe
- **Contracts** : Clauses RGPD sous-traitants (DPA)

### Violation de données
- **Détection** : Monitoring 24/7, alertes automatiques
- **Notification CNIL** : 72h maximum si risque avéré
- **Information personnes** : Si risque élevé, communication claire
- **Registre** : Documentation toutes violations (mineures incluses)

---

## 📋 **Sous-traitants et transferts**

### Sous-traitants RGPD
#### Supabase (PostgreSQL hébergement)
- **Localisation** : Frankfurt, Allemagne (UE)
- **Certification** : SOC 2, ISO 27001
- **DPA** : Data Processing Agreement signé
- **Garanties** : Chiffrement, accès restreint, audits

#### OpenAI (API IA)
- **Localisation** : États-Unis (transfert international)
- **Mécanisme** : Clauses contractuelles types UE
- **Données** : Pseudonymisées uniquement
- **Contrôle** : Monitoring requêtes, filtrage sensible

### Transferts internationaux sécurisés
- **Évaluation** : Analyse risques pays tiers (États-Unis)
- **Garanties** : Pseudonymisation, chiffrement, audit
- **Alternative** : Modèles européens (Mistral AI) évalués
- **Monitoring** : Surveillance utilisation, conformité

---

## 📅 **Procédures de tri et suppression**

### Automatisation des suppressions
- **Trigger base données** : Suppression CASCADE modélisée
- **Scripts CRON** : Nettoyage hebdomadaire données expirées
- **Monitoring** : Métriques volume supprimé, erreurs
- **Audit** : Vérification mensuelle effectiveness

### Fréquences de tri
- **Quotidien** : Logs temporaires, sessions expirées
- **Hebdomadaire** : Comptes inactifs >30j, caches obsolètes
- **Mensuel** : Données anonymisées, archives
- **Annuel** : Révision durées conservation, audit complet

### Procédures manuelles
- **Demandes suppression** : Interface utilisateur + validation
- **Cas complexes** : Évaluation DPO, traçabilité décision
- **Vérification** : Contrôle effectivité suppression 72h
- **Documentation** : Registre suppressions horodaté

---

## 📊 **Indicateurs de conformité**

### Métriques RGPD
- **Demandes d'accès** : Délai moyen traitement <30j
- **Suppressions** : 100% effectives dans délais
- **Violations** : 0 notification CNIL (objectif)
- **Formation** : 100% équipe sensibilisée annuellement

### Audits et contrôles
- **Auto-évaluation** : Checklist RGPD trimestrielle
- **Audit externe** : Contrôle annuel cabinet spécialisé
- **Tests violation** : Simulation incident semestrielle
- **Certification** : ISO 27001 visée 2026

---

## 📞 **Contacts et responsabilités**

### Responsable de traitement
- **Nom** : Développeur IA Certification Simplon
- **Email** : dev.ia.certification@simplon.co
- **Téléphone** : +33 X XX XX XX XX
- **Adresse** : Formation Simplon, [Adresse complète]

### Délégué à la Protection des Données (DPO)
- **Nom** : [À désigner si >250 employés ou données sensibles]
- **Email** : dpo@simplon.co
- **Mission** : Conseil, contrôle, point de contact CNIL

### Contact technique
- **Administrateur système** : admin.tech@projet-coach-ia.fr
- **Urgences sécurité** : security@projet-coach-ia.fr (24/7)

---

> **Dernière mise à jour** : 02/08/2025  
> **Prochaine révision** : 02/11/2025 (trimestrielle)  
> **Version** : 1.0 - Conforme RGPD UE 2016/679