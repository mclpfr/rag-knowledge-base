import os
from pathlib import Path
from typing import List, Dict, Any
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Document:
    """Classe pour représenter un document avec son contenu et ses métadonnées."""
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata or {}

class RAGSystem:
    """Système RAG pour l'indexation et la recherche de documents."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", api_key: str = None):
        """Initialise le système RAG avec un modèle d'embedding."""
        # Charger les variables d'environnement
        load_dotenv()
        
        # Configuration du modèle d'embedding
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialisation de ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_name
            )
        )
        
        # Configuration de l'API OpenAI
        self.openai_client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model_name = "gpt-3.5-turbo"
        
        logger.info("Système RAG initialisé avec succès")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extrait le texte d'un fichier PDF."""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF: {str(e)}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Découpe le texte en chunks avec chevauchement."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    
    def add_document(self, file_path: str, metadata: Dict[str, Any] = None):
        """Ajoute un document à la base de connaissances."""
        if metadata is None:
            metadata = {}
            
        try:
            logger.info(f"Traitement du document: {file_path}")
            
            # Extraction et prétraitement
            text = self.extract_text_from_pdf(file_path)
            chunks = self.chunk_text(text)
            
            # Préparation des métadonnées
            doc_metadata = {
                "source": str(Path(file_path).name),
                "type": "pdf",
                **metadata
            }
            
            # Ajout à la base vectorielle
            ids = [f"{Path(file_path).stem}_{i}" for i in range(len(chunks))]
            metadatas = [{**doc_metadata, "chunk_id": i} for i in range(len(chunks))]
            
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Document ajouté avec succès: {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du document: {str(e)}")
            return False
    
    def query(self, question: str, top_k: int = 3) -> Dict:
        """Interroge le système RAG avec une question."""
        try:
            logger.info(f"Recherche de réponses pour: {question}")
            
            # Recherche des documents pertinents
            results = self.collection.query(
                query_texts=[question],
                n_results=top_k
            )
            
            if not results['documents'] or not results['documents'][0]:
                return {
                    "answer": "Aucune information pertinente trouvée dans les documents.",
                    "sources": []
                }
            
            # Construction du contexte
            context = "\n\n".join([
                f"Extrait {i+1} (Source: {m['source']}):\n{doc}"
                for i, (doc, m) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0]
                ))
            ])
            
            # Génération de la réponse
            response = self._generate_response(question, context)
            
            # Extraction des sources uniques
            sources = list(set([m["source"] for m in results['metadatas'][0]]))
            
            return {
                "answer": response,
                "sources": sources
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            logger.error(error_msg)
            return {
                "answer": f"Désolé, une erreur est survenue: {str(e)}",
                "sources": []
            }
    
    def _generate_response(self, question: str, context: str) -> str:
        """Génère une réponse à partir du contexte en utilisant l'API OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """Tu es un assistant expert qui répond aux questions en te basant sur le contexte fourni. 
                        Réponds de manière claire et concise. 
                        Si tu ne connais pas la réponse, dis-le clairement."""
                    },
                    {
                        "role": "user",
                        "content": f"""Contexte:
                        {context}
                        
                        Question: {question}
                        
                        Réponse:"""
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")
            return f"Désolé, je n'ai pas pu générer de réponse. Erreur: {str(e)}"

# Fonction utilitaire pour charger plusieurs documents
def load_documents(directory: str, rag_system: RAGSystem):
    """Charge tous les PDF d'un répertoire dans le système RAG."""
    directory = Path(directory)
    if not directory.exists():
        logger.error(f"Le répertoire {directory} n'existe pas.")
        return []
    
    loaded_files = []
    for file_path in directory.glob("*.pdf"):
        try:
            success = rag_system.add_document(str(file_path))
            if success:
                loaded_files.append(file_path.name)
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {file_path}: {str(e)}")
    
    return loaded_files
