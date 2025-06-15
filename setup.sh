#!/bin/bash

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Créer un environnement virtuel
echo "Création de l'environnement virtuel..."
python3 -m venv venv

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo "Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Vérifier la présence du fichier .env
if [ ! -f ".env" ]; then
    echo "Création du fichier .env..."
    cp .env.example .env
    echo "Veuvez configurer votre clé API dans le fichier .env"
fi

echo "Installation terminée !"
echo "Pour démarrer l'application, exécutez :"
echo "source venv/bin/activate && streamlit run app.py"
