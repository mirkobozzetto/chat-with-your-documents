# 🤖 RAG AI Assistant - Chat with your documents

Un système RAG (Retrieval-Augmented Generation) moderne utilisant OpenAI pour les embeddings et le chat, avec une interface Streamlit intuitive.

## ✨ Fonctionnalités

- **Upload PDF** : Traitement automatique des documents PDF
- **Chunking intelligent** : Découpage optimisé des documents
- **Embeddings OpenAI** : Utilise `text-embedding-3-small` pour la vectorisation
- **Chat GPT-4** : Réponses générées par `gpt-4o-mini`
- **Interface web** : Interface Streamlit moderne et responsive
- **Vector Store local** : Base ChromaDB persistante
- **Sources citées** : Affichage des passages utilisés pour les réponses

## 🚀 Installation

1. **Cloner et installer les dépendances :**

```bash
pip install -r requirements.txt
```

2. **Configurer OpenAI API :**

```bash
# Créer un fichier .env
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## 💻 Utilisation

### Interface Web (Recommandée)

```bash
streamlit run app.py
```

### Ligne de commande

```bash
python cli_demo.py path/to/your/document.pdf
```

## 🛠️ Architecture

```
rag-ai/
├── app.py              # Interface Streamlit
├── rag_system.py       # Système RAG principal
├── config.py           # Configuration
├── cli_demo.py         # Demo ligne de commande
├── requirements.txt    # Dépendances
└── chroma_db/         # Base vectorielle (auto-créée)
```

## 📦 Stack Technique

- **LangChain** : Framework RAG
- **OpenAI** : Embeddings + Chat
- **ChromaDB** : Vector store local
- **Streamlit** : Interface web
- **Unstructured** : Parser PDF avancé

## ⚙️ Configuration

Le fichier `config.py` permet de personnaliser :

- Modèles OpenAI (`EMBEDDING_MODEL`, `CHAT_MODEL`)
- Paramètres de chunking (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
- Répertoire de la base vectorielle

## 🎯 Usage Rapide

1. Lancer l'app : `streamlit run app.py`
2. Uploader un PDF dans la sidebar
3. Cliquer "Process PDF"
4. Poser des questions dans le chat

## 🔧 Dépendances Principales

- `langchain>=0.1.0` : Framework RAG
- `langchain-openai>=0.1.0` : Intégration OpenAI
- `chromadb>=0.4.0` : Vector database
- `streamlit>=1.31.0` : Interface web
- `unstructured[pdf]>=0.12.0` : Parser PDF
