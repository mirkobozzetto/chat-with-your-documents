#!/usr/bin/env python3
"""
Command-line interface for the RAG system.
Usage: python cli.py <pdf_path>
"""

import sys
import os
from rag_system import OptimizedRAGSystem


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py <pdf_path>")
        print("       python3 cli.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    print("Initializing RAG system...")
    rag = OptimizedRAGSystem()

    print(f"Processing PDF: {pdf_path}")
    rag.process_pdf(pdf_path)

    print("\nPDF processed successfully!")
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
