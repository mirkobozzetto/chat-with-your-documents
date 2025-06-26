# src/vector_stores/batch_processor.py
from typing import List, Optional, Callable, Any, TypeVar, Generic
from langchain.schema import Document

T = TypeVar('T')

class BatchProcessor(Generic[T]):
    """Handles batch processing with progress callbacks for vector store operations"""
    
    def __init__(self, batch_size: int = 50, progress_start: float = 0.9):
        self.batch_size = batch_size
        self.progress_start = progress_start
    
    def process_batches(
        self,
        items: List[T], 
        processor_func: Callable[[List[T], int, int], None],
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> None:
        """
        Process items in batches with progress tracking
        
        Args:
            items: List of items to process
            processor_func: Function to process each batch (batch, batch_num, total_batches)
            progress_callback: Optional progress callback
        """
        if not items:
            return
            
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            print(f"📦 Processing batch {batch_num}/{total_batches}")
            
            # Process the batch
            processor_func(batch, batch_num, total_batches)
            
            # Update progress
            if progress_callback:
                progress = self.progress_start + (batch_num / total_batches) * (1.0 - self.progress_start)
                progress_callback(progress, f"Batch {batch_num}/{total_batches}")

class VectorStoreErrorHandler:
    """Centralized error handling for vector store operations"""
    
    @staticmethod
    def handle_document_operation_error(
        operation: str, 
        document_filename: str, 
        error: Exception,
        return_value: Any = False
    ) -> Any:
        """Handle errors in document operations with consistent logging"""
        print(f"❌ Error {operation} document {document_filename}: {str(error)}")
        return return_value
    
    @staticmethod
    def handle_general_operation_error(
        operation: str,
        error: Exception,
        return_value: Any = None
    ) -> Any:
        """Handle general operation errors with consistent logging"""
        print(f"⚠️ Error {operation}: {str(error)}")
        return return_value