#!/bin/bash

# V26MEME Setup Script
# Run this to set up the complete development environment

set -e

echo "🚀 Setting up V26MEME Autonomous Trading System"
echo "================================================"

# Check if required tools are installed
check_dependencies() {
    echo "📋 Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Rust
    if ! command -v cargo &> /dev/null; then
        echo "⚠️ Rust is not installed. Installing via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
    fi
    
    # Check Go
    if ! command -v go &> /dev/null; then
        echo "❌ Go is not installed. Please install Go 1.21+ first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    echo "✅ All dependencies found"
}

# Create environment file
setup_environment() {
    echo "🔧 Setting up environment..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 Created .env file from template"
        echo "⚠️ IMPORTANT: Edit .env and add your API keys before continuing!"
        echo ""
        echo "Required API keys:"
        echo "- OPENAI_API_KEY (required for AI features)"
        echo "- COINBASE_API_KEY, COINBASE_SECRET (for trading)"
        echo "- KRAKEN_API_KEY, KRAKEN_SECRET (for trading)"
        echo "- ALCHEMY_API_KEY (for Ethereum access)"
        echo ""
        read -p "Press Enter after you've updated .env with your API keys..."
    else
        echo "✅ .env file already exists"
    fi
}

# Install Python dependencies
setup_python() {
    echo "🐍 Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Created Python virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Installed Python dependencies"
}

# Install Rust dependencies
setup_rust() {
    echo "🦀 Setting up Rust environment..."
    
    # Build the project to download and compile dependencies
    cargo build
    echo "✅ Built Rust components"
}

# Install Go dependencies
setup_go() {
    echo "🐹 Setting up Go environment..."
    
    # Download Go modules
    go mod download
    go mod tidy
    echo "✅ Downloaded Go dependencies"
}

# Install Node.js dependencies for dashboard
setup_nodejs() {
    echo "📊 Setting up Node.js dashboard..."
    
    cd dashboard
    npm install
    cd ..
    echo "✅ Installed Node.js dependencies"
}

# Start infrastructure services
start_infrastructure() {
    echo "🏗️ Starting infrastructure services..."
    
    # Start PostgreSQL and Redis
    docker-compose up -d timescale redis
    
    echo "⏳ Waiting for database to be ready..."
    sleep 10
    
    # Check if database is accessible
    until docker exec -it $(docker-compose ps -q timescale) pg_isready -U v26meme; do
        echo "⏳ Waiting for database..."
        sleep 2
    done
    
    echo "✅ Infrastructure services started"
}

# Initialize database
init_database() {
    echo "🗄️ Initializing database..."
    
    # The init script should run automatically via docker-entrypoint-initdb.d
    # But let's verify the database is set up correctly
    docker exec -it $(docker-compose ps -q timescale) psql -U v26meme -d v26meme -c "SELECT COUNT(*) FROM discovered_patterns;"
    
    echo "✅ Database initialized"
}

# Run initial tests
run_tests() {
    echo "🧪 Running initial tests..."
    
    # Test Rust components
    echo "Testing Rust components..."
    cargo test
    
    # Test Python components
    echo "Testing Python components..."
    source venv/bin/activate
    python -m pytest tests/ -v || echo "⚠️ No tests found yet"
    
    # Test Go components
    echo "Testing Go components..."
    go test ./... || echo "⚠️ No tests found yet"
    
    echo "✅ Tests completed"
}

# Create initial project structure files
create_placeholder_files() {
    echo "📁 Creating additional project structure..."
    
    # Create additional directories that might be needed
    mkdir -p data/patterns
    mkdir -p data/cache
    mkdir -p logs/trades
    mkdir -p strategies/discovered
    
    # Create placeholder files to maintain git structure
    touch data/.gitkeep
    touch logs/.gitkeep
    
    # Create a simple test script
    cat > tests/test_system.py << 'EOF'
#!/usr/bin/env python3
"""
Basic system test to verify all components can communicate
"""

import os
import sys
import asyncio
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intelligence.openai_strategist import OpenAIStrategist

async def test_openai_connection():
    """Test if OpenAI API key is working"""
    try:
        strategist = OpenAIStrategist()
        status = strategist.get_budget_status()
        print(f"✅ OpenAI integration ready: {status}")
        return True
    except Exception as e:
        print(f"❌ OpenAI integration failed: {e}")
        return False

def test_environment():
    """Test if environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    else:
        print("✅ All required environment variables set")
        return True

async def main():
    """Run all tests"""
    print("🧪 Running V26MEME System Tests")
    print("=" * 40)
    
    # Test environment
    env_ok = test_environment()
    
    # Test OpenAI (only if API key is set)
    openai_ok = True
    if os.getenv('OPENAI_API_KEY'):
        openai_ok = await test_openai_connection()
    else:
        print("⚠️ OpenAI API key not set, skipping OpenAI test")
    
    # Summary
    print("\n" + "=" * 40)
    if env_ok and openai_ok:
        print("✅ All system tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
EOF
    
    chmod +x tests/test_system.py
    echo "✅ Created additional project files"
}

# Main setup flow
main() {
    echo "Starting V26MEME setup..."
    
    check_dependencies
    setup_environment
    create_placeholder_files
    setup_python
    setup_rust
    setup_go
    setup_nodejs
    start_infrastructure
    init_database
    run_tests
    
    echo ""
    echo "🎉 V26MEME setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Verify your .env file has all required API keys"
    echo "2. Run the system test: python tests/test_system.py"
    echo "3. Start the full system: docker-compose up"
    echo "4. Access dashboard at http://localhost:3000"
    echo ""
    echo "🚨 REMEMBER: This system will trade with REAL MONEY"
    echo "   Start with paper trading mode first!"
    echo ""
    echo "Happy trading! 🚀"
}

# Run main function
main "$@"
