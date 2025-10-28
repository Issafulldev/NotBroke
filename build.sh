#!/bin/bash
set -e

echo "🚀 Starting frontend build..."
echo "📁 Current directory: $(pwd)"

# Navigate to frontend directory
cd frontend

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
