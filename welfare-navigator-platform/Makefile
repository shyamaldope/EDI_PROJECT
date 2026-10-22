.PHONY: help setup dev test seed demo-artifacts lint docker-up docker-down

help:
	@echo "Welfare Navigator Platform Commands:"
	@echo "  make setup          - Install dependencies for backend and frontend"
	@echo "  make seed           - Seed database with 20 schemes & 50 citizens"
	@echo "  make demo-artifacts - Generate sample PDF GR and synthetic certificates"
	@echo "  make dev            - Run backend, mock portals, and frontend concurrently"
	@echo "  make test           - Run full backend pytest test suite"
	@echo "  make docker-up      - Launch full dockerized stack"
	@echo "  make docker-down    - Stop dockerized stack"

setup:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

seed:
	python welfare-navigator-platform/backend/database/seed.py

demo-artifacts:
	python welfare-navigator-platform/sample_artifacts/generate_artifacts.py

dev:
	@echo "Launching backend, mock portals, and frontend..."
	python welfare-navigator-platform/backend/main.py

test:
	pytest welfare-navigator-platform/backend/tests -v

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
