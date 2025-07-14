# scripts/sync_thales_orders.py
"""
Script pour synchroniser les commandes THALES depuis Google Sheet vers thales_orders.json
Repository: thales-xml-auto-corrector
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
THALES_GSHEET_ID = os.getenv('THALES_GSHEET_ID', '1MVbYGS1FKKDWdI0rctib07EuigtBSuKcbsReSA5jnyE')
WORKSHEET_NAME = 'Commandes_THALES'
THALES_ORDERS_JSON_PATH = 'thales_orders.json'

# Scopes Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def setup_google_sheets_client():
    """Configure le client Google Sheets avec service account"""
    try:
        # Récupérer les credentials depuis la variable d'environnement
        service_account_info = json.loads(os.getenv('SERVICE_ACCOUNT_JSON'))
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        
        print("✅ Client Google Sheets configuré avec succès")
        return service
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration Google Sheets: {e}")
        sys.exit(1)

def read_thales_sheet(service) -> pd.DataFrame:
    """Lit les données THALES depuis Google Sheet"""
    try:
        print(f"📊 Lecture du Google Sheet THALES: {THALES_GSHEET_ID}")
        
        # Lire toutes les données de l'onglet
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=THALES_GSHEET_ID,
            range=f"{WORKSHEET_NAME}!A:N"  # Colonnes A à N (14 colonnes)
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("⚠️ Aucune donnée trouvée dans le Google Sheet")
            return pd.DataFrame()
        
        # Créer DataFrame avec la première ligne comme headers
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # Nettoyer les lignes vides
        df = df.dropna(subset=['Numéro Commande'])
        
        print(f"✅ {len(df)} commandes THALES lues depuis Google Sheet")
        
        # Log des colonnes détectées
        print(f"📋 Colonnes détectées: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du Google Sheet: {e}")
        sys.exit(1)

def convert_thales_data_to_dict(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convertit les données THALES en format JSON"""
    try:
        commandes = []
        
        for index, row in df.iterrows():
            # Extraire les données avec gestion des valeurs manquantes
            commande = {
                "order_id": str(row.get('Numéro Commande', '')).strip(),
                "client": "THALES",
                "code_agence": str(row.get('Code Agence', '')).strip(),
                "emploi_cc": str(row.get('Emploi CC', '')).strip(),
                "categorie_socio": str(row.get('Catégorie Socio', '')).strip(),
                "classement_cc": str(row.get('Classement CC', '')).strip(),
                "centre_analyse": str(row.get('Centre Analyse', '')).strip(),
                "centre_analyse_prefix": extract_centre_analyse_prefix(str(row.get('Centre Analyse', ''))),
                "siret_client": str(row.get('SIRET Client', '')).strip(),
                "site_mission": str(row.get('Site Mission', '')).strip(),
                "date_debut": format_date(str(row.get('Date Début', ''))),
                "date_fin": format_date(str(row.get('Date Fin', ''))),
                "nom_fichier": str(row.get('Nom Fichier', '')).strip(),
                "timestamp_traitement": str(row.get('Timestamp', '')).strip(),
                "last_updated": datetime.now().isoformat()
            }
            
            # Déterminer si le site n'est pas GEMENOS (pour la règle conditionnelle)
            commande["site_not_gemenos"] = "GEMENOS" not in commande.get("site_mission", "").upper()
            
            # Nettoyer les valeurs vides
            commande = {k: v for k, v in commande.items() if v and str(v) != 'nan'}
            
            # Validation minimale
            if commande.get('order_id'):
                commandes.append(commande)
            else:
                print(f"⚠️ Ligne {index + 2} ignorée: pas de numéro de commande")
        
        print(f"✅ {len(commandes)} commandes THALES valides converties")
        return commandes
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion des données: {e}")
        return []

def extract_centre_analyse_prefix(centre_analyse: str) -> str:
    """Extrait le préfixe du centre d'analyse (ex: '1FRA' de '1FRA / PLADI/BP/PST04')"""
    try:
        if not centre_analyse or centre_analyse == 'nan':
            return ""
        
        # Premier token avant l'espace ou le slash
        parts = centre_analyse.split()
        if parts:
            prefix = parts[0].split('/')[0].strip()
            return prefix
        
        return ""
    except:
        return ""

def format_date(date_str: str) -> str:
    """Formate les dates en format ISO"""
    try:
        if not date_str or date_str == 'nan':
            return ""
        
        # Si c'est déjà un timestamp, le garder
        if 'T' in date_str:
            return date_str
        
        # Tenter de parser une date DD/MM/YYYY
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str
    except:
        return date_str

