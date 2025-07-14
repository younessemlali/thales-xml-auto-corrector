# streamlit_app/app.py
"""
Application Streamlit pour la correction automatique des fichiers XML THALES
Repository: thales-xml-auto-corrector
"""

import streamlit as st
import pandas as pd
import json
import zipfile
import io
import re
from datetime import datetime
from lxml import etree
from typing import Dict, List, Any, Optional, Tuple

# Configuration de la page
st.set_page_config(
    page_title="THALES XML Auto-Corrector",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration des chemins
THALES_ORDERS_JSON_PATH = 'thales_orders.json'

class ThalesXMLProcessor:
    """Processeur XML spécialisé pour les commandes THALES"""
    
    def __init__(self, thales_data: Dict[str, Any]):
        self.thales_data = thales_data
        self.commandes = {cmd['order_id']: cmd for cmd in thales_data.get('commandes', [])}
        self.regles_xml = thales_data.get('regles_xml', [])
        
    def extract_order_id_from_xml(self, xml_content: str) -> Optional[str]:
        """Extrait le numéro de commande du XML"""
        try:
            # Patterns pour détecter les numéros de commande THALES
            patterns = [
                r'FU\d{8}',  # Format standard FU70001236
                r'<OrderId[^>]*>.*?FU\d{8}.*?</OrderId>',
                r'<IdValue[^>]*>(FU\d{8})</IdValue>',
                r'<CustomerJobCode[^>]*>(FU\d{8})</CustomerJobCode>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, xml_content, re.IGNORECASE)
                for match in matches:
                    # Extraire juste le numéro de commande
                    order_match = re.search(r'FU\d{8}', match)
                    if order_match:
                        return order_match.group(0)
            
            return None
            
        except Exception as e:
            st.error(f"Erreur lors de l'extraction de l'order ID: {e}")
            return None
    
    def get_commande_data(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une commande THALES"""
        return self.commandes.get(order_id)
    
    def apply_xml_rule(self, xml_tree: etree.Element, rule: Dict[str, Any], commande_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Applique une règle XML spécifique"""
        try:
            rule_name = rule.get('name')
            xpath = rule.get('xpath')
            source_field = rule.get('source_field')
            action = rule.get('action', 'create_or_update')
            condition = rule.get('condition')
            
            # Vérifier la condition si elle existe
            if condition and condition == 'site_not_gemenos':
                if not commande_data.get('site_not_gemenos', False):
                    return False, f"Condition {condition} non remplie"
            
            # Récupérer la valeur à insérer
            value = commande_data.get(source_field)
            if not value:
                return False, f"Valeur manquante pour {source_field}"
            
            # Chercher l'élément existant
            existing_elements = xml_tree.xpath(xpath)
            
            if existing_elements:
                # Mettre à jour l'élément existant
                existing_elements[0].text = str(value)
                return True, f"Mis à jour {rule_name}: {value}"
            else:
                # Créer un nouvel élément
                return self._create_xml_element(xml_tree, rule, value)
                
        except Exception as e:
            return False, f"Erreur lors de l'application de la règle {rule_name}: {e}"
    
    def _create_xml_element(self, xml_tree: etree.Element, rule: Dict[str, Any], value: str) -> Tuple[bool, str]:
        """Crée un nouvel élément XML selon la règle"""
        try:
            parent_xpath = rule.get('parent_xpath')
            position = rule.get('position', 'last_child')
            
            if not parent_xpath:
                return False, f"parent_xpath manquant pour {rule.get('name')}"
            
            # Trouver l'élément parent
            parent_elements = xml_tree.xpath(parent_xpath)
            if not parent_elements:
                return False, f"Élément parent non trouvé: {parent_xpath}"
            
            parent = parent_elements[0]
            
            # Extraire le nom de l'élément depuis le xpath
            element_name = rule.get('xpath', '').split('/')[-1]
            if not element_name:
                return False, f"Impossible d'extraire le nom de l'élément"
            
            # Créer le nouvel élément
            new_element = etree.SubElement(parent, element_name)
            new_element.text = str(value)
            
            return True, f"Créé {rule.get('name')}: {value}"
            
        except Exception as e:
            return False, f"Erreur lors de la création de l'élément: {e}"
    
    def process_xml(self, xml_content: str, order_id: str) -> Tuple[Optional[str], List[str]]:
        """Traite un XML avec les règles THALES"""
        try:
            # Parser le XML
            parser = etree.XMLParser(strip_whitespace=False, recover=True)
            xml_tree = etree.fromstring(xml_content.encode('utf-8'), parser)
            
            # Récupérer les données de la commande
            commande_data = self.get_commande_data(order_id)
            if not commande_data:
                return None, [f"❌ Commande {order_id} non trouvée dans les données THALES"]
            
            applied_rules = []
            
            # Appliquer chaque règle XML
            for rule in self.regles_xml:
                success, message = self.apply_xml_rule(xml_tree, rule, commande_data)
                if success:
                    applied_rules.append(f"✅ {message}")
                else:
                    applied_rules.append(f"⚠️ {message}")
            
            # Générer le XML corrigé
            corrected_xml = etree.tostring(xml_tree, encoding='unicode', pretty_print=True)
            
            return corrected_xml, applied_rules
            
        except Exception as e:
            return None, [f"❌ Erreur lors du traitement XML: {e}"]

@st.cache_data(ttl=300)  # Cache 5 minutes
def load_thales_data():
    """Charge les données THALES avec cache"""
    try:
        with open(THALES_ORDERS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        st.sidebar.success(f"✅ {len(data.get('commandes', []))} commandes THALES chargées")
        return data
        
    except FileNotFoundError:
        st.sidebar.error(f"❌ Fichier {THALES_ORDERS_JSON_PATH} non trouvé")
        st.sidebar.info("Exécutez d'abord la synchronisation GitHub Actions")
        return None
    except Exception as e:
        st.sidebar.error(f"❌ Erreur chargement: {e}")
        return None

def display_thales_statistics(thales_data: Dict[str, Any]):
    """Affiche les statistiques THALES"""
    stats = thales_data.get('statistiques', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Commandes", stats.get('total_commandes', 0))
    
    with col2:
        st.metric("Codes Agence", len(stats.get('codes_agence_uniques', [])))
    
    with col3:
        st.metric("Emplois CC", len(stats.get('emplois_cc_uniques', [])))
    
    with col4:
        st.metric("Règles XML", len(thales_data.get('regles_xml', [])))

def display_commande_details(commande_data: Dict[str, Any]):
    """Affiche les détails d'une commande THALES"""
    st.write("### 📋 Détails de la Commande")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Numéro:** {commande_data.get('order_id', 'N/A')}")
        st.write(f"**Code Agence:** {commande_data.get('code_agence', 'N/A')}")
        st.write(f"**Emploi CC:** {commande_data.get('emploi_cc', 'N/A')}")
        st.write(f"**Catégorie Socio:** {commande_data.get('categorie_socio', 'N/A')}")
        st.write(f"**Classement CC:** {commande_data.get('classement_cc', 'N/A')}")
    
    with col2:
        st.write(f"**Centre d'Analyse:** {commande_data.get('centre_analyse', 'N/A')}")
        st.write(f"**SIRET Client:** {commande_data.get('siret_client', 'N/A')}")
        st.write(f"**Date Début:** {commande_data.get('date_debut', 'N/A')}")
        st.write(f"**Date Fin:** {commande_data.get('date_fin', 'N/A')}")
        st.write(f"**Site Mission:** {commande_data.get('site_mission', 'N/A')[:50]}...")

def main():
    """Fonction principale de l'application Streamlit"""
    
    # En-tête
    st.title("⚙️ THALES XML Auto-Corrector")
    st.markdown("*Correction automatique des fichiers XML THALES basée sur les données de commandes*")
    
    # Sidebar - Chargement des données
    with st.sidebar:
        st.header("📊 Données THALES")
        
        # Bouton de rechargement des données
        if st.button("🔄 Recharger les données"):
            st.cache_data.clear()
            st.rerun()
        
        # Chargement des données
        thales_data = load_thales_data()
        
        if not thales_data:
            st.stop()
        
        # Affichage des informations de dernière mise à jour
        last_updated = thales_data.get('metadata', {}).get('last_updated', 'Inconnue')
        st.info(f"🕒 Dernière MAJ: {last_updated[:19].replace('T', ' ')}")
        
        # Filtre par code agence
        stats = thales_data.get('statistiques', {})
        codes_agence = ['Tous'] + stats.get('codes_agence_uniques', [])
        selected_agence = st.selectbox("📍 Filtrer par agence", codes_agence)
    
    # Affichage des statistiques
    display_thales_statistics(thales_data)
    
    # Interface principale
    st.header("📁 Upload et Traitement XML")
    
    # Upload de fichiers
    uploaded_files = st.file_uploader(
        "Sélectionnez les fichiers XML à corriger",
        type=['xml'],
        accept_multiple_files=True,
        help="Supports: fichiers XML individuels ou multiples"
    )
    
    if uploaded_files:
        # Initialisation du processeur
        processor = ThalesXMLProcessor(thales_data)
        
        st.write(f"### 📄 {len(uploaded_files)} fichier(s) uploadé(s)")
        
        # Traitement des fichiers
        results = []
        processed_files = []
        
        for uploaded_file in uploaded_files:
            st.write(f"#### 🔄 Traitement: {uploaded_file.name}")
            
            try:
                # Lire le contenu XML
                xml_content = uploaded_file.read().decode('utf-8')
                
                # Extraire l'order ID
                order_id = processor.extract_order_id_from_xml(xml_content)
                
                if not order_id:
                    st.error(f"❌ Numéro de commande THALES non trouvé dans {uploaded_file.name}")
                    continue
                
                st.success(f"✅ Commande détectée: **{order_id}**")
                
                # Récupérer les données de la commande
                commande_data = processor.get_commande_data(order_id)
                
                if not commande_data:
                    st.error(f"❌ Commande {order_id} non trouvée dans les données")
                    continue
                
                # Filtrage par agence si sélectionné
                if selected_agence != 'Tous' and commande_data.get('code_agence') != selected_agence:
                    st.warning(f"⚠️ Commande ignorée (agence: {commande_data.get('code_agence')})")
                    continue
                
                # Afficher les détails de la commande
                with st.expander(f"📋 Détails commande {order_id}", expanded=False):
                    display_commande_details(commande_data)
                
                # Traitement XML
                corrected_xml, applied_rules = processor.process_xml(xml_content, order_id)
                
                if corrected_xml:
                    st.success(f"✅ XML corrigé avec succès!")
                    
                    # Afficher les règles appliquées
                    with st.expander(f"📝 Règles appliquées ({len(applied_rules)})", expanded=False):
                        for rule in applied_rules:
                            st.write(rule)
                    
                    # Préparer pour téléchargement
                    processed_files.append({
                        'original_name': uploaded_file.name,
                        'corrected_name': f"{uploaded_file.name.replace('.xml', '')}_THALES_corrected.xml",
                        'content': corrected_xml,
                        'order_id': order_id,
                        'rules_applied': len([r for r in applied_rules if r.startswith('✅')])
                    })
                    
                else:
                    st.error(f"❌ Échec de la correction du XML")
                    for rule in applied_rules:
                        st.write(rule)
            
            except Exception as e:
                st.error(f"❌ Erreur lors du traitement de {uploaded_file.name}: {e}")
        
        # Section de téléchargement
        if processed_files:
            st.header("💾 Téléchargement")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 📄 Fichiers individuels")
                for file_info in processed_files:
                    st.download_button(
                        label=f"📥 {file_info['corrected_name']}",
                        data=file_info['content'],
                        file_name=file_info['corrected_name'],
                        mime='application/xml',
                        help=f"Commande: {file_info['order_id']} | {file_info['rules_applied']} règles appliquées"
                    )
            
            with col2:
                if len(processed_files) > 1:
                    st.write("### 📦 Archive ZIP")
                    
                    # Créer une archive ZIP
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_info in processed_files:
                            zip_file.writestr(file_info['corrected_name'], file_info['content'])
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label=f"📥 Télécharger tous ({len(processed_files)} fichiers)",
                        data=zip_buffer.getvalue(),
                        file_name=f"THALES_XML_corrected_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                        mime='application/zip'
                    )
            
            # Résumé
            st.success(f"🎉 **{len(processed_files)} fichier(s) traité(s) avec succès!**")
            
            # Tableau récapitulatif
            if len(processed_files) > 1:
                df_summary = pd.DataFrame([
                    {
                        'Fichier': f['original_name'],
                        'Commande': f['order_id'],
                        'Règles Appliquées': f['rules_applied']
                    }
                    for f in processed_files
                ])
                
                st.write("### 📊 Résumé du traitement")
                st.dataframe(df_summary, use_container_width=True)
    
    # Section informations
    with st.expander("ℹ️ Comment utiliser cette application", expanded=False):
        st.markdown("""
        ### 🚀 Étapes d'utilisation
        
        1. **📁 Upload** : Sélectionnez un ou plusieurs fichiers XML THALES
        2. **🔍 Détection** : L'application détecte automatiquement les numéros de commande
        3. **📋 Correspondance** : Les données de commande sont récupérées depuis le Google Sheet
        4. **⚙️ Correction** : Application automatique des règles XML THALES
        5. **💾 Téléchargement** : Récupération des fichiers XML corrigés
        
        ### 📝 Règles appliquées
        
        - **Numéro de commande** → `OrderId/IdValue`
        - **Emploi CC** → `PositionStatus/Code`  
        - **Catégorie socio** → `PositionLevel`
        - **Classement CC** → `PositionCoefficient`
        - **Centre d'analyse** → `CostCenterName`, `DepartmentCode`, `CostCenterCode`
        - **WorkSite conditionnel** → Si site ≠ GEMENOS
        
        ### 🔄 Synchronisation
        
        Les données sont synchronisées automatiquement toutes les 15 minutes depuis votre Google Sheet.
        """)

if __name__ == "__main__":
    main()
