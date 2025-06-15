import os
import streamlit as st
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from rag_system import RAGSystem, load_documents
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="📚 Assistant Documentaire",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    .main { padding: 1rem; }
    .title { color: #1E88E5; }
    .upload-section { 
        background-color: #f8f9fa; 
        padding: 1.5rem; 
        border-radius: 10px; 
        margin-bottom: 1.5rem; 
        border: 1px solid #e0e0e0;
    }
    .chat-container { 
        max-height: 60vh; 
        overflow-y: auto; 
        margin-bottom: 1rem; 
        padding: 1rem; 
        border: 1px solid #e0e0e0; 
        border-radius: 8px; 
        background-color: #fafafa;
    }
    .user-message { 
        background-color: #e3f2fd; 
        padding: 12px 16px; 
        border-radius: 12px; 
        margin: 8px 0; 
        max-width: 80%; 
        margin-left: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .assistant-message { 
        background-color: #f5f5f5; 
        padding: 12px 16px; 
        border-radius: 12px; 
        margin: 8px 0;
        max-width: 80%; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .source-badge { 
        background-color: #e0e0e0; 
        color: #424242; 
        padding: 4px 10px; 
        border-radius: 16px; 
        font-size: 0.8em; 
        margin: 4px 4px 4px 0; 
        display: inline-block;
        font-family: monospace;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        font-weight: 500;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
        padding: 10px 15px;
    }
    .stFileUploader>div>div>div>div>div>div {
        border-radius: 10px;
        border: 2px dashed #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

def init_session():
    """Initialise les variables de session."""
    if 'rag' not in st.session_state:
        st.session_state.rag = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False

# Initialisation de la session
init_session()

def display_chat():
    """Affiche l'historique de la conversation."""
    if 'messages' in st.session_state and st.session_state.messages:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Afficher les sources si elles existent
                if message.get("sources"):
                    st.caption("Sources utilisées :")
                    cols = st.columns(4)
                    for i, source in enumerate(message["sources"][:4]):  # Limiter à 4 sources
                        with cols[i % 4]:
                            st.code(source.split('/')[-1], help=source)

def main():
    # En-tête de l'application
    st.title("📚 Assistant Documentaire")
    st.markdown("Posez des questions sur vos documents PDF et obtenez des réponses précises basées sur leur contenu.")
    st.markdown("---")
    
    # Barre latérale pour le téléchargement des documents
    with st.sidebar:
        st.header("📂 Gestion des documents")
        
        # Section de téléchargement
        with st.expander("📤 Téléverser des documents", expanded=not st.session_state.documents_loaded):
            uploaded_files = st.file_uploader(
                "Sélectionnez un ou plusieurs fichiers PDF",
                type=["pdf"],
                accept_multiple_files=True,
                key="file_uploader"
            )
            
            if st.button("Charger les documents", key="load_btn", 
                        disabled=len(uploaded_files) == 0 or st.session_state.documents_loaded):
                with st.spinner("Traitement des documents en cours..."):
                    try:
                        # Initialisation du système RAG
                        api_key = os.getenv("OPENAI_API_KEY")
                        if not api_key:
                            st.error("Clé API OpenAI non trouvée. Veuillez la définir dans le fichier .env")
                            return
                            
                        st.session_state.rag = RAGSystem(api_key=api_key)
                        
                        # Créer un répertoire temporaire pour les fichiers téléchargés
                        temp_dir = Path("temp_uploads")
                        temp_dir.mkdir(exist_ok=True)
                        
                        # Enregistrer et traiter chaque fichier
                        loaded_count = 0
                        for uploaded_file in uploaded_files:
                            temp_path = temp_dir / uploaded_file.name
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            if st.session_state.rag.add_document(str(temp_path)):
                                loaded_count += 1
                        
                        # Nettoyer les fichiers temporaires
                        for temp_file in temp_dir.glob("*"):
                            temp_file.unlink()
                        temp_dir.rmdir()
                        
                        if loaded_count > 0:
                            st.session_state.documents_loaded = True
                            st.session_state.messages = [{
                                "role": "assistant", 
                                "content": f"✅ {loaded_count} document(s) chargé(s) avec succès ! Posez-moi vos questions.",
                                "sources": []
                            }]
                            st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erreur lors du chargement des documents: {str(e)}")
        
        # Section d'information
        st.markdown("---")
        st.markdown("### 📝 Comment utiliser")
        st.markdown("""
        1. Téléversez un ou plusieurs fichiers PDF
        2. Cliquez sur "Charger les documents"
        3. Posez vos questions dans la zone de chat
        4. Consultez les sources utilisées pour les réponses
        """)
        
        st.markdown("---")
        st.markdown("### ⚙️ Paramètres")
        if st.button("Réinitialiser la conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Affichage de la conversation
    if st.session_state.documents_loaded:
        display_chat()
        
        # Zone de saisie de la question
        if prompt := st.chat_input("Posez votre question ici..."):
            # Ajouter le message de l'utilisateur
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Afficher le message de l'utilisateur
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Afficher un indicateur de chargement
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("▌")
                
                try:
                    # Obtenir la réponse du système RAG
                    response = st.session_state.rag.query(prompt)
                    
                    # Afficher la réponse
                    message_placeholder.markdown(response["answer"])
                    
                    # Ajouter la réponse à l'historique
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "sources": response["sources"]
                    })
                    
                    # Afficher les sources
                    if response["sources"]:
                        st.caption("Sources utilisées :")
                        cols = st.columns(4)
                        for i, source in enumerate(response["sources"][:4]):  # Limiter à 4 sources
                            with cols[i % 4]:
                                st.code(source.split('/')[-1], help=source)
                    
                except Exception as e:
                    error_msg = f"Désolé, une erreur est survenue: {str(e)}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })
    else:
        # Message d'accueil si aucun document n'est chargé
        st.info("Veuillez d'abord téléverser et charger des documents PDF dans la barre latérale pour commencer.")
        
        # Section de démonstration
        st.markdown("### Exemple de questions à poser :")
        st.markdown("""
        - Quel est le thème principal de ce document ?
        - Résumez le contenu en quelques points clés.
        - Quelles sont les conclusions principales ?
        - Pouvez-vous expliquer [concept] mentionné dans le document ?
        """)

if __name__ == "__main__":
    main()
