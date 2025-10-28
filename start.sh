#!/bin/bash
set -e

echo "🚀 Starting NotBroke Frontend..."
echo "📁 Current directory: $(pwd)"
echo "📋 Directory listing:"
ls -la | head -20

# Find the actual root where frontend exists
FRONTEND_DIR=""

# Try common locations
if [ -d "./frontend" ] && [ -f "./frontend/package.json" ]; then
    FRONTEND_DIR="./frontend"
elif [ -d "../frontend" ] && [ -f "../frontend/package.json" ]; then
    FRONTEND_DIR="../frontend"
elif [ -d "../../frontend" ] && [ -f "../../frontend/package.json" ]; then
    FRONTEND_DIR="../../frontend"
else
    # Last resort: find it anywhere
    FOUND=$(find / -maxdepth 5 -name "package.json" -path "*/frontend/package.json" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        FRONTEND_DIR=$(dirname "$FOUND")
    fi
fi

if [ -z "$FRONTEND_DIR" ]; then
    echo "❌ Error: Cannot find frontend directory with package.json!"
    exit 1
fi

echo "✅ Found frontend at: $FRONTEND_DIR"
cd "$FRONTEND_DIR"

echo "✅ In directory: $(pwd)"
ls -la | head -10

# Use PORT from environment or default to 3000
PORT=${PORT:-3000}
echo "🌐 Starting frontend on port $PORT..."

npm start
