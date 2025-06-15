# 📚 Assistant Documentaire IA

Un système RAG (Retrieval-Augmented Generation) pour interroger des documents PDF en langage naturel.

## 🚀 Fonctionnalités

- Téléversement de documents PDF multiples
- Indexation et recherche sémantique
- Réponses précises basées sur le contenu des documents
- Visualisation des sources utilisées
- Interface utilisateur intuitive avec Streamlit

## 🛠 Installation

1. **Cloner le dépôt**
   ```bash
   git clone [URL_DU_REPO]
   cd rag-knowledge-base
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # ou
   .\venv\Scripts\activate  # Sur Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   Copiez le fichier `.env.example` vers `.env` et configurez vos clés API :
   ```bash
   cp .env.example .env
   # Éditez le fichier .env pour y ajouter votre clé API
   ```

## 🚀 Utilisation

1. **Lancer l'application**
   ```bash
   streamlit run app.py
   ```

2. **Dans votre navigateur**
   - Accédez à l'interface à l'adresse indiquée (généralement http://localhost:8501)
   - Téléversez vos documents PDF via l'interface
   - Posez vos questions en langage naturel

## 📂 Structure du projet

```
.
├── app.py              # Application Streamlit
├── rag_system.py       # Cœur du système RAG
├── requirements.txt    # Dépendances
├── .env               # Configuration (à créer)
└── chroma_db/         # Base de données vectorielle (créée automatiquement)
```

## 🔒 Sécurité

- Ne partagez jamais votre clé API
- Le fichier `.env` est inclus dans `.gitignore` par défaut
- Les documents téléversés sont stockés temporairement pendant la session

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙋 Support

Pour toute question ou problème, veuillez ouvrir une issue sur le dépôt.