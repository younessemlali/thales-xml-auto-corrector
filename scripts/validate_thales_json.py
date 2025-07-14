# scripts/validate_thales_json.py
"""
Script de validation pour thales_orders.json
Vérifie la structure et l'intégrité des données THALES
Repository: thales-xml-auto-corrector
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, List

THALES_ORDERS_JSON_PATH = 'thales_orders.json'

def validate_json_structure(data: Dict[str, Any]) -> bool:
    """Valide la structure générale du JSON THALES"""
    try:
        required_sections = ['metadata', 'commandes', 'regles_xml', 'statistiques']
        
        for section in required_sections:
            if section not in data:
                print(f"❌ Section manquante: {section}")
                return False
        
        # Vérifier metadata
        metadata = data['metadata']
        required_meta_fields = ['last_updated', 'version', 'client', 'source']
        
        for field in required_meta_fields:
            if field not in metadata:
                print(f"❌ Champ metadata manquant: {field}")
                return False
        
        # Vérifier que c'est bien THALES
        if metadata.get('client') != 'THALES':
            print(f"❌ Client incorrect dans metadata: {metadata.get('client')}")
            return False
        
        print("✅ Structure JSON THALES valide")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation structure: {e}")
        return False

def validate_thales_commandes(commandes: List[Dict[str, Any]]) -> bool:
    """Valide les commandes THALES"""
    try:
        if not isinstance(commandes, list):
            print("❌ 'commandes' doit être une liste")
            return False
        
        if len(commandes) == 0:
            print("⚠️ Aucune commande THALES trouvée")
            return True
        
        # Champs requis pour THALES
        required_fields = ['order_id', 'client', 'emploi_cc', 'code_agence']
        invalid_orders = []
        
        for i, commande in enumerate(commandes):
            if not isinstance(commande, dict):
                invalid_orders.append(f"Index {i}: pas un dictionnaire")
                continue
                
            missing_fields = [field for field in required_fields if not commande.get(field)]
            if missing_fields:
                invalid_orders.append(f"Index {i} (order_id: {commande.get('order_id', 'N/A')}): champs manquants {missing_fields}")
            
            # Vérifier que c'est bien THALES
            if commande.get('client') != 'THALES':
                invalid_orders.append(f"Index {i}: client n'est pas THALES")
            
            # Validation format numéro de commande THALES (commence par FU)
            order_id = commande.get('order_id', '')
            if order_id and not order_id.startswith('FU'):
                print(f"⚠️ Numéro de commande inhabituel: {order_id} (ne commence pas par 'FU')")
        
        if invalid_orders:
            print("❌ Commandes THALES invalides:")
            for error in invalid_orders[:10]:  # Afficher max 10 erreurs
                print(f"   {error}")
            return False
        
        print(f"✅ {len(commandes)} commandes THALES valides")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation commandes: {e}")
        return False

def validate_thales_regles_xml(regles_xml: List[Dict[str, Any]]) -> bool:
    """Valide les règles XML THALES"""
    try:
        if not isinstance(regles_xml, list):
            print("❌ 'regles_xml' doit être une liste")
            return False
        
        if len(regles_xml) == 0:
            print("❌ Aucune règle XML définie pour THALES")
            return False
        
        # Champs requis pour les règles
        required_rule_fields = ['name', 'xpath', 'source_field', 'action', 'group']
        invalid_rules = []
        
        # Vérifier les règles spécifiques THALES
        expected_rules = [
            'numero_commande',
            'emploi_cc_position_code', 
            'categorie_socio_position_level',
            'classement_cc_coefficient',
            'centre_analyse_cost_center_name'
        ]
        
        rule_names = [rule.get('name') for rule in regles_xml]
        
        for expected_rule in expected_rules:
            if expected_rule not in rule_names:
                invalid_rules.append(f"Règle manquante: {expected_rule}")
        
        for i, regle in enumerate(regles_xml):
            if not isinstance(regle, dict):
                invalid_rules.append(f"Index {i}: pas un dictionnaire")
                continue
                
            missing_fields = [field for field in required_rule_fields if field not in regle]
            if missing_fields:
                invalid_rules.append(f"Règle '{regle.get('name', 'N/A')}': champs manquants {missing_fields}")
        
        if invalid_rules:
            print("❌ Règles XML THALES invalides:")
            for error in invalid_rules:
                print(f"   {error}")
            return False
        
        print(f"✅ {len(regles_xml)} règles XML THALES valides")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation règles XML: {e}")
        return False

def validate_thales_statistiques(stats: Dict[str, Any]) -> bool:
    """Valide les statistiques THALES"""
    try:
        required_stats = ['total_commandes', 'codes_agence_uniques', 'emplois_cc_uniques']
        
        for stat in required_stats:
            if stat not in stats:
                print(f"❌ Statistique manquante: {stat}")
                return False
        
        # Vérifications de cohérence
        total_commandes = stats.get('total_commandes', 0)
        if not isinstance(total_commandes, int) or total_commandes < 0:
            print(f"❌ total_commandes invalide: {total_commandes}")
            return False
        
        print(f"✅ Statistiques THALES valides (total: {total_commandes} commandes)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de validation statistiques: {e}")
        return False

def generate_validation_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un rapport de validation détaillé"""
    try:
        commandes = data.get('commandes', [])
        stats = data.get('statistiques', {})
        
        rapport = {
            "timestamp_validation": datetime.now().isoformat(),
            "fichier": THALES_ORDERS_JSON_PATH,
            "resume": {
                "total_commandes": len(commandes),
                "total_regles": len(data.get('regles_xml', [])),
                "codes_agence": len(stats.get('codes_agence_uniques', [])),
                "emplois_cc": len(stats.get('emplois_cc_uniques', [])),
                "categories_socio": len(stats.get('categories_socio_uniques', []))
            },
            "details": {
                "codes_agence_liste": stats.get('codes_agence_uniques', []),
                "emplois_cc_liste": stats.get('emplois_cc_uniques', [])[:10],  # Max 10
                "categories_socio_liste": stats.get('categories_socio_uniques', []),
                "repartition_agences": stats.get('repartition_par_agence', {})
            },
            "qualite_donnees": {
                "commandes_avec_emploi_cc": len([c for c in commandes if c.get('emploi_cc')]),
                "commandes_avec_centre_analyse": len([c for c in commandes if c.get('centre_analyse')]),
                "commandes_avec_dates": len([c for c in commandes if c.get('date_debut')])
            }
        }
        
        return rapport
        
    except Exception as e:
        print(f"⚠️ Erreur génération rapport: {e}")
        return {}

