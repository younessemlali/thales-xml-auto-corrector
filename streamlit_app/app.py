# streamlit_app/app.py
"""
THALES XML Auto-Corrector - Version Native 100%
Reproduit exactement la logique du Google Apps Script mais en upload direct
Repository: thales-xml-auto-corrector
"""

import streamlit as st
import json
import re
import zipfile
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
from lxml import etree
import pandas as pd

# Configuration
st.set_page_config(
    page_title="THALES XML Auto-Corrector",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ThalesEmailParser:
    """Parser pour emails THALES - reproduit la logique du script Apps Script"""
    
    def __init__(self):
        self.client = "THALES"
    
    def parse_html_email(self, file_content: str, file_name: str) -> Optional[Dict[str, Any]]:
        """
        Extrait les données THALES depuis un email HTML
        Reproduit exactement la logique du script Google Apps Script
        """
        try:
            # Nettoyer le contenu HTML (même logique que Apps Script)
            text_content = self._clean_html_content(file_content)
            
            # Validation THALES
            if not self._is_valid_thales_email(text_content):
                return None
            
            # Extraction des données (mêmes regex que Apps Script)
            extracted_data = {
                "fileName": file_name,
                "dateReception": datetime.now(),
                "client": "THALES"
            }
            
            # 1. Code agence (ex: GR1 dans "Agence de GR1-GR1")
            agence_match = re.search(r'Agence de ([A-Z0-9]+)(?:-[A-Z0-9]+)?', text_content, re.IGNORECASE)
            extracted_data["codeAgence"] = agence_match.group(1) if agence_match else 'INCONNU'
            
            # 2. Numéro de commande (ex: FU70001236)
            commande_match = re.search(r'Publication de la commande client N[°\s]*:\s*([A-Z0-9]+)', text_content, re.IGNORECASE)
            extracted_data["numeroCommande"] = commande_match.group(1) if commande_match else None
            
            # 3. EMPLOI CC (ex: 10A3071)
            emploi_match = re.search(r'\*?EMPLOi CC[:\s]*([A-Z0-9]+)(?:\s*-)', text_content, re.IGNORECASE)
            extracted_data["emploiCC"] = emploi_match.group(1).strip() if emploi_match else None
            
            # 4. Catégorie socio-professionnelle (ex: OUVRIER)
            categorie_match = re.search(r'\*?Catégorie socio-professionnelle[:\s]*([A-Z]+)', text_content, re.IGNORECASE)
            extracted_data["categorieSocio"] = categorie_match.group(1).strip() if categorie_match else None
            
            # 5. Classement CC (ex: B3)
            classement_match = re.search(r'\*?Classement CC[:\s]*([A-Z0-9]+)', text_content, re.IGNORECASE)
            extracted_data["classementCC"] = classement_match.group(1).strip() if classement_match else None
            
            # 6. Centre d'analyse (ex: 1FRA / PLADI/BP/PST04)
            centre_match = re.search(r'\*?Centre d\'analyse[:\s]*([^\\r\\n.]+)', text_content, re.IGNORECASE)
            extracted_data["centreAnalyse"] = centre_match.group(1).strip() if centre_match else None
            
            # 7. SIRET Client
            siret_match = re.search(r'SIRET[:\s]*([0-9]+)', text_content, re.IGNORECASE)
            extracted_data["siretClient"] = siret_match.group(1) if siret_match else None
            
            # 8. Site de mission
            site_match = re.search(r'Lieu de la mission[:\s]*([^\\r\\n]+?)(?=\\s*\\r|\\s*\\n|Informations|$)', text_content, re.IGNORECASE)
            extracted_data["siteMission"] = site_match.group(1).strip().replace('\\s+', ' ') if site_match else None
            
            # 9. Date début de mission
            date_debut_match = re.search(r'Date de début de mission[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})', text_content, re.IGNORECASE)
            if date_debut_match:
                extracted_data["dateDebut"] = self._parse_french_date(date_debut_match.group(1))
            
            # 10. Date fin de mission
            date_fin_match = re.search(r'Date de fin de mission[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})', text_content, re.IGNORECASE)
            if date_fin_match:
                extracted_data["dateFin"] = self._parse_french_date(date_fin_match.group(1))
            
            # Calcul du préfixe centre d'analyse
            extracted_data["centreAnalysePrefix"] = self._extract_centre_prefix(extracted_data.get("centreAnalyse", ""))
            
            # Déterminer si site ≠ GEMENOS
            extracted_data["siteNotGemenos"] = "GEMENOS" not in extracted_data.get("siteMission", "").upper()
            
            # Validation des données critiques
            if not extracted_data["numeroCommande"]:
                return None
                
            return extracted_data
            
        except Exception as e:
            st.error(f"Erreur lors de l'extraction de {file_name}: {e}")
            return None
    
    def _clean_html_content(self, content: str) -> str:
        """Nettoie le contenu HTML (même logique que Apps Script)"""
        # Supprimer les balises script et style
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Supprimer toutes les balises HTML
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Décoder les entités HTML
        html_entities = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&quot;': '"', '&#39;': "'", '=C3=A9': 'é', '=C3=A8': 'è',
            '=C3=A0': 'à', '=C2=B0': '°'
        }
        
        for entity, replacement in html_entities.items():
            content = content.replace(entity, replacement)
        
        # Nettoyer les espaces
        content = re.sub(r'\\r\\n', ' ', content)
        content = re.sub(r'\\n', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        
        return content
    
    def _is_valid_thales_email(self, content: str) -> bool:
        """Valide que c'est bien un email THALES"""
        return 'THALES SAS' in content and 'Publication de la commande client' in content
    
    def _parse_french_date(self, date_str: str) -> str:
        """Parse une date française DD/MM/YYYY"""
        try:
            day, month, year = date_str.split('/')
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            return date_str
    
    def _extract_centre_prefix(self, centre_analyse: str) -> str:
        """Extrait le préfixe du centre d'analyse"""
        if not centre_analyse:
            return ""
        
        parts = centre_analyse.split()
        if parts:
            return parts[0].split('/')[0].strip()
        return ""

class ThalesXMLCorrector:
    """Correcteur XML THALES basé sur les règles XPath"""
    
    def __init__(self):
        self.xml_rules = self._get_thales_xml_rules()
    
    def correct_xml_file(self, xml_content: str, thales_data: Dict[str, Any]) -> str:
        """Applique les corrections XML selon les règles THALES"""
        try:
            # Parser le XML
            parser = etree.XMLParser(strip_cdata=False)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)
            
            corrections_applied = []
            
            # Appliquer chaque règle
            for rule in self.xml_rules:
                if self._should_apply_rule(rule, thales_data):
                    success = self._apply_xml_rule(root, rule, thales_data)
                    if success:
                        corrections_applied.append(rule['name'])
            
            # Retourner le XML corrigé
            corrected_xml = etree.tostring(root, encoding='unicode', pretty_print=True)
            
            return corrected_xml, corrections_applied
            
        except Exception as e:
            st.error(f"Erreur lors de la correction XML: {e}")
            return xml_content, []
    
    def _should_apply_rule(self, rule: Dict[str, Any], thales_data: Dict[str, Any]) -> bool:
        """Détermine si une règle doit être appliquée"""
        # Vérifier les conditions
        if 'condition' in rule:
            condition = rule['condition']
            if condition == 'site_not_gemenos':
                return thales_data.get('siteNotGemenos', False)
        
        # Vérifier que le champ source existe
        source_field = rule['source_field']
        return bool(thales_data.get(self._map_field_name(source_field)))
    
    def _apply_xml_rule(self, root: etree.Element, rule: Dict[str, Any], thales_data: Dict[str, Any]) -> bool:
        """Applique une règle XML spécifique"""
        try:
            xpath = rule['xpath']
            source_field = rule['source_field']
            action = rule['action']
            
            # Mapper le nom du champ
            mapped_field = self._map_field_name(source_field)
            value = thales_data.get(mapped_field)
            
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
    
    def _map_field_name(self, source_field: str) -> str:
        """Mappe les noms de champs entre les règles et les données extraites"""
        mapping = {
            'order_id': 'numeroCommande',
            'emploi_cc': 'emploiCC',
            'categorie_socio': 'categorieSocio',
            'classement_cc': 'classementCC',
            'centre_analyse': 'centreAnalyse',
            'centre_analyse_prefix': 'centreAnalysePrefix'
        }
        return mapping.get(source_field, source_field)
    
    def _get_thales_xml_rules(self) -> List[Dict[str, Any]]:
        """Définit les règles XML THALES (même logique que le script sync)"""
        return [
            {
                "name": "numero_commande",
                "description": "Numéro de commande dans OrderId/IdValue",
                "xpath": "//ReferenceInformation/OrderId/IdValue",
                "source_field": "order_id",
                "action": "create_or_update",
                "parent_xpath": "//ReferenceInformation/OrderId",
                "group": "ReferenceInformation"
            },
            {
                "name": "emploi_cc_position_code",
                "description": "EMPLOI CC dans PositionStatus/Code",
                "xpath": "//PositionCharacteristics/PositionStatus/Code",
                "source_field": "emploi_cc",
                "action": "create_or_update",
                "parent_xpath": "//PositionCharacteristics/PositionStatus",
                "group": "PositionCharacteristics"
            },
            {
                "name": "categorie_socio_position_level",
                "description": "Catégorie socio-professionnelle dans PositionLevel",
                "xpath": "//PositionCharacteristics/PositionLevel",
                "source_field": "categorie_socio",
                "action": "create_or_update",
                "parent_xpath": "//PositionCharacteristics",
                "group": "PositionCharacteristics"
            },
            {
                "name": "classement_cc_coefficient",
                "description": "Classement CC dans PositionCoefficient",
                "xpath": "//PositionCharacteristics/PositionCoefficient",
                "source_field": "classement_cc",
                "action": "create_or_update",
                "parent_xpath": "//PositionCharacteristics",
                "group": "PositionCharacteristics"
            },
            {
                "name": "centre_analyse_cost_center_name",
                "description": "Centre d'analyse complet dans CostCenterName",
                "xpath": "//CustomerReportingRequirements/CostCenterName",
                "source_field": "centre_analyse",
                "action": "create_or_update",
                "parent_xpath": "//CustomerReportingRequirements",
                "group": "CustomerReportingRequirements"
            },
            {
                "name": "centre_analyse_department_code",
                "description": "Préfixe centre d'analyse dans DepartmentCode",
                "xpath": "//CustomerReportingRequirements/DepartmentCode",
                "source_field": "centre_analyse_prefix",
                "action": "create_or_update",
                "parent_xpath": "//CustomerReportingRequirements",
                "group": "CustomerReportingRequirements"
            },
            {
                "name": "centre_analyse_cost_center_code",
                "description": "Préfixe centre d'analyse dans CostCenterCode",
                "xpath": "//CustomerReportingRequirements/CostCenterCode",
                "source_field": "centre_analyse_prefix",
                "action": "create_or_update",
                "parent_xpath": "//CustomerReportingRequirements",
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
                "group": "ContractInformation"
            }
        ]