def get_thales_xml_rules() -> List[Dict[str, Any]]:
    """Définit les règles XML pour THALES basées sur le tableau XPath fourni"""
    return [
        {
            "name": "numero_commande",
            "description": "Numéro de commande dans OrderId/IdValue",
            "xpath": "//ReferenceInformation/OrderId/IdValue",
            "source_field": "order_id",
            "action": "create_or_update",
            "parent_xpath": "//ReferenceInformation/OrderId",
            "position": "before_siblings",
            "group": "ReferenceInformation"
        },
        {
            "name": "emploi_cc_position_code", 
            "description": "EMPLOI CC dans PositionStatus/Code",
            "xpath": "//PositionCharacteristics/PositionStatus/Code",
            "source_field": "emploi_cc",
            "action": "create_or_update",
            "parent_xpath": "//PositionCharacteristics/PositionStatus",
            "position": "first_child",
            "group": "PositionCharacteristics"
        },
        {
            "name": "categorie_socio_position_level",
            "description": "Catégorie socio-professionnelle dans PositionLevel",
            "xpath": "//PositionCharacteristics/PositionLevel", 
            "source_field": "categorie_socio",
            "action": "create_or_update",
            "parent_xpath": "//PositionCharacteristics",
            "position": "after_position_status",
            "group": "PositionCharacteristics"
        },
        {
            "name": "classement_cc_coefficient",
            "description": "Classement CC dans PositionCoefficient",
            "xpath": "//PositionCharacteristics/PositionCoefficient",
            "source_field": "classement_cc", 
            "action": "create_or_update",
            "parent_xpath": "//PositionCharacteristics",
            "position": "after_position_level",
            "group": "PositionCharacteristics"
        },
        {
            "name": "centre_analyse_cost_center_name",
            "description": "Centre d'analyse complet dans CostCenterName",
            "xpath": "//CustomerReportingRequirements/CostCenterName",
            "source_field": "centre_analyse",
            "action": "create_or_update", 
            "parent_xpath": "//CustomerReportingRequirements",
            "position": "after_cost_center_code",
            "group": "CustomerReportingRequirements"
        },
        {
            "name": "centre_analyse_department_code",
            "description": "Préfixe centre d'analyse dans DepartmentCode",
            "xpath": "//CustomerReportingRequirements/DepartmentCode",
            "source_field": "centre_analyse_prefix",
            "action": "create_or_update",
            "parent_xpath": "//CustomerReportingRequirements",
            "position": "beginning",
            "group": "CustomerReportingRequirements"
        },
        {
            "name": "centre_analyse_cost_center_code",
            "description": "Préfixe centre d'analyse dans CostCenterCode",
            "xpath": "//CustomerReportingRequirements/CostCenterCode",
            "source_field": "centre_analyse_prefix",
            "action": "create_or_update",
            "parent_xpath": "//CustomerReportingRequirements",
            "position": "after_department_code",
            "group": "CustomerReportingRequirements"
        },
        {
            "name": "worksite_conditional",
            "description": "Centre d'analyse dans WorkSiteName si site ≠ GEMENOS",
            "xpath": "//WorkSite/WorkSiteName",
            "source_field": "centre_analyse",
            "action": "create_or_update",
            "condition": "site_not_gemenos",
            "parent_xpath": "//WorkSite",
            "position": "after_environment_id",
            "group": "ContractInformation"
        }
    ]

def create_thales_orders_json(commandes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Crée la structure JSON pour THALES orders"""
    
    # Calculer des statistiques
    codes_agence = list(set([c.get("code_agence", "") for c in commandes if c.get("code_agence")]))
    emplois_cc = list(set([c.get("emploi_cc", "") for c in commandes if c.get("emploi_cc")]))
    categories_socio = list(set([c.get("categorie_socio", "") for c in commandes if c.get("categorie_socio")]))
    classements_cc = list(set([c.get("classement_cc", "") for c in commandes if c.get("classement_cc")]))
    
    return {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "version": "1.0.0",
            "client": "THALES",
            "source": "Google Sheet via Apps Script",
            "repository": "thales-xml-auto-corrector"
        },
        "commandes": commandes,
        "regles_xml": get_thales_xml_rules(),
        "statistiques": {
            "total_commandes": len(commandes),
            "derniere_mise_a_jour": datetime.now().isoformat(),
            "codes_agence_uniques": codes_agence,
            "emplois_cc_uniques": emplois_cc,
            "categories_socio_uniques": categories_socio,
            "classements_cc_uniques": classements_cc,
            "repartition_par_agence": {
                agence: len([c for c in commandes if c.get("code_agence") == agence])
                for agence in codes_agence
            }
        }
    }

def save_thales_orders_json(data: Dict[str, Any]) -> bool:
    """Sauvegarde le fichier thales_orders.json"""
    try:
        with open(THALES_ORDERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {THALES_ORDERS_JSON_PATH} mis à jour avec {len(data['commandes'])} commandes THALES")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 === SYNCHRONISATION COMMANDES THALES ===")
    
    try:
        # 1. Configuration Google Sheets
        service = setup_google_sheets_client()
        
        # 2. Lecture des données THALES
        df_thales = read_thales_sheet(service)
        
        if df_thales.empty:
            print("ℹ️ Aucune donnée THALES à synchroniser")
            return
        
        # 3. Conversion en format JSON
        thales_commandes = convert_thales_data_to_dict(df_thales)
        
        if not thales_commandes:
            print("⚠️ Aucune commande THALES valide trouvée")
            return
        
        # 4. Création de la structure JSON THALES
        thales_data = create_thales_orders_json(thales_commandes)
        
        # 5. Sauvegarde
        success = save_thales_orders_json(thales_data)
        
        if success:
            print(f"🎉 Synchronisation THALES terminée avec succès!")
            print(f"📊 {len(thales_commandes)} commandes synchronisées")
            
            # Afficher quelques statistiques
            stats = thales_data['statistiques']
            print(f"🏢 Codes agence: {', '.join(stats['codes_agence_uniques'][:5])}")
            print(f"💼 Emplois CC: {len(stats['emplois_cc_uniques'])} uniques")
            print(f"👥 Catégories socio: {', '.join(stats['categories_socio_uniques'])}")
        else:
            print("❌ Échec de la synchronisation THALES")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur critique dans la synchronisation THALES: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
