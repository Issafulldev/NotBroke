#!/bin/bash
set -e

echo "🚀 Starting frontend build..."
echo "📁 Current directory: $(pwd)"

# Navigate to the project root if we're not already there
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    echo "Looking for frontend in parent directories..."
    if [ -d "../frontend" ]; then
        cd ..
    else
        echo "❌ Cannot find frontend directory!"
        exit 1
    fi
fi

echo "✅ Found frontend directory at: $(pwd)/frontend"
cd frontend

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building application..."
npm run build

echo "✅ Frontend build completed successfully!"
