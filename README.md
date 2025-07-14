# ⚙️ THALES XML Auto-Corrector

Système automatisé de correction de fichiers XML pour les commandes **THALES**, basé sur l'extraction automatique des données depuis les emails PIXID.

## 🏗️ Architecture

```
📧 Emails HTML    📤 Apps Script    📊 Google Sheet    🤖 GitHub Actions    📄 JSON              ⚙️ Streamlit
(Google Drive) → (extraction)   → (données THALES) → (sync 15min)      → (thales_orders.json) → (correction XML)
```

## 📋 Fonctionnalités

- ✅ **Extraction automatique** : Emails THALES → Google Sheet (Apps Script)
- ✅ **Synchronisation** : Google Sheet → JSON (GitHub Actions, toutes les 15min)
- ✅ **Correction XML** : Application automatique des règles THALES (Streamlit)
- ✅ **Interface web** : Upload, correction et téléchargement de fichiers XML
- ✅ **Monitoring** : Logs détaillés et validation automatique

## 🔧 Règles de Correction XML

| Donnée Email | Balise XML Cible | XPath | Action |
|--------------|------------------|-------|--------|
| **Numéro commande** (`FU70001236`) | `<OrderId><IdValue>` | `//ReferenceInformation/OrderId/IdValue` | Créer/Corriger |
| **Emploi CC** (`10A3071`) | `<PositionStatus><Code>` | `//PositionCharacteristics/PositionStatus/Code` | Créer/Corriger |
| **Catégorie socio** (`OUVRIER`) | `<PositionLevel>` | `//PositionCharacteristics/PositionLevel` | Créer/Corriger |
| **Classement CC** (`B3`) | `<PositionCoefficient>` | `//PositionCharacteristics/PositionCoefficient` | Créer/Corriger |
| **Centre analyse** (`1FRA / PLADI/BP/PST04`) | `<CostCenterName>` | `//CustomerReportingRequirements/CostCenterName` | Créer/Corriger |
| **Préfixe centre** (`1FRA`) | `<DepartmentCode>`, `<CostCenterCode>` | `//CustomerReportingRequirements/...` | Créer/Corriger |
| **WorkSite conditionnel** | `<WorkSiteName>` | `//WorkSite/WorkSiteName` | Si site ≠ GEMENOS |

## 📂 Structure du Repository

```
thales-xml-auto-corrector/
├── .github/workflows/
│   └── sync_thales_orders.yml      # Workflow GitHub Actions (15min)
├── scripts/
│   ├── sync_thales_orders.py       # Synchronisation Google Sheet → JSON
│   └── validate_thales_json.py     # Validation structure JSON
├── streamlit_app/
│   └── app.py                      # Application Streamlit
├── config/
│   └── thales_xml_rules.json       # Configuration règles XML
├── thales_orders.json              # Données THALES (auto-généré)
├── requirements.txt                # Dépendances Python
└── README.md                       # Documentation
```

## 🚀 Installation et Déploiement

### 1️⃣ Prérequis

- **Google Apps Script** : Script d'extraction emails déployé
- **Google Sheet** : Alimenté automatiquement par Apps Script
- **Repository GitHub** : `thales-xml-auto-corrector`
- **Service Account Google** : Accès Google Sheets API

### 2️⃣ Configuration Secrets GitHub

Dans **Settings** → **Secrets and variables** → **Actions** :

```
PERSONAL_ACCESS_TOKEN    # Token GitHub avec permissions repo
THALES_GSHEET_ID         # 1MVbYGS1FKKDWdI0rctib07EuigtBSuKcbsReSA5jnyE
SERVICE_ACCOUNT_JSON     # Credentials Google Service Account
```

**Exemple SERVICE_ACCOUNT_JSON :**
```json
{
  "type": "service_account",
  "project_id": "votre-projet-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "service-account@votre-projet.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

### 3️⃣ Déploiement des fichiers

1. **Créer le repository** `thales-xml-auto-corrector`
2. **Copier tous les fichiers** dans la structure ci-dessus
3. **Configurer les secrets** GitHub
4. **Donner accès** à la Service Account sur le Google Sheet THALES

### 4️⃣ Test et validation

```bash
# Test manuel du workflow
GitHub → Actions → "Sync THALES Orders" → "Run workflow"

# Vérifier la génération du JSON
cat thales_orders.json

# Lancer l'application Streamlit
streamlit run streamlit_app/app.py
```

## 📊 Structure des Données

### Google Sheet THALES (source)

| Timestamp | Code Agence | Numéro Commande | Emploi CC | Catégorie Socio | Classement CC | Centre Analyse | ... |
|-----------|-------------|-----------------|-----------|-----------------|---------------|----------------|-----|
| 2025-07-14 15:38 | GR1 | FU70001236 | 10A3071 | OUVRIER | B3 | 1FRA / PLADI/BP/PST04 | ... |

### thales_orders.json (généré)

```json
{
  "metadata": {
    "last_updated": "2025-07-14T17:26:48.725Z",
    "version": "1.0.0",
    "client": "THALES"
  },
  "commandes": [
    {
      "order_id": "FU70001236",
      "client": "THALES",
      "code_agence": "GR1",
      "emploi_cc": "10A3071",
      "categorie_socio": "OUVRIER",
      "classement_cc": "B3",
      "centre_analyse": "1FRA / PLADI/BP/PST04",
      "centre_analyse_prefix": "1FRA",
      "siret_client": "84468774900052",
      "site_not_gemenos": true,
      "last_updated": "2025-07-14T17:26:48.725Z"
    }
  ],
  "regles_xml": [...],
  "statistiques": {
    "total_commandes": 1,
    "codes_agence_uniques": ["GR1"],
    "emplois_cc_uniques": ["10A3071"]
  }
}
```

## 🖥️ Utilisation Streamlit

### Interface Web

1. **Accès** : `streamlit run streamlit_app/app.py`
2. **Upload** : Sélectionner fichiers XML THALES
3. **Détection automatique** : Numéros de commande extraits
4. **Correction** : Règles XML appliquées automatiquement
5. **Téléchargement** : Fichiers XML corrigés

### Fonctionnalités

- ✅ **Upload multiple** : Traitement de plusieurs fichiers simultanément
- ✅ **Détection intelligente** : Reconnaissance automatique des commandes THALES
- ✅ **Filtrage par agence** : Traitement sélectif selon l'agence
- ✅ **Validation en temps réel** : Vérification des données avant correction
- ✅ **Téléchargement ZIP** : Archive pour les traitements multiples
- ✅ **Logs détaillés** : Suivi des règles appliquées

## 🔄 Workflow Automatique

### GitHub Actions (toutes les 15 minutes)

1. **Connexion** au Google Sheet THALES
2. **Lecture** des nouvelles données
3. **Conversion** en format JSON
4. **Validation** de la structure
5. **Commit** automatique si changements
6. **Notification** en cas d'erreur

### Monitoring

- **Logs GitHub Actions** : Détail de chaque synchronisation
- **Validation automatique** : Vérification structure JSON
- **Statistiques** : Nombre de commandes, agences, etc.
- **Alertes** : Notification des échecs de synchronisation

## 🔧 Configuration Avancée

### Règles XML personnalisées

Modifier `config/thales_xml_rules.json` pour ajuster :
- XPath des éléments XML
- Champs sources des données
- Conditions d'application
- Priorités des règles

### Paramètres de synchronisation

Dans `scripts/sync_thales_orders.py` :
```python
THALES_GSHEET_ID = "1MVbYGS1FKKDWdI0rctib07EuigtBSuKcbsReSA5jnyE"
WORKSHEET_NAME = "Commandes_THALES"
```

### Fréquence GitHub Actions

Dans `.github/workflows/sync_thales_orders.yml` :
```yaml
schedule:
  - cron: '*/15 * * * *'  # Toutes les 15 minutes
```

## 🐛 Dépannage

### Erreurs courantes

**1. Fichier thales_orders.json non trouvé**
```bash
# Solution: Exécuter manuellement la synchronisation
python scripts/sync_thales_orders.py
```

**2. Erreur permissions Google Sheet**
```bash
# Solution: Ajouter la service account comme lecteur du sheet
# Email: service-account@votre-projet.iam.gserviceaccount.com
```

**3. Workflow GitHub Actions échoue**
```bash
# Vérifier les secrets GitHub
# Vérifier les permissions du token GitHub
# Consulter les logs dans Actions
```

### Logs et diagnostics

```bash
# Validation manuelle du JSON
python scripts/validate_thales_json.py

# Test de l'application Streamlit
streamlit run streamlit_app/app.py --server.headless true

# Vérification des dépendances
pip install -r requirements.txt
```

## 📈 Métriques et Performance

### Capacités

- **Volume** : Traitement de centaines de commandes simultanément
- **Vitesse** : Correction XML en quelques secondes
- **Disponibilité** : Synchronisation automatique 24/7
- **Fiabilité** : Validation et logs complets

### Optimisations

- **Cache Streamlit** : Réduction des temps de chargement
- **Traitement par batch** : Efficacité pour gros volumes
- **Validation progressive** : Détection précoce des erreurs
- **Compression ZIP** : Téléchargement optimisé

## 🤝 Contribution

### Structure des commits

```
🔄 feat: nouvelle règle XML pour THALES
🐛 fix: correction extraction numéro commande  
📊 docs: mise à jour README
🔧 config: ajustement fréquence sync
```

### Tests

```bash
# Tests unitaires
pytest scripts/

# Validation JSON
python scripts/validate_thales_json.py

# Test Streamlit
streamlit run streamlit_app/app.py
```

## 📞 Support

### Contacts

- **Issues GitHub** : Signalement de bugs
- **Discussions** : Questions et améliorations
- **Email** : pixid.administrateur@randstad.fr

### Documentation

- **Google Apps Script** : Documentation du script d'extraction
- **GitHub Actions** : Workflow de synchronisation
- **Streamlit** : Guide utilisateur de l'interface

---

## 📝 Changelog

### v1.0.0 (2025-07-14)
- ✅ Création du repository THALES
- ✅ Synchronisation Google Sheet → JSON
- ✅ Application Streamlit complète
- ✅ Règles XML basées sur tableau XPath
- ✅ Workflow GitHub Actions automatique

---

## 🔗 Tokens de Liaison

**Éléments qui relient tous les fichiers :**
- **THALES_GSHEET_ID** : `1MVbYGS1FKKDWdI0rctib07EuigtBSuKcbsReSA5jnyE`
- **Worksheet** : `Commandes_THALES`
- **Fichier JSON** : `thales_orders.json`
- **Colonnes** : Timestamp, Code Agence, Numéro Commande, Emploi CC, Catégorie Socio, Classement CC, Centre Analyse...

**🎉 Repository THALES XML Auto-Corrector prêt pour la production !**
