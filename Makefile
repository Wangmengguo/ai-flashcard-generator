# AI Flashcard Generator - Makefile
# Simplifies common deployment and development tasks

.PHONY: help dev prod test clean build push deploy health logs stop

# Default target
help:
	@echo "AI Flashcard Generator - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev         - Start development environment with hot reload"
	@echo "  make dev-logs    - Show development logs"
	@echo "  make dev-stop    - Stop development environment"
	@echo ""
	@echo "Production:"
	@echo "  make prod        - Start production environment"
	@echo "  make prod-full   - Start production with monitoring and nginx"
	@echo "  make prod-logs   - Show production logs"
	@echo "  make prod-stop   - Stop production environment"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build       - Build Docker images"
	@echo "  make push        - Push images to registry"
	@echo "  make deploy      - Deploy to remote server"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run code linting"
	@echo "  make security    - Run security scans"
	@echo ""
	@echo "Maintenance:"
	@echo "  make health      - Check application health"
	@echo "  make verify      - Run comprehensive deployment verification"
	@echo "  make validate    - Validate configuration files"
	@echo "  make logs        - Show all logs"
	@echo "  make clean       - Clean up containers and images"
	@echo "  make backup      - Create backup"
	@echo "  make update      - Update dependencies"
	@echo ""

# Development environment
dev:
	@echo "🚀 Starting development environment..."
	@cp .env.development .env || echo "Using existing .env file"
	docker-compose --profile dev up -d
	@echo "✅ Development environment started at http://localhost:8001"
	@echo "📋 Run 'make dev-logs' to see logs"

dev-logs:
	docker-compose logs -f flashcard-dev

dev-stop:
	docker-compose --profile dev down

# Production environment
prod:
	@echo "🚀 Starting production environment..."
	@cp .env.production .env || echo "Using existing .env file"
	docker-compose up -d
	@echo "✅ Production environment started at http://localhost:8000"
	@echo "📋 Run 'make prod-logs' to see logs"

prod-full:
	@echo "🚀 Starting full production environment with monitoring..."
	@cp .env.production .env || echo "Using existing .env file"
	docker-compose --profile production --profile monitoring up -d
	@echo "✅ Full production environment started:"
	@echo "   📱 App: http://localhost:8000"
	@echo "   📊 Prometheus: http://localhost:9090"
	@echo "   📈 Grafana: http://localhost:3000"

prod-logs:
	docker-compose logs -f flashcard-app

prod-stop:
	docker-compose --profile production --profile monitoring down

# Build and deployment
build:
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ Build completed"

build-prod:
	@echo "🔨 Building production Docker image..."
	docker build -t flashcard-generator:latest .
	@echo "✅ Production build completed"

push:
	@echo "📤 Pushing images to registry..."
	docker tag flashcard-generator:latest $(REGISTRY)/flashcard-generator:latest
	docker push $(REGISTRY)/flashcard-generator:latest
	@echo "✅ Images pushed"

deploy:
	@echo "🚀 Deploying to remote server..."
	@if [ -z "$(SERVER)" ]; then \
		echo "❌ Please specify SERVER: make deploy SERVER=your-server.com"; \
		exit 1; \
	fi
	scp docker-compose.yml $(SERVER):/opt/flashcard-generator/
	scp .env.production $(SERVER):/opt/flashcard-generator/.env
	ssh $(SERVER) "cd /opt/flashcard-generator && docker-compose pull && docker-compose up -d"
	@echo "✅ Deployment completed"

# Testing and quality assurance
test:
	@echo "🧪 Running tests..."
	docker-compose exec flashcard-app python -m pytest tests/ -v --cov=main
	@echo "✅ Tests completed"

test-local:
	@echo "🧪 Running local tests..."
	python -m pytest tests/ -v --cov=main
	@echo "✅ Local tests completed"

lint:
	@echo "🔍 Running code linting..."
	docker-compose exec flashcard-app black --check main.py
	docker-compose exec flashcard-app flake8 main.py
	docker-compose exec flashcard-app mypy main.py
	@echo "✅ Linting completed"

lint-local:
	@echo "🔍 Running local linting..."
	black --check main.py
	flake8 main.py
	mypy main.py
	@echo "✅ Local linting completed"

security:
	@echo "🔒 Running security scans..."
	bandit -r . -f json -o security-report.json
	docker run --rm -v $(PWD):/tmp/.cache/ aquasec/trivy:latest image flashcard-generator:latest
	@echo "✅ Security scan completed"