def main():
    """Interface principale Streamlit"""
    
    # Titre et description
    st.title("⚙️ THALES XML Auto-Corrector")
    st.markdown("**Version Native 100% - Sans APIs externes**")
    
    # Sidebar pour les instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        **Étape 1:** Uploadez vos emails THALES (HTML/EML)
        
        **Étape 2:** Vérifiez les données extraites
        
        **Étape 3:** Uploadez vos fichiers XML à corriger
        
        **Étape 4:** Téléchargez les XML corrigés
        """)
        
        st.markdown("---")
        st.markdown("**🎯 Reproduit exactement la logique du script Google Apps Script**")
    
    # Initialiser les parsers
    email_parser = ThalesEmailParser()
    xml_corrector = ThalesXMLCorrector()
    
    # Étape 1: Upload des emails THALES
    st.header("📧 1. Upload des Emails THALES")
    
    uploaded_emails = st.file_uploader(
        "Sélectionnez vos emails THALES (HTML ou EML)",
        type=['html', 'eml', 'txt'],
        accept_multiple_files=True,
        help="Même format que ceux traités par Google Apps Script"
    )
    
    thales_data_list = []
    
    if uploaded_emails:
        st.success(f"📁 {len(uploaded_emails)} fichiers email uploadés")
        
        # Parser chaque email
        with st.expander("🔍 Détails de l'extraction", expanded=True):
            for i, email_file in enumerate(uploaded_emails):
                try:
                    # Lire le contenu
                    content = email_file.read().decode('utf-8', errors='ignore')
                    
                    # Parser avec la même logique que Apps Script
                    extracted_data = email_parser.parse_html_email(content, email_file.name)
                    
                    if extracted_data:
                        thales_data_list.append(extracted_data)
                        
                        # Afficher les données extraites
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**✅ {email_file.name}**")
                            st.markdown(f"- **Commande:** {extracted_data.get('numeroCommande', 'N/A')}")
                            st.markdown(f"- **Agence:** {extracted_data.get('codeAgence', 'N/A')}")
                            st.markdown(f"- **Emploi CC:** {extracted_data.get('emploiCC', 'N/A')}")
                        
                        with col2:
                            st.markdown("**Données extraites:**")
                            st.markdown(f"- **Catégorie:** {extracted_data.get('categorieSocio', 'N/A')}")
                            st.markdown(f"- **Classement:** {extracted_data.get('classementCC', 'N/A')}")
                            st.markdown(f"- **Centre:** {extracted_data.get('centreAnalysePrefix', 'N/A')}")
                    else:
                        st.warning(f"⚠️ {email_file.name}: Données THALES non détectées")
                
                except Exception as e:
                    st.error(f"❌ Erreur avec {email_file.name}: {e}")
    
    # Étape 2: Affichage du résumé des données
    if thales_data_list:
        st.header("📊 2. Données THALES Extraites")
        
        # Créer un DataFrame pour affichage
        df_display = pd.DataFrame([
            {
                'Fichier': data['fileName'],
                'Commande': data.get('numeroCommande', ''),
                'Agence': data.get('codeAgence', ''),
                'Emploi CC': data.get('emploiCC', ''),
                'Catégorie': data.get('categorieSocio', ''),
                'Classement': data.get('classementCC', ''),
                'Centre': data.get('centreAnalyse', ''),
                'Préfixe': data.get('centreAnalysePrefix', '')
            }
            for data in thales_data_list
        ])
        
        st.dataframe(df_display, use_container_width=True)
        
        # Statistiques
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📧 Emails traités", len(thales_data_list))
        with col2:
            agences = set(data.get('codeAgence', '') for data in thales_data_list)
            st.metric("🏢 Agences", len(agences))
        with col3:
            commandes = set(data.get('numeroCommande', '') for data in thales_data_list if data.get('numeroCommande'))
            st.metric("📋 Commandes", len(commandes))
        with col4:
            emplois = set(data.get('emploiCC', '') for data in thales_data_list if data.get('emploiCC'))
            st.metric("💼 Emplois CC", len(emplois))
    
    # Étape 3: Upload des fichiers XML
    if thales_data_list:
        st.header("⚙️ 3. Correction des Fichiers XML")
        
        uploaded_xmls = st.file_uploader(
            "Sélectionnez vos fichiers XML à corriger",
            type=['xml'],
            accept_multiple_files=True,
            help="Les corrections seront appliquées selon les règles THALES"
        )
        
        if uploaded_xmls:
            st.success(f"📁 {len(uploaded_xmls)} fichiers XML uploadés")
            
            # Options de correction
            with st.expander("🔧 Options de Correction"):
                auto_detect = st.checkbox("🎯 Détection automatique par numéro de commande", value=True)
                manual_mapping = st.checkbox("🔧 Correspondance manuelle", value=False)
                
                if manual_mapping:
                    st.info("Fonctionnalité de correspondance manuelle à implémenter")
            
            # Bouton de correction
            if st.button("🚀 Appliquer les Corrections THALES", type="primary"):
                corrected_files = []
                correction_summary = []
                
                # Traiter chaque fichier XML
                for xml_file in uploaded_xmls:
                    try:
                        xml_content = xml_file.read().decode('utf-8')
                        
                        # Détecter la commande associée
                        matching_data = None
                        if auto_detect:
                            # Chercher le numéro de commande dans le XML
                            for data in thales_data_list:
                                if data.get('numeroCommande') and data['numeroCommande'] in xml_content:
                                    matching_data = data
                                    break
                        
                        if not matching_data and thales_data_list:
                            # Prendre la première par défaut
                            matching_data = thales_data_list[0]
                        
                        if matching_data:
                            # Appliquer les corrections
                            corrected_xml, applied_rules = xml_corrector.correct_xml_file(xml_content, matching_data)
                            
                            corrected_files.append({
                                'name': xml_file.name,
                                'content': corrected_xml,
                                'original_size': len(xml_content),
                                'corrected_size': len(corrected_xml)
                            })
                            
                            correction_summary.append({
                                'fichier': xml_file.name,
                                'commande': matching_data.get('numeroCommande', 'N/A'),
                                'regles_appliquees': len(applied_rules),
                                'details': applied_rules
                            })
                        else:
                            st.warning(f"⚠️ Aucune donnée THALES trouvée pour {xml_file.name}")
                    
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
                            st.markdown(f"**{summary['fichier']}** (Commande: {summary['commande']})")
                            if summary['details']:
                                for rule in summary['details']:
                                    st.markdown(f"  - ✅ {rule}")
                            else:
                                st.markdown("  - ⚠️ Aucune règle appliquée")
                    
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

# Point d'entrée
if __name__ == "__main__":
    main()
