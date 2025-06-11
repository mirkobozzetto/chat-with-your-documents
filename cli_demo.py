#!/usr/bin/env python3
"""
Command-line demo for the RAG system.
Usage: python cli_demo.py <pdf_path>
"""

import sys
import os
from rag_system import RAGSystem


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli_demo.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    print("🤖 Initializing RAG system...")
    rag = RAGSystem()

    print(f"📄 Processing PDF: {pdf_path}")
    rag.process_pdf(pdf_path)

    print("\n✅ PDF processed successfully!")
    print("You can now ask questions. Type 'quit' to exit.\n")

    while True:
        question = input("❓ Your question: ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break

        if not question:
            continue

        print("\n🤔 Thinking...")
        result = rag.query(question)

        print(f"\n💡 Answer:")
        print(result["answer"])

        print(f"\n📚 Sources ({len(result['source_documents'])} documents):")
        for i, doc in enumerate(result["source_documents"], 1):
            preview = doc.page_content[:150].replace('\n', ' ')
            print(f"  {i}. {preview}...")

        print("\n" + "-"*50 + "\n")


if __name__ == "__main__":
    main()
