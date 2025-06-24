#!/bin/bash

echo "🔄 Starting live Docker logs for RAG app..."
echo "📍 URL: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop"
echo ""

docker logs chat-with-your-documents-rag-app-1 -f --timestamps | \
    while IFS= read -r line; do
        if [[ $line == *"🔐"* ]]; then
            echo -e "\033[32m$line\033[0m"
        elif [[ $line == *"❌"* ]]; then
            echo -e "\033[31m$line\033[0m"
        elif [[ $line == *"✅"* ]]; then
            echo -e "\033[32m$line\033[0m"
        elif [[ $line == *"📊"* ]]; then
            echo -e "\033[34m$line\033[0m"
        elif [[ $line == *"ERROR"* ]] || [[ $line == *"FATAL"* ]]; then
            echo -e "\033[31m$line\033[0m"  # Rouge pour erreurs
        else
            echo "$line"
        fi
    done
