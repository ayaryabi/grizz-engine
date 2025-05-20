#!/bin/bash
# Start LLM worker

# Load environment variables from .env file if present
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# Set worker ID if not already set
if [ -z "$WORKER_ID" ]; then
  export WORKER_ID="worker-$(uuidgen | tr -d '-' | tr '[:upper:]' '[:lower:]')"
fi

echo "Starting LLM worker with ID: $WORKER_ID"
python -m app.workers.llm_worker 