.PHONY: all build-rust build-go setup-python clean test deploy

# Default target
all: setup-python build-rust build-go

# Setup Python environment
setup-python:
	@echo "🐍 Setting up Python environment..."
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	@echo "✅ Python environment ready"

# Build Rust components
build-rust:
	@echo "🦀 Building Rust components..."
	cargo build --release
	@echo "✅ Rust components built"

# Build Go execution engine  
build-go:
	@echo "🐹 Building Go execution engine..."
	cd core && go build -o execution_engine execution_engine.go
	@echo "✅ Go execution engine built"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	cargo clean
	cd core && go clean
	rm -rf venv
	@echo "✅ Clean complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	cargo test
	cd core && go test
	./venv/bin/python -m pytest intelligence/tests/
	@echo "✅ All tests passed"

# Setup database
setup-db:
	@echo "🗄️ Setting up database..."
	createdb v26meme || true
	./venv/bin/python -c "import asyncio; import asyncpg; asyncio.run(asyncpg.connect('postgresql://localhost:5432/v26meme').close())"
	sqlx migrate run
	@echo "✅ Database ready"

# Deploy system
deploy: all setup-db
	@echo "🚀 Starting V26MEME system..."
	./target/release/autobob2

# Development mode
dev:
	@echo "🔧 Starting in development mode..."
	cargo run

# Monitor system
monitor:
	@echo "📊 System monitoring..."
	tail -f autobob2.log
