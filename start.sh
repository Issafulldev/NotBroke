#!/bin/bash
set -e

echo "🚀 Starting NotBroke Frontend..."
echo "📁 Current directory: $(pwd)"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found!"
    echo "📍 Looking in parent directories..."
    if [ -d "../frontend" ]; then
        cd ..
    else
        echo "❌ Cannot find frontend directory!"
        exit 1
    fi
fi

echo "✅ Found frontend directory"
echo "📁 Entering frontend directory..."
cd frontend

# Check for package.json
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend!"
    exit 1
fi

# Use PORT from environment or default to 3000
PORT=${PORT:-3000}
echo "🌐 Starting frontend on port $PORT..."

npm start
