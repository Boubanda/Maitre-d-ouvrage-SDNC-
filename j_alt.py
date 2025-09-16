import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import json
import re
from datetime import datetime
import io
import base64
import pymupdf as fitz
import numpy as np
from typing import Dict, List, Optional, Tuple
import time
import plotly.graph_objects as go
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="Maquette MOA : Extraction automatisée de données",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    :root {
        --primary-color: #1e3c72;
        --secondary-color: #2a5298;
        --accent-color: #4a90e2;
        --success-color: #4caf50;
        --warning-color: #ff9800;
        --error-color: #f44336;
        --light-bg: #f8f9fa;
        --dark-text: #2c3e50;
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 12px;
        margin-bottom: 2.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid var(--accent-color);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-3px);
    }
    
    .extraction-result {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid var(--success-color);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
    }
    
    .error-box {
        background: #fff5f5;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid var(--error-color);
        box-shadow: 0 4px 12px rgba(244, 67, 54, 0.1);
    }
    
    .workflow-step {
        background: white;
        padding: 1.5rem;
        margin: 0.75rem 0;
        border-radius: 10px;
        border-left: 5px solid var(--accent-color);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .validation-box {
        background: #fffaf5;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid var(--warning-color);
        box-shadow: 0 4px 12px rgba(255, 152, 0, 0.1);
    }
    
    .upload-box {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed var(--accent-color);
        text-align: center;
        transition: all 0.3s ease;
        margin-bottom: 2rem;
    }
    
    .upload-box:hover {
        border-color: var(--primary-color);
        background: #f8faff;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
    }
    
    .stTab {
        border-radius: 10px;
    }
    
    .stTab [role="tablist"] {
        background: white;
        border-radius: 10px 10px 0 0;
        padding: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .stTab [role="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        margin: 0 0.25rem;
        transition: all 0.3s ease;
    }
    
    .stTab [role="tab"][aria-selected="true"] {
        background: var(--accent-color);
        color: white;
    }
    
    .sidebar .sidebar-content {
        background: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--dark-text);
    }
    
    .file-info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class OCRProcessor:
    """Classe pour traiter l'OCR et l'extraction de données"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extrait le texte d'un PDF"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            st.error(f"Erreur lors de l'extraction PDF: {str(e)}")
            return ""
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extrait le texte d'une image avec Tesseract"""
        try:
            # Configuration OCR pour le français
            config = r'--oem 3 --psm 6 -l fra'
            text = pytesseract.image_to_string(image, config=config)
            return text
        except Exception as e:
            st.error(f"Erreur OCR: {str(e)}")
            return ""
    
    def extract_structured_data(self, text: str) -> Dict:
        """Extrait les données structurées du texte"""
        data = {
            'numero_reference': None,
            'nom': None,
            'prenom': None,
            'date': None,
            'montant': None,
            'numero_siret': None,
            'adresse': None,
            'telephone': None,
            'email': None
        }
        
        # Patterns de reconnaissance
        patterns = {
            'numero_reference': r'(?:ref|référence|numéro|n°)\s*:?\s*([A-Z0-9\-]+)',
            'nom': r'(?:nom|famille)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'prenom': r'(?:prénom|prenom)\s*:?\s*([A-Z][a-z]+)',
            'date': r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            'montant': r'(\d+(?:\s?\d{3})*(?:[,\.]\d{2})?)\s*€?',
            'numero_siret': r'(?:siret|siren)\s*:?\s*(\d{14})',
            'telephone': r'(?:tél|téléphone|tel)\s*:?\s*(\d{2}(?:\s?\d{2}){4})',
            'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'adresse': r'(?:adresse)\s*:?\s*([0-9]+[^0-9\n]+(?:\n[^0-9\n]+)*)'
        }
        
        # Extraction avec regex
        for field, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                data[field] = matches[0].strip()
        
        return data

def create_workflow_visualization():
    """Crée une visualisation du workflow"""
    fig = go.Figure()
    
    # Étapes du workflow
    steps = [
        "Téléversement",
        "OCR",
        "Extraction",
        "Validation",
        "Sauvegarde"
    ]
    
    # Positions
    x_positions = [1, 2, 3, 4, 5]
    y_positions = [1, 1, 1, 1, 1]
    
    # Ajout des nœuds
    fig.add_trace(go.Scatter(
        x=x_positions,
        y=y_positions,
        mode='markers+text',
        marker=dict(size=60, color='#2a5298'),
        text=steps,
        textposition="middle center",
        textfont=dict(color="white", size=10),
        showlegend=False
    ))
    
    # Ajout des flèches
    for i in range(len(x_positions)-1):
        fig.add_annotation(
            x=x_positions[i+1],
            y=y_positions[i+1],
            ax=x_positions[i],
            ay=y_positions[i],
            xref="x", yref="y",
            axref="x", ayref="y",
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#2a5298"
        )
    
    fig.update_layout(
        title="Workflow de traitement des documents",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def main():
    # En-tête principal avec logo et titre
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 1rem;">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h1 style="margin: 0;">Maquette MOA : Extraction automatisée de données</h1>
        </div>
        <p style="font-size: 1.1rem; opacity: 0.9;">Solution intelligente de numérisation et d'extraction de données structurées</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar pour les informations
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 16V12" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 8H12.01" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h3>Informations</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📊 Stack technique", expanded=True):
            st.info("""
            - **Streamlit** (Interface utilisateur)
            - **Tesseract OCR** (Reconnaissance de texte)
            - **PyMuPDF** (Traitement PDF)
            - **Regex/Pattern matching** (Extraction de données)
            - **Plotly** (Visualisations interactives)
            """)
        
        with st.expander("📋 Formats supportés"):
            st.write("""
            - Documents PDF
            - Images (PNG, JPG, JPEG)
            - Formats haute résolution (TIFF, BMP)
            """)
        
        with st.expander("🎯 Données extraites"):
            st.write("""
            - Numéros de référence
            - Nom et prénom
            - Dates importantes
            - Montants financiers
            - Numéros SIRET/SIREN
            - Coordonnées complètes
            """)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem; margin-top: 2rem;">
            <p>Version 1.0.0</p>
            <p>© 2023 DGFiP - Tous droits réservés</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Workflow visualization
    st.plotly_chart(create_workflow_visualization(), use_container_width=True)
    
    # Initialisation du processeur OCR
    ocr_processor = OCRProcessor()
    
    # Section de téléversement améliorée
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="color: var(--primary-color);">📤 Téléversement de document</h2>
        <p style="color: #666;">Sélectionnez un document PDF ou image pour commencer le traitement</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container():
            st.markdown('<div class="upload-box">', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Glissez-déposez un fichier ou cliquez pour parcourir",
                type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
                help="Formats supportés : PDF, PNG, JPG, JPEG, TIFF, BMP",
                label_visibility="collapsed"
            )
            st.markdown('<p style="color: #666; font-size: 0.9rem;">Taille maximale : 10MB</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if uploaded_file:
            st.markdown('<div class="file-info-card">', unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 2V8H20" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <h4 style="margin: 0; color: var(--dark-text);">Fichier prêt</h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(f"**Nom :** {uploaded_file.name}")
            st.write(f"**Type :** {uploaded_file.type.split('/')[-1].upper()}")
            st.write(f"**Taille :** {uploaded_file.size / 1024:.1f} KB")
            st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # Étape 1: Aperçu du fichier
        st.markdown("""
        <div style="margin: 2rem 0 1.5rem 0;">
            <h2 style="color: var(--primary-color);">🔍 Aperçu du document</h2>
            <p style="color: #666;">Vérifiez que le document est correct avant traitement</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if uploaded_file.type == "application/pdf":
                try:
                    # Conversion PDF vers image pour l'aperçu
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    page = doc[0]
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Aperçu avec cadre
                    st.markdown('<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; background: white;">', unsafe_allow_html=True)
                    st.image(image, caption="Aperçu du PDF (Page 1)", use_column_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    doc.close()
                    uploaded_file.seek(0)  # Reset file pointer
                except Exception as e:
                    st.error(f"Erreur lors de l'aperçu PDF: {str(e)}")
            else:
                image = Image.open(uploaded_file)
                st.markdown('<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; background: white;">', unsafe_allow_html=True)
                st.image(image, caption="Aperçu du document", use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                uploaded_file.seek(0)  # Reset file pointer
        
        with col2:
            st.markdown("""
            <div class="workflow-step">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                        <path d="M8 10L12 14L22 4" stroke="#2196f3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16" stroke="#2196f3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <h4 style="margin: 0;">Étape 1 : Aperçu</h4>
                </div>
                <p style="margin: 0.5rem 0 0 0; color: #666;">Document chargé avec succès</p>
                <div style="display: flex; align-items: center; margin-top: 1rem;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M12 16V12" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M12 8H12.01" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <p style="margin: 0; color: #4caf50; font-weight: 500;">Prêt pour l'extraction</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Bouton d'extraction amélioré
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <button onclick="document.querySelector('.stButton button').click()" style="background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%); color: white; border: none; border-radius: 8px; padding: 1rem 2rem; font-size: 1.1rem; font-weight: 500; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);">
                🚀 Lancer l'extraction des données
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        # Étape 2: OCR et extraction
        if st.button("🧠 Lancer l'OCR et l'extraction", type="primary", key="extract_button"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Zone de statut stylisée
            status_container = st.container()
            with status_container:
                st.markdown('<div class="workflow-step">', unsafe_allow_html=True)
                
                # Simulation du traitement
                for i in range(100):
                    progress_bar.progress(i + 1)
                    if i < 30:
                        status_text.markdown("""
                        <div style="display: flex; align-items: center;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                                <path d="M12 2V6" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M12 18V22" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M4.93 4.93L7.76 7.76" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M16.24 16.24L19.07 19.07" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M2 12H6" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M18 12H22" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M4.93 19.07L7.76 16.24" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M16.24 7.76L19.07 4.93" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <p style="margin: 0;">Analyse du document en cours...</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif i < 60:
                        status_text.markdown("""
                        <div style="display: flex; align-items: center;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                                <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <p style="margin: 0;">Extraction du texte...</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif i < 90:
                        status_text.markdown("""
                        <div style="display: flex; align-items: center;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                                <path d="M19 21L12 16L5 21V5C5 4.46957 5.21071 3.96086 5.58579 3.58579C5.96086 3.21071 6.46957 3 7 3H17C17.5304 3 18.0391 3.21071 18.4142 3.58579C18.7893 3.96086 19 4.46957 19 5V21Z" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <p style="margin: 0;">Identification des données structurées...</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        status_text.markdown("""
                        <div style="display: flex; align-items: center;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                                <path d="M22 11.08V12C21.9988 14.1564 21.3005 16.2547 20.0093 17.9818C18.7182 19.709 16.9033 20.9725 14.8354 21.5839C12.7674 22.1953 10.5573 22.1219 8.53447 21.3746C6.51168 20.6273 4.78465 19.2461 3.61096 17.4371C2.43727 15.628 1.87979 13.4881 2.02168 11.3363C2.16356 9.18455 2.99721 7.13631 4.39828 5.49706C5.79935 3.85781 7.69279 2.71537 9.79619 2.24013C11.8996 1.7649 14.1003 1.98232 16.07 2.86" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M22 4L12 14.01L9 11.01" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <p style="margin: 0; color: #4caf50; font-weight: 500;">Traitement terminé avec succès!</p>
                        </div>
                        """, unsafe_allow_html=True)
                    time.sleep(0.02)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Extraction du texte
            extracted_text = ""
            
            if uploaded_file.type == "application/pdf":
                file_bytes = uploaded_file.read()
                extracted_text = ocr_processor.extract_text_from_pdf(file_bytes)
                uploaded_file.seek(0)
            else:
                image = Image.open(uploaded_file)
                extracted_text = ocr_processor.extract_text_from_image(image)
                uploaded_file.seek(0)
            
            # Stockage dans session state
            st.session_state.extracted_text = extracted_text
            st.session_state.extracted_data = ocr_processor.extract_structured_data(extracted_text)
            
            progress_bar.empty()
            status_text.empty()
        
        # Affichage des résultats
        if 'extracted_text' in st.session_state and 'extracted_data' in st.session_state:
            st.markdown("""
            <div style="margin: 3rem 0 1.5rem 0;">
                <h2 style="color: var(--primary-color);">📊 Résultats de l'extraction</h2>
                <p style="color: #666;">Vérifiez et validez les données extraites</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Tabs pour organiser les résultats
            tab1, tab2, tab3 = st.tabs(["📋 Données structurées", "📄 Texte brut", "✅ Validation"])
            
            with tab1:
                st.markdown('<div class="extraction-result">', unsafe_allow_html=True)
                
                # En-tête avec icône
                st.markdown("""
                <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.75rem;">
                        <path d="M9 17V7M9 17L5 13M9 17L13 13M15 7V17M15 17L19 13M15 17L11 13" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <h3 style="margin: 0;">Données structurées extraites</h3>
                </div>
                """, unsafe_allow_html=True)
                
                data = st.session_state.extracted_data
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("📋 Numéro de référence", data.get('numero_reference', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("👤 Nom", data.get('nom', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("👤 Prénom", data.get('prenom', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("📅 Date", data.get('date', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("📧 Email", data.get('email', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("💰 Montant", data.get('montant', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("🏢 SIRET", data.get('numero_siret', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("📞 Téléphone", data.get('telephone', 'Non trouvé'))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("📍 Adresse", data.get('adresse', 'Non trouvé') or "Non trouvé", help="L'adresse peut nécessiter une vérification manuelle")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab2:
                # En-tête avec icône
                st.markdown("""
                <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.75rem;">
                        <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <h3 style="margin: 0;">Texte brut extrait par OCR</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Zone de texte avec cadre
                st.markdown('<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; background: white;">', unsafe_allow_html=True)
                st.text_area("", st.session_state.extracted_text, height=300, label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Statistiques du texte
                st.markdown("""
                <div style="margin-top: 1.5rem;">
                    <h4 style="color: var(--dark-text); margin-bottom: 1rem;">Statistiques du texte</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                text_stats = {
                    'Nombre de caractères': len(st.session_state.extracted_text),
                    'Nombre de mots': len(st.session_state.extracted_text.split()),
                    'Nombre de lignes': len(st.session_state.extracted_text.split('\n'))
                }
                
                for i, (stat, value) in enumerate(text_stats.items()):
                    with [col1, col2, col3][i]:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric(stat, value)
                        st.markdown('</div>', unsafe_allow_html=True)
            
            with tab3:
                st.markdown('<div class="validation-box">', unsafe_allow_html=True)
                
                # En-tête avec icône
                st.markdown("""
                <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.75rem;">
                        <path d="M12 15V17M12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21ZM12 7V11L15 12" stroke="#ff9800" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <h3 style="margin: 0;">Validation et correction manuelle</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Interface de validation
                data = st.session_state.extracted_data.copy()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    data['numero_reference'] = st.text_input("Numéro de référence", data.get('numero_reference', ''), key="ref_input")
                    data['nom'] = st.text_input("Nom", data.get('nom', ''), key="nom_input")
                    data['prenom'] = st.text_input("Prénom", data.get('prenom', ''), key="prenom_input")
                    data['date'] = st.text_input("Date", data.get('date', ''), key="date_input")
                    data['email'] = st.text_input("Email", data.get('email', ''), key="email_input")
                
                with col2:
                    data['montant'] = st.text_input("Montant", data.get('montant', ''), key="montant_input")
                    data['numero_siret'] = st.text_input("SIRET", data.get('numero_siret', ''), key="siret_input")
                    data['telephone'] = st.text_input("Téléphone", data.get('telephone', ''), key="tel_input")
                    data['adresse'] = st.text_area("Adresse", data.get('adresse', ''), height=100, key="adresse_input")
                
                # Boutons d'action
                st.markdown("""
                <div style="display: flex; justify-content: space-between; margin-top: 2rem;">
                    <div style="flex: 1; margin-right: 1rem;">
                        <button onclick="document.querySelector('.stButton button:nth-of-type(1)').click()" style="width: 100%; background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%); color: white; border: none; border-radius: 8px; padding: 0.75rem; font-weight: 500; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="display: flex; align-items: center; justify-content: center;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                                    <path d="M19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16L21 8V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M17 21V13H7V21" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M7 3V8H15" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                Sauvegarder JSON
                            </div>
                        </button>
                    </div>
                    <div style="flex: 1; margin-right: 1rem;">
                        <button onclick="document.querySelector('.stButton button:nth-of-type(2)').click()" style="width: 100%; background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%); color: white; border: none; border-radius: 8px; padding: 0.75rem; font-weight: 500; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="display: flex; align-items: center; justify-content: center;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                                    <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M7 7H17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M7 11H13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                Sauvegarder CSV
                            </div>
                        </button>
                    </div>
                    <div style="flex: 1;">
                        <button onclick="document.querySelector('.stButton button:nth-of-type(3)').click()" style="width: 100%; background: #f8f9fa; color: var(--dark-text); border: 1px solid #e0e0e0; border-radius: 8px; padding: 0.75rem; font-weight: 500; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <div style="display: flex; align-items: center; justify-content: center;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                                    <path d="M4 12V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V12" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M16 6L12 2L8 6" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M12 2V15" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                Réinitialiser
                            </div>
                        </button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Boutons réels (cachés)
                if st.button("💾 Sauvegarder JSON", key="save_json"):
                    json_data = {
                        'timestamp': datetime.now().isoformat(),
                        'filename': uploaded_file.name,
                        'extracted_data': data,
                        'validation_status': 'validated'
                    }
                    
                    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 Télécharger JSON",
                        data=json_str,
                        file_name=f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_json"
                    )
                
                if st.button("📊 Sauvegarder CSV", key="save_csv"):
                    df = pd.DataFrame([data])
                    csv_str = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv_str,
                        file_name=f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_csv"
                    )
                
                if st.button("🔄 Réinitialiser", key="reset"):
                    for key in ['extracted_text', 'extracted_data']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.experimental_rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Analyse de la qualité
            st.markdown("""
            <div style="margin: 3rem 0 1.5rem 0;">
                <h2 style="color: var(--primary-color);">📈 Analyse de la qualité</h2>
                <p style="color: #666;">Mesure de la performance de l'extraction</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Calcul du score de confiance (simulé)
                confidence_score = min(100, len([v for v in data.values() if v and v != 'Non trouvé']) * 12)
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = confidence_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Score de confiance OCR", 'font': {'size': 16}},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Graphique des champs extraits
                extracted_fields = [k for k, v in data.items() if v and v != 'Non trouvé']
                missing_fields = [k for k, v in data.items() if not v or v == 'Non trouvé']
                
                fig = go.Figure(data=[
                    go.Bar(
                        name='Extraits', 
                        x=['Champs'], 
                        y=[len(extracted_fields)], 
                        marker_color='#4caf50',
                        text=[f"{len(extracted_fields)}/{len(data)} champs"],
                        textposition='auto'
                    ),
                    go.Bar(
                        name='Manquants', 
                        x=['Champs'], 
                        y=[len(missing_fields)], 
                        marker_color='#f44336',
                        text=[f"{len(missing_fields)}/{len(data)} champs"],
                        textposition='auto'
                    )
                ])
                
                fig.update_layout(
                    title='Champs extraits vs manquants',
                    title_font_size=16,
                    barmode='stack',
                    height=300,
                    margin=dict(l=20, r=20, t=60, b=20),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Footer amélioré
    st.markdown("""
    <div style="margin-top: 5rem; padding: 2rem 0; text-align: center; border-top: 1px solid #e0e0e0;">
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 0.5rem;">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 8V12" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 16H12.01" stroke="#2a5298" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h4 style="margin: 0; color: var(--dark-text);">Maquette MOA : Extraction automatisée de données</h4>
        </div>
        <p style="color: #666; margin-bottom: 0.5rem;">Solution de numérisation intelligente pour la DGFiP</p>
        <p style="color: #999; font-size: 0.9rem;">Version 1.0.0 - © 2023 Tous droits réservés</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()