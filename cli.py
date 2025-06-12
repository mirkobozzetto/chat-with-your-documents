#!/usr/bin/env python3
"""
Usage: python cli.py <document_path>
"""

import sys
import os
from rag_system import OptimizedRAGSystem


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py <document_path>")
        print("       python3 cli.py <document_path>")
        print("Supported formats: PDF, DOCX, TXT, MD")
        sys.exit(1)

    document_path = sys.argv[1]

    if not os.path.exists(document_path):
        print(f"Error: Document file not found: {document_path}")
        sys.exit(1)

    print("Initializing RAG system...")
    rag = OptimizedRAGSystem()

    print(f"Processing document: {document_path}")
    rag.process_pdf(document_path)

    print("\nDocument processed successfully!")
    print("You can now ask questions. Type 'quit' to exit.\n")

    while True:
        question = input("Your question: ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            break

        if not question:
            continue

        try:
            result = rag.ask_question(question)
            print(f"\nAnswer: {result['result']}")
            print(f"\nSources used: {len(result['source_documents'])} chunks")
            print("-" * 50)
        except Exception as e:
            print(f"Error: {str(e)}")

    print("Goodbye!")


if __name__ == "__main__":
    main()