# Health and monitoring
health:
	@echo "🏥 Checking application health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Health check failed"

health-dev:
	@echo "🏥 Checking development environment health..."
	@curl -s http://localhost:8001/health | python -m json.tool || echo "❌ Health check failed"

# Comprehensive deployment verification
verify:
	@echo "🔍 Running comprehensive deployment verification..."
	python deployment-check.py

verify-dev:
	@echo "🔍 Running development environment verification..."
	python deployment-check.py http://localhost:8001

# Configuration validation
validate:
	@echo "📋 Validating configuration..."
	python validate-config.py

status:
	@echo "📊 Container status:"
	docker-compose ps

logs:
	docker-compose logs -f

logs-app:
	@echo "📋 Application logs:"
	tail -f logs/app.log

logs-access:
	@echo "📋 Access logs:"
	tail -f logs/access.log

logs-error:
	@echo "📋 Error logs:"
	tail -f logs/error.log

# Maintenance
clean:
	@echo "🧹 Cleaning up containers and images..."
	docker-compose down --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed"

clean-all:
	@echo "🧹 Deep cleaning (WARNING: This will remove all stopped containers and unused images)..."
	docker-compose down --remove-orphans --volumes
	docker system prune -af
	docker volume prune -f
	@echo "✅ Deep cleanup completed"

backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d_%H%M%S).tar.gz \
		.env* docker-compose.yml nginx/ monitoring/ logs/ config/
	@echo "✅ Backup created in backups/ directory"

update:
	@echo "📦 Updating dependencies..."
	pip install --upgrade -r requirements.txt
	docker-compose build --no-cache
	@echo "✅ Dependencies updated"

# Database operations (for future use)
db-migrate:
	@echo "🗄️ Running database migrations..."
	docker-compose exec flashcard-app alembic upgrade head
	@echo "✅ Migrations completed"

db-backup:
	@echo "💾 Backing up database..."
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U $$POSTGRES_USER $$POSTGRES_DB > backups/db-backup-$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created"

# Performance testing
load-test:
	@echo "⚡ Running load test..."
	python performance_test.py
	@echo "✅ Load test completed"

bench:
	@echo "📊 Running benchmarks..."
	python benchmark.py
	@echo "✅ Benchmarks completed"

# SSL certificate management (for production)
ssl-cert:
	@echo "🔐 Generating SSL certificate..."
	@mkdir -p nginx/ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout nginx/ssl/key.pem \
		-out nginx/ssl/cert.pem \
		-subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
	@echo "✅ SSL certificate generated"

# Environment setup
setup-dev:
	@echo "🛠️  Setting up development environment..."
	python -m venv venv
	./venv/bin/pip install -r requirements.dev.txt
	cp .env.example .env
	@echo "✅ Development environment setup completed"
	@echo "📋 Please edit .env file and set OPENROUTER_API_KEY"

setup-prod:
	@echo "🛠️  Setting up production environment..."
	cp .env.production .env
	@echo "✅ Production environment setup completed"
	@echo "📋 Please edit .env file and set required values"

# Documentation
docs:
	@echo "📚 Available documentation:"
	@echo "  📖 README.md - Project overview"
	@echo "  🚀 DEPLOYMENT_GUIDE.md - Detailed deployment guide"
	@echo "  ✅ DEPLOYMENT_CHECKLIST.md - Pre-deployment checklist"
	@echo "  🏆 PRODUCTION_BEST_PRACTICES.md - Production best practices"
	@echo "  🏗️  ARCHITECTURE_ANATOMY.md - Architecture documentation"

# Quick deployment scenarios
quick-dev:
	@echo "⚡ Quick development setup..."
	make setup-dev
	make dev
	make health-dev

quick-prod:
	@echo "⚡ Quick production setup..."
	make setup-prod
	make build
	make prod
	make health

# Monitoring shortcuts
monitor:
	@echo "📊 Opening monitoring dashboards..."
	@echo "Opening Prometheus: http://localhost:9090"
	@echo "Opening Grafana: http://localhost:3000"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:9090; \
		open http://localhost:3000; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:9090; \
		xdg-open http://localhost:3000; \
	fi

# Environment variables
ENV_FILE ?= .env
REGISTRY ?= your-registry.com
SERVER ?=

# Include environment variables from .env file if it exists
-include $(ENV_FILE)