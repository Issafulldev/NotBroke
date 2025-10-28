#!/bin/bash
set -e

echo "🚀 Starting frontend build..."
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

echo "✅ Found frontend directory at: $(pwd)/frontend"
cd frontend

# Check for package.json
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend!"
    exit 1
fi

echo "✅ Found package.json"
echo "📦 Installing dependencies..."
npm install

echo "🔨 Building application..."
npm run build

echo "✅ Frontend build completed successfully!"
