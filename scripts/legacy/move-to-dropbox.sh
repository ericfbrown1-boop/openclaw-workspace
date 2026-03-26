#!/bin/bash
# Move folder/file to Jarvis Dropbox and create local symlink
# Usage: move-to-dropbox.sh <local_path> <dropbox_path>

set -e

if [ $# -lt 2 ]; then
    echo "Usage: move-to-dropbox.sh <local_path> <dropbox_path>"
    echo "Example: move-to-dropbox.sh ~/ProjectScraper/Rubrik /ProjectScraper/Rubrik"
    exit 1
fi

LOCAL_PATH="$1"
DROPBOX_PATH="$2"
DROPBOX_CLI=~/.openclaw/workspace/dropbox-cli.py

if [ ! -e "$LOCAL_PATH" ]; then
    echo "Error: $LOCAL_PATH does not exist"
    exit 1
fi

echo "📦 Moving $LOCAL_PATH to Dropbox at $DROPBOX_PATH"

# If it's a directory, tar it first
if [ -d "$LOCAL_PATH" ]; then
    echo "📁 Directory detected, creating tarball..."
    TARBALL="${LOCAL_PATH}.tar.gz"
    tar -czf "$TARBALL" -C "$(dirname "$LOCAL_PATH")" "$(basename "$LOCAL_PATH")"
    
    echo "⬆️  Uploading tarball to Dropbox..."
    python3 "$DROPBOX_CLI" upload "$TARBALL" "${DROPBOX_PATH}.tar.gz"
    
    echo "🗑️  Removing local tarball..."
    rm "$TARBALL"
    
    echo "✅ Directory moved to Dropbox"
    echo "   Dropbox path: ${DROPBOX_PATH}.tar.gz"
    echo ""
    echo "To restore: python3 $DROPBOX_CLI download ${DROPBOX_PATH}.tar.gz && tar -xzf $(basename ${DROPBOX_PATH}).tar.gz"
    
elif [ -f "$LOCAL_PATH" ]; then
    echo "📄 File detected, uploading..."
    python3 "$DROPBOX_CLI" upload "$LOCAL_PATH" "$DROPBOX_PATH"
    
    echo "✅ File moved to Dropbox"
    echo "   Dropbox path: $DROPBOX_PATH"
fi

echo ""
echo "💾 Local storage freed: $(du -sh "$LOCAL_PATH" | cut -f1)"
echo ""
read -p "Delete local copy? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$LOCAL_PATH"
    echo "🗑️  Local copy deleted"
else
    echo "✋ Local copy preserved"
fi