def main():
    """Fonction principale de validation"""
    print("🔍 === VALIDATION THALES_ORDERS.JSON ===")
    
    try:
        # Charger le fichier JSON
        with open(THALES_ORDERS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Fichier JSON chargé: {THALES_ORDERS_JSON_PATH}")
        
        # Validation structure générale
        if not validate_json_structure(data):
            print("❌ Validation structure échouée")
            sys.exit(1)
        
        # Validation commandes THALES  
        if not validate_thales_commandes(data.get('commandes', [])):
            print("❌ Validation commandes échouée")
            sys.exit(1)
        
        # Validation règles XML
        if not validate_thales_regles_xml(data.get('regles_xml', [])):
            print("❌ Validation règles XML échouée")
            sys.exit(1)
        
        # Validation statistiques
        if not validate_thales_statistiques(data.get('statistiques', {})):
            print("❌ Validation statistiques échouée")
            sys.exit(1)
        
        # Génération du rapport
        rapport = generate_validation_report(data)
        if rapport:
            print("\n📊 === RAPPORT DE VALIDATION ===")
            resume = rapport['resume']
            print(f"Total commandes: {resume['total_commandes']}")
            print(f"Total règles XML: {resume['total_regles']}")
            print(f"Codes agence uniques: {resume['codes_agence']}")
            print(f"Emplois CC uniques: {resume['emplois_cc']}")
            print(f"Catégories socio: {resume['categories_socio']}")
            
            qualite = rapport['qualite_donnees']
            print(f"\n📈 Qualité des données:")
            print(f"- Avec emploi CC: {qualite['commandes_avec_emploi_cc']}/{resume['total_commandes']}")
            print(f"- Avec centre analyse: {qualite['commandes_avec_centre_analyse']}/{resume['total_commandes']}")
            print(f"- Avec dates: {qualite['commandes_avec_dates']}/{resume['total_commandes']}")
            
            if rapport['details']['codes_agence_liste']:
                print(f"\n🏢 Codes agence: {', '.join(rapport['details']['codes_agence_liste'])}")
        
        print("\n🎉 === VALIDATION RÉUSSIE ===")
        print("thales_orders.json est valide et prêt pour Streamlit")
        
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {THALES_ORDERS_JSON_PATH}")
        print("Exécutez d'abord le script de synchronisation")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur de validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
