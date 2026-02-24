#!/bin/bash
# Wrapper script to download bank documents
# Usage: ./download-bank-docs.sh "Bank Name" [starting-url]

BANK_NAME="$1"
STARTING_URL="$2"

if [ -z "$BANK_NAME" ]; then
    echo "❌ Error: Bank name required"
    echo "Usage: ./download-bank-docs.sh 'Bank Name' [starting-url]"
    exit 1
fi

echo "🏦 Downloading documents from: $BANK_NAME"
echo ""

# Set Chrome endpoint
export CHROME_CDP_ENDPOINT="http://localhost:9222"

# Run the downloader
cd ~/.openclaw/workspace
node bank-document-downloader.js "$BANK_NAME" "$STARTING_URL"
