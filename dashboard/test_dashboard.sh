#!/bin/bash

echo "🚀 Testing ARCH-FL Dashboard Setup"
echo "=================================="
echo ""

# Check if we're in the dashboard directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Please run this script from the dashboard directory"
    exit 1
fi

echo "✅ Dashboard directory structure verified"
echo ""

# Test backend
cd backend || exit
echo "🔧 Testing backend..."

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 is available"
else
    echo "❌ Python 3 is required but not found"
    cd ..
    exit 1
fi

# Check backend requirements
if [ -f "requirements.txt" ]; then
    echo "✅ Backend requirements file found"
else
    echo "❌ Backend requirements.txt not found"
    cd ..
    exit 1
fi

# Test FastAPI main file
if [ -f "main.py" ]; then
    echo "✅ Backend main.py found"
    
    # Check if FastAPI imports work
    if python3 -c "import fastapi; print('FastAPI available')" 2>/dev/null; then
        echo "✅ FastAPI is installed"
    else
        echo "⚠️  FastAPI not installed. You may need to run: pip install -r requirements.txt"
    fi
else
    echo "❌ Backend main.py not found"
    cd ..
    exit 1
fi

cd .. || exit
echo ""

# Test frontend
cd frontend || exit
echo "🔧 Testing frontend..."

# Check if Node.js is available
if command -v node &> /dev/null; then
    echo "✅ Node.js is available"
    NODE_VERSION=$(node -v)
    echo "   Node version: $NODE_VERSION"
else
    echo "❌ Node.js is required but not found"
    cd ..
    exit 1
fi

# Check if npm is available
if command -v npm &> /dev/null; then
    echo "✅ npm is available"
else
    echo "❌ npm is required but not found"
    cd ..
    exit 1
fi

# Check package.json
if [ -f "package.json" ]; then
    echo "✅ Frontend package.json found"
else
    echo "❌ Frontend package.json not found"
    cd ..
    exit 1
fi

# Check vite config
if [ -f "vite.config.js" ]; then
    echo "✅ Vite configuration found"
else
    echo "❌ Vite configuration not found"
    cd ..
    exit 1
fi

cd .. || exit
echo ""

echo "🎉 Dashboard Setup Verification Complete!"
echo ""
echo "Next steps:"
echo "1. Install backend dependencies: pip install -r backend/requirements.txt"
echo "2. Install frontend dependencies: cd frontend && npm install"
echo "3. Start backend: cd backend && uvicorn main:app --reload"
echo "4. Start frontend: cd frontend && npm run dev"
echo ""
echo "The dashboard will be available at: http://localhost:3000"
echo "API will be available at: http://localhost:8000/api/docs"
