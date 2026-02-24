#!/bin/bash
# Launch Chrome with remote debugging for bank document downloads

echo "🚀 Launching Chrome with remote debugging enabled..."
echo ""
echo "📝 What this does:"
echo "  • Opens Chrome on port 9222 (allows me to control it)"
echo "  • Uses separate profile (won't affect your main Chrome)"
echo "  • You handle all logins and 2FA"
echo ""
echo "👉 Next steps:"
echo "  1. Login to your bank in the Chrome window that opens"
echo "  2. Navigate to Statements/Documents/Tax Forms page"
echo "  3. Tell me: 'Ready to download from [Bank Name]'"
echo ""
echo "Press Ctrl+C to stop Chrome when done."
echo ""

# Set Chrome debugging port
export CHROME_CDP_ENDPOINT="http://localhost:9222"

# Launch Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-automation" \
  --no-first-run \
  --no-default-browser-check \
  2>/dev/null &

CHROME_PID=$!
echo "✅ Chrome launched (PID: $CHROME_PID)"
echo "🔌 Remote debugging on: http://localhost:9222"
echo ""
echo "When you're done with all banks, run: kill $CHROME_PID"
