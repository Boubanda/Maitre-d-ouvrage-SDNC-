# 🧩 Maquette MOA : Extraction automatisée de données

## 🎯 Objectif

Cette application Streamlit démontre une chaîne complète de numérisation et d'extraction intelligente de données à partir de documents numérisés (PDF ou images). Elle simule un workflow qui pourrait être intégré dans un système de gestion documentaire comme celui de la DGFiP.

## ✨ Fonctionnalités

### 📤 Téléversement de documents
- Support des formats PDF, PNG, JPG, JPEG, TIFF, BMP
- Aperçu immédiat du document téléversé
- Validation des formats et tailles

### 🔍 OCR et reconnaissance de texte
- Extraction automatique du texte avec Tesseract OCR
- Support du français avec configuration optimisée
- Traitement différencié PDF vs images

### 🧠 Extraction intelligente de données
- Reconnaissance automatique des champs clés :
  - Numéro de référence
  - Nom et prénom
  - Dates
  - Montants
  - Numéro SIRET
  - Coordonnées (adresse, téléphone, email)
- Utilisation de patterns regex optimisés

### ✅ Validation et correction manuelle
- Interface de validation intuitive
- Correction manuelle des données extraites
- Sauvegarde en JSON ou CSV

### 📊 Analyse de qualité
- Score de confiance OCR
- Visualisation des champs extraits/manquants
- Statistiques sur le texte extrait

### 🔄 Workflow visualisé
- Représentation graphique du processus
- Suivi des étapes en temps réel
- Interface claire et professionnelle

## 🛠️ Stack technique

- **Frontend** : Streamlit avec CSS personnalisé
- **OCR** : Tesseract OCR avec support français
- **PDF** : PyMuPDF pour l'extraction et conversion
- **Images** : Pillow pour le traitement d'images
- **Visualisation** : Plotly pour les graphiques interactifs
- **Traitement** : Pandas pour la manipulation de données
- **Expressions régulières** : Regex pour l'extraction structurée

## 📦 Installation

### Prérequis
- Python 3.9+
- Docker (optionnel)
- Tesseract OCR

### Installation locale

1. **Cloner le repository**
```bash
git clone <repository-url>
cd ocr-extraction-app
```

2. **Installer les dépendances système**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-fra

# macOS
brew install tesseract tesseract-lang

# Windows
# Télécharger depuis https://github.com/UB-Mannheim/tesseract/wiki
```

3. **Installer les dépendances Python**
```bash
pip install -r requirements.txt
```

4. **Lancer l'application**
```bash
streamlit run app.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

### Installation avec Docker

1. **Build et lancement**
```bash
docker-compose up --build
```

2. **Accès à l'application**
```
http://localhost:8501
```

## 🚀 Utilisation

### 1. Téléverser un document
- Cliquez sur "Sélectionnez un fichier PDF ou image"
- Choisissez votre document (PDF, image)
- Visualisez l'aperçu

### 2. Lancer l'extraction
- Cliquez sur "🧠 Lancer l'OCR et l'extraction"
- Attendez la fin du traitement
- Consultez les résultats dans les différents onglets

### 3. Valider les données
- Onglet "Validation" : corrigez manuellement les erreurs
- Sauvegardez en JSON ou CSV
- Analysez la qualité de l'extraction

## 📊 Métriques et monitoring

### Indicateurs de performance
- Score de confiance OCR (0-100%)
- Nombre de champs extraits vs manquants
- Statistiques textuelles (caractères, mots, lignes)

### Visualisations
- Workflow en temps réel
- Graphiques de qualité
- Métriques de performance

## 🔧 Configuration

### Tesseract OCR
- Langue : Français (fra)
- Mode OCR : OEM 3 (LSTM + Legacy)
- Segmentation : PSM 6 (Bloc de texte uniforme)

### Patterns d'extraction
Les patterns regex sont optimisés pour reconnaître :
- Références alphanumériques
- Noms et prénoms français
- Dates aux formats DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
- Montants avec séparateurs français
- Numéros SIRET (14 chiffres)
- Emails et téléphones

## 🎨 Interface utilisateur

### Design system
- Palette de couleurs professionnelle
- Composants réutilisables
- Responsive design
- Animations de progression

### Expérience utilisateur
- Workflow guidé étape par étape
- Feedback visuel constant
- Validation en temps réel
- Exports mult