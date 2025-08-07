#!/bin/bash
# V26MEME Quick Deploy Script for Fresh Instance
# Run this on the new instance after transferring your .env file

set -e

echo "🚀 Starting V26MEME Quick Deploy..."

# Update system
echo "📦 Updating system..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "🔧 Installing dependencies..."
sudo apt install -y git curl build-essential pkg-config libssl-dev python3 python3-pip python3-venv

# Install Rust
echo "🦀 Installing Rust..."
if ! command -v cargo &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
fi

# Install Go
echo "🐹 Installing Go..."
if ! command -v go &> /dev/null; then
    wget https://golang.org/dl/go1.21.0.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin
fi

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in for Docker group changes to take effect"
fi

# Clone repository if not exists
if [ ! -d "Autobob2" ]; then
    echo "📥 Cloning V26MEME repository..."
    git clone https://github.com/shinertx/Autobob2.git
fi

cd Autobob2

# Make setup script executable
chmod +x setup.sh

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy your .env file with real API keys to this directory"
    echo "Then run: make deploy"
    exit 1
fi

echo "🏗️ Building V26MEME system..."

# Build Rust components
echo "Building Rust discovery engine..."
cd core
cargo build --release
cd ..

# Install Python dependencies
echo "🐍 Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Build Go execution engine
echo "Building Go execution engine..."
cd core
go build -o execution_engine execution_engine.go
cd ..

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for database
echo "⏳ Waiting for database to be ready..."
sleep 10

# Initialize database
echo "🗄️ Initializing database..."
source .venv/bin/activate
python infrastructure/database/setup_db.py

echo "✅ V26MEME deployed successfully!"
echo ""
echo "🎯 Starting all services..."
echo "📊 Dashboard will be available at: http://$(curl -s ifconfig.me):5001"
echo ""

# Start all services
make start

echo "🎉 V26MEME is now running!"
echo "Monitor the dashboard at: http://$(curl -s ifconfig.me):5001"
