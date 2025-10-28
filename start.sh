#!/bin/bash
set -e

echo "🚀 Starting NotBroke Frontend..."
echo "📁 Current directory: $(pwd)"

# Navigate to frontend directory
cd frontend

if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend!"
    exit 1
fi

echo "✅ Found package.json"

# Use PORT from environment or default to 3000
PORT=${PORT:-3000}
echo "🌐 Starting frontend on port $PORT..."

npm start
