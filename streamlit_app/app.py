# streamlit_app/app.py
"""
THALES XML Auto-Corrector - Version avec lecture JSON
Lit automatiquement thales_orders.json généré par le système GitHub Actions + Google Apps Script
Repository: thales-xml-auto-corrector
"""

import streamlit as st
import json
import re
import zipfile
import io
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from lxml import etree
import pandas as pd

# Configuration
st.set_page_config(
    page_title="THALES XML Auto-Corrector",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chemin vers le fichier JSON généré par GitHub Actions
THALES_ORDERS_JSON_PATH = 'thales_orders.json'

class ThalesDataManager:
    """Gestionnaire des données THALES depuis le JSON généré par GitHub Actions"""
    
    def __init__(self):
        self.thales_data = None
        self.last_loaded = None
        
    def load_thales_data(self) -> bool:
        """Charge les données THALES depuis le JSON"""
        try:
            if not os.path.exists(THALES_ORDERS_JSON_PATH):
                st.error(f"❌ Fichier {THALES_ORDERS_JSON_PATH} non trouvé")
                st.info("🔄 Le fichier est généré automatiquement par GitHub Actions toutes les 15 minutes depuis votre Google Sheet")
                return False
            
            with open(THALES_ORDERS_JSON_PATH, 'r', encoding='utf-8') as f:
                self.thales_data = json.load(f)
            
            self.last_loaded = datetime.now()
            return True
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des données THALES: {e}")
            return False
    
    def get_commandes(self) -> List[Dict[str, Any]]:
        """Retourne la liste des commandes THALES"""
        if not self.thales_data:
            return []
        return self.thales_data.get('commandes', [])
    
    def get_commande_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Trouve une commande par son numéro"""
        for commande in self.get_commandes():
            if commande.get('order_id') == order_id:
                return commande
        return None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Retourne les métadonnées du fichier JSON"""
        if not self.thales_data:
            return {}
        return self.thales_data.get('metadata', {})
    
    def get_statistiques(self) -> Dict[str, Any]:
        """Retourne les statistiques des données"""
        if not self.thales_data:
            return {}
        return self.thales_data.get('statistiques', {})

class ThalesXMLCorrector:
    """Correcteur XML THALES basé sur les règles XPath"""
    
    def __init__(self, thales_data_manager: ThalesDataManager):
        self.data_manager = thales_data_manager
        self.xml_rules = self._get_thales_xml_rules()
    
    def detect_order_ids_in_xml(self, xml_content: str) -> List[str]:
        """Détecte les numéros de commande THALES dans un fichier XML"""
        found_orders = []
        commandes = self.data_manager.get_commandes()
        
        for commande in commandes:
            order_id = commande.get('order_id', '')
            if order_id and order_id in xml_content:
                found_orders.append(order_id)
        
        return found_orders
    
    def correct_xml_file(self, xml_content: str, order_id: str) -> tuple[str, List[str]]:
        """Applique les corrections XML selon les règles THALES"""
        try:
            # Récupérer les données de la commande
            commande_data = self.data_manager.get_commande_by_id(order_id)
            if not commande_data:
                return xml_content, []
            
            # Parser le XML
            parser = etree.XMLParser(strip_cdata=False)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)
            
            corrections_applied = []
            
            # Appliquer chaque règle
            for rule in self.xml_rules:
                if self._should_apply_rule(rule, commande_data):
                    success = self._apply_xml_rule(root, rule, commande_data)
                    if success:
                        corrections_applied.append(rule['name'])
            
            # Retourner le XML corrigé
            corrected_xml = etree.tostring(root, encoding='unicode', pretty_print=True)
            
            return corrected_xml, corrections_applied
            
        except Exception as e:
            st.error(f"Erreur lors de la correction XML: {e}")
            return xml_content, []
    
    def _should_apply_rule(self, rule: Dict[str, Any], commande_data: Dict[str, Any]) -> bool:
        """Détermine si une règle doit être appliquée"""
        # Vérifier les conditions
        if 'condition' in rule:
            condition = rule['condition']
            if condition == 'site_not_gemenos':
                return commande_data.get('site_not_gemenos', False)
        
        # Vérifier que le champ source existe
        source_field = rule['source_field']
        return bool(commande_data.get(source_field))
    
    def _apply_xml_rule(self, root: etree.Element, rule: Dict[str, Any], commande_data: Dict[str, Any]) -> bool:
        """Applique une règle XML spécifique"""
        try:
            xpath = rule['xpath']
            source_field = rule['source_field']
            
            value = commande_data.get(source_field)
            if not value:
                return False
            
            # Chercher l'élément existant
            elements = root.xpath(xpath)
            
            if elements:
                # Mettre à jour l'élément existant
                elements[0].text = str(value)
            else:
                # Créer l'élément
                self._create_xml_element(root, rule, value)
            
            return True
            
        except Exception as e:
            st.warning(f"Erreur lors de l'application de la règle {rule['name']}: {e}")
            return False
    
    def _create_xml_element(self, root: etree.Element, rule: Dict[str, Any], value: str):
        """Crée un nouvel élément XML"""
        try:
            xpath = rule['xpath']
            parent_xpath = rule.get('parent_xpath')
            
            if not parent_xpath:
                return
            
            # Trouver le parent
            parents = root.xpath(parent_xpath)
            if not parents:
                return
            
            parent = parents[0]
            
            # Extraire le nom de l'élément depuis xpath
            element_name = xpath.split('/')[-1]
            
            # Créer l'élément
            new_element = etree.Element(element_name)
            new_element.text = str(value)
            
            # Ajouter au parent
            parent.append(new_element)
            
        except Exception as e:
            st.warning(f"Erreur lors de la création de l'élément: {e}")
    
    def _get_thales_xml_rules(self) -> List[Dict[str, Any]]:
        """Récupère les règles XML depuis les données THALES ou utilise les règles par défaut"""
        if self.data_manager.thales_data and 'regles_xml' in self.data_manager.thales_data:
            return self.data_manager.thales_data['regles_xml']
        
        # Règles par défaut si pas dans le JSON
        return [
            {
                "name": "numero_commande",
                "xpath": "//ReferenceInformation/OrderId/IdValue",
                "source_field": "order_id",
                "action": "create_or_update",
                "parent_xpath": "//ReferenceInformation/OrderId"
            },
            {
                "name": "emploi_cc_position_code",
                "xpath": "//PositionCharacteristics/PositionStatus/Code",
                "source_field": "emploi_cc",
                "action": "create_or_update",
                "parent_xpath": "//PositionCharacteristics/PositionStatus"
            },
            {
                "name": "categorie_socio_position_level",
                "xpath": "//PositionCharacteristics/PositionLevel",
                "source_field": "categorie_socio",
                "action": "create_or_update",
                "parent_xpath": "//PositionCharacteristics"
            },
            {
                "name": "classement_cc_coefficient",
                "xpath": "//PositionCharacteristics/PositionCoefficient",
                "source_field": "classement_cc",
                "action": "create_or_update",
                "parent_xpath": "//PositionCharacteristics"
            },
            {
                "name": "centre_analyse_cost_center_name",
                "xpath": "//CustomerReportingRequirements/CostCenterName",
                "source_field": "centre_analyse",
                "action": "create_or_update",
                "parent_xpath": "//CustomerReportingRequirements"
            },
            {
                "name": "centre_analyse_department_code",
                "xpath": "//CustomerReportingRequirements/DepartmentCode",
                "source_field": "centre_analyse_prefix",
                "action": "create_or_update",
                "parent_xpath": "//CustomerReportingRequirements"
            },
            {
                "name": "centre_analyse_cost_center_code",
                "xpath": "//CustomerReportingRequirements/CostCenterCode",
                "source_field": "centre_analyse_prefix",
                "action": "create_or_update",
                "parent_xpath": "//CustomerReportingRequirements"
            },
            {
                "name": "worksite_conditional",
                "xpath": "//WorkSite/WorkSiteName",
                "source_field": "centre_analyse",
                "action": "create_or_update",
                "condition": "site_not_gemenos",
                "parent_xpath": "//WorkSite"
            }
        ]

def display_thales_data_status(data_manager: ThalesDataManager):
    """Affiche le statut des données THALES"""
    metadata = data_manager.get_metadata()
    stats = data_manager.get_statistiques()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_commandes = stats.get('total_commandes', 0)
        st.metric("📋 Commandes THALES", total_commandes)
    
    with col2:
        codes_agence = len(stats.get('codes_agence_uniques', []))
        st.metric("🏢 Agences", codes_agence)
    
    with col3:
        emplois_cc = len(stats.get('emplois_cc_uniques', []))
        st.metric("💼 Emplois CC", emplois_cc)
    
    with col4:
        last_updated = metadata.get('last_updated', 'Inconnu')
        if last_updated != 'Inconnu':
            try:
                dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                last_updated = dt.strftime('%H:%M')
            except:
                pass
        st.metric("🔄 Dernière MAJ", last_updated)

def main():
    """Interface principale Streamlit"""
    
    # Titre et description
    st.title("⚙️ THALES XML Auto-Corrector")
    st.markdown("**Correction automatique basée sur Google Sheet THALES**")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Système THALES")
        st.markdown("""
        **🔄 Flux automatisé :**
        1. 📧 Emails → Google Apps Script
        2. 📊 Google Sheet → GitHub Actions  
        3. 📄 JSON → Streamlit
        4. ⚙️ Correction XML automatique
        """)
        
        if st.button("🔄 Recharger les données"):
            st.rerun()
    
    # Initialiser le gestionnaire de données
    data_manager = ThalesDataManager()
    
    # Charger les données THALES
    if not data_manager.load_thales_data():
        st.error("❌ Impossible de charger les données THALES")
        st.info("Vérifiez que le workflow GitHub Actions fonctionne correctement")
        return
    
    # Afficher le statut des données
    st.header("📊 Données THALES Disponibles")
    display_thales_data_status(data_manager)
    
    # Afficher un échantillon des commandes
    with st.expander("📋 Échantillon des commandes THALES", expanded=False):
        commandes = data_manager.get_commandes()
        if commandes:
            # Afficher les 10 premières commandes
            df_sample = pd.DataFrame(commandes[:10])
            if not df_sample.empty:
                # Sélectionner les colonnes importantes
                columns_to_show = ['order_id', 'code_agence', 'emploi_cc', 'categorie_socio', 'classement_cc']
                available_columns = [col for col in columns_to_show if col in df_sample.columns]
                if available_columns:
                    st.dataframe(df_sample[available_columns], use_container_width=True)
                else:
                    st.dataframe(df_sample, use_container_width=True)
        else:
            st.info("Aucune commande disponible")
    
    # Upload des fichiers XML
    st.header("⚙️ Correction des Fichiers XML")
    
    uploaded_xmls = st.file_uploader(
        "Sélectionnez vos fichiers XML THALES à corriger",
        type=['xml'],
        accept_multiple_files=True,
        help="Les numéros de commande seront détectés automatiquement"
    )
    
    if uploaded_xmls:
        st.success(f"📁 {len(uploaded_xmls)} fichiers XML uploadés")
        
        # Initialiser le correcteur
        xml_corrector = ThalesXMLCorrector(data_manager)
        
        # Analyser les fichiers pour détecter les numéros de commande
        detection_results = []
        
        for xml_file in uploaded_xmls:
            try:
                xml_content = xml_file.read().decode('utf-8')
                detected_orders = xml_corrector.detect_order_ids_in_xml(xml_content)
                
                detection_results.append({
                    'fichier': xml_file.name,
                    'taille': len(xml_content),
                    'commandes_detectees': detected_orders,
                    'status': 'Commande détectée' if detected_orders else 'Aucune commande THALES détectée'
                })
                
            except Exception as e:
                detection_results.append({
                    'fichier': xml_file.name,
                    'taille': 0,
                    'commandes_detectees': [],
                    'status': f'Erreur: {e}'
                })
        
        # Afficher les résultats de détection
        st.subheader("🔍 Détection des Numéros de Commande")
        
        df_detection = pd.DataFrame([
            {
                'Fichier XML': result['fichier'],
                'Commandes THALES': ', '.join(result['commandes_detectees']) if result['commandes_detectees'] else 'Aucune',
                'Statut': result['status']
            }
            for result in detection_results
        ])
        
        st.dataframe(df_detection, use_container_width=True)
        
        # Bouton de correction
        files_with_orders = [r for r in detection_results if r['commandes_detectees']]
        
        if files_with_orders:
            st.success(f"✅ {len(files_with_orders)} fichiers avec commandes THALES détectées")
            
            if st.button("🚀 Appliquer les Corrections THALES", type="primary"):
                corrected_files = []
                correction_summary = []
                
                # Re-lire les fichiers pour correction
                for i, xml_file in enumerate(uploaded_xmls):
                    detection_result = detection_results[i]
                    
                    if not detection_result['commandes_detectees']:
                        continue
                    
                    try:
                        xml_file.seek(0)  # Remettre le curseur au début
                        xml_content = xml_file.read().decode('utf-8')
                        
                        # Prendre la première commande détectée
                        order_id = detection_result['commandes_detectees'][0]
                        
                        # Appliquer les corrections
                        corrected_xml, applied_rules = xml_corrector.correct_xml_file(xml_content, order_id)
                        
                        corrected_files.append({
                            'name': xml_file.name,
                            'content': corrected_xml,
                            'original_size': len(xml_content),
                            'corrected_size': len(corrected_xml)
                        })
                        
                        correction_summary.append({
                            'fichier': xml_file.name,
                            'commande': order_id,
                            'regles_appliquees': len(applied_rules),
                            'details': applied_rules
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Erreur avec {xml_file.name}: {e}")
                
                # Afficher le résumé des corrections
                if correction_summary:
                    st.success(f"✅ {len(corrected_files)} fichiers XML corrigés")
                    
                    # Tableau des corrections
                    df_corrections = pd.DataFrame(correction_summary)
                    st.dataframe(df_corrections[['fichier', 'commande', 'regles_appliquees']], use_container_width=True)
                    
                    # Détails des règles appliquées
                    with st.expander("📋 Détails des Règles Appliquées"):
                        for summary in correction_summary:
                            commande_data = data_manager.get_commande_by_id(summary['commande'])
                            
                            st.markdown(f"**{summary['fichier']}** - Commande: {summary['commande']}")
                            
                            if commande_data:
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**Données appliquées:**")
                                    st.markdown(f"- Emploi CC: {commande_data.get('emploi_cc', 'N/A')}")
                                    st.markdown(f"- Catégorie: {commande_data.get('categorie_socio', 'N/A')}")
                                    st.markdown(f"- Classement: {commande_data.get('classement_cc', 'N/A')}")
                                
                                with col2:
                                    st.markdown("**Règles appliquées:**")
                                    if summary['details']:
                                        for rule in summary['details']:
                                            st.markdown(f"  - ✅ {rule}")
                                    else:
                                        st.markdown("  - ⚠️ Aucune règle appliquée")
                            
                            st.markdown("---")
                    
                    # Téléchargement
                    if len(corrected_files) == 1:
                        # Un seul fichier
                        file = corrected_files[0]
                        st.download_button(
                            label=f"📥 Télécharger {file['name']} (corrigé)",
                            data=file['content'],
                            file_name=f"THALES_CORRIGE_{file['name']}",
                            mime="application/xml"
                        )
                    else:
                        # Plusieurs fichiers - créer un ZIP
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for file in corrected_files:
                                zip_file.writestr(f"THALES_CORRIGE_{file['name']}", file['content'])
                        
                        st.download_button(
                            label=f"📥 Télécharger Archive ZIP ({len(corrected_files)} fichiers)",
                            data=zip_buffer.getvalue(),
                            file_name=f"THALES_XML_CORRIGES_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                            mime="application/zip"
                        )
        else:
            st.warning("⚠️ Aucune commande THALES détectée dans les fichiers XML")
            st.info("Vérifiez que vos fichiers XML contiennent des numéros de commande présents dans le Google Sheet")

# Point d'entrée
if __name__ == "__main__":
    main()
