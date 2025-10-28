#!/bin/bash
set -e

echo "🚀 Starting frontend build with submodule initialization..."
echo "📁 Current directory: $(pwd)"

# Initialize and update git submodules
echo "📦 Initializing git submodules..."
git submodule init
git submodule update --init --recursive

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found even after submodule init!"
    exit 1
fi

echo "✅ Frontend submodule initialized"
echo "📁 Entering frontend directory..."
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
