#!/bin/bash

set -e

mkdir -p chat_history/conversations
mkdir -p chroma_db

if [ ! -f agent_configs.json ]; then
    echo "{}" > agent_configs.json
fi

if [ ! -f auth_users.json ]; then
    echo "{}" > auth_users.json
fi

if [ ! -f chat_history/index.json ]; then
    echo "{\"conversations\": {}}" > chat_history/index.json
fi

exec "$@"
