#!/bin/bash
set -e

echo "🚀 Setting up Car Defect Detection Platform..."

# Python Backend Setup
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "🐍 Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Frontend Setup
echo "🍞 Installing Frontend dependencies (Bun)..."
cd frontend
bun install

echo "🏗️ Building Frontend for production..."
bun run build
cd ..

echo "✅ Setup complete! Run ./start.sh to launch the application."
