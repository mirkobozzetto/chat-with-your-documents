# src/vector_stores/collection_name_manager.py
import re
import unicodedata
from pathlib import Path
from typing import Set


class CollectionNameManager:
    """
    Single Responsibility: Generate and validate Qdrant collection names
    following the pattern rag_{clean_document_name}
    """
    
    RAG_PREFIX = "rag_"
    MAX_COLLECTION_NAME_LENGTH = 63  # Qdrant limit
    
    @classmethod
    def generate_collection_name(cls, document_filename: str) -> str:
        """
        Generate a clean collection name from a document filename
        
        Args:
            document_filename: Original filename (e.g., "temp_nietzsche_le_gai_savoir.pdf")
            
        Returns:
            Clean collection name (e.g., "rag_temp_nietzsche_le_gai_savoir")
        """
        # Extract base name without extension
        base_name = Path(document_filename).stem
        
        # Clean the name
        clean_name = cls._clean_document_name(base_name)
        
        # Build collection name
        collection_name = f"{cls.RAG_PREFIX}{clean_name}"
        
        # Ensure it fits within limits
        if len(collection_name) > cls.MAX_COLLECTION_NAME_LENGTH:
            # Truncate while keeping the prefix
            max_suffix_length = cls.MAX_COLLECTION_NAME_LENGTH - len(cls.RAG_PREFIX)
            clean_name = clean_name[:max_suffix_length]
            collection_name = f"{cls.RAG_PREFIX}{clean_name}"
        
        return collection_name
    
    @classmethod
    def _clean_document_name(cls, name: str) -> str:
        """
        Clean document name for use in collection name
        
        Rules:
        - Lowercase
        - Replace spaces and special chars with underscores
        - Remove accents
        - Only alphanumeric and underscores
        - Remove consecutive underscores
        """
        # Normalize unicode (remove accents)
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        
        # Convert to lowercase
        name = name.lower()
        
        # Replace non-alphanumeric chars with underscores
        name = re.sub(r'[^a-z0-9_]', '_', name)
        
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # Ensure not empty
        if not name:
            name = "document"
        
        return name
    
    @classmethod
    def extract_document_name_from_collection(cls, collection_name: str) -> str:
        """
        Extract original document name from collection name
        
        Args:
            collection_name: Collection name (e.g., "rag_temp_nietzsche_le_gai_savoir")
            
        Returns:
            Document name (e.g., "temp_nietzsche_le_gai_savoir")
        """
        if collection_name.startswith(cls.RAG_PREFIX):
            return collection_name[len(cls.RAG_PREFIX):]
        return collection_name
    
    @classmethod
    def is_rag_collection(cls, collection_name: str) -> bool:
        """Check if collection name follows RAG pattern"""
        return collection_name.startswith(cls.RAG_PREFIX)
    
    @classmethod
    def validate_collection_name(cls, collection_name: str) -> bool:
        """
        Validate that a collection name is valid for Qdrant
        
        Args:
            collection_name: Name to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check length
        if len(collection_name) > cls.MAX_COLLECTION_NAME_LENGTH:
            return False
        
        # Check pattern (alphanumeric + underscores, must start with letter or underscore)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', collection_name):
            return False
        
        return True
    
    @classmethod
    def get_all_rag_collections(cls, all_collections: Set[str]) -> Set[str]:
        """
        Filter collections to only return RAG collections
        
        Args:
            all_collections: Set of all collection names
            
        Returns:
            Set of RAG collection names only
        """
        return {col for col in all_collections if cls.is_rag_collection(col)}