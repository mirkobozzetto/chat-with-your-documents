# src/document_selection_persistence.py
import json
import os
from pathlib import Path
from typing import Optional


class DocumentSelectionPersistence:

    def __init__(self, storage_file: str = "last_document_selection.json"):
        self.storage_file = Path(storage_file)

    def save_selection(self, document_name: Optional[str]) -> None:
        data = {"selected_document": document_name}

        try:
            with open(self.storage_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Warning: Could not save document selection: {e}")

    def load_selection(self) -> Optional[str]:
        if not self.storage_file.exists():
            return None

        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                return data.get("selected_document")
        except Exception as e:
            print(f"Warning: Could not load document selection: {e}")
            return None

    def clear_selection(self) -> None:
        self.save_selection(None)
