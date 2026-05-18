.PHONY: dev dev-backend dev-frontend build install clean

BACKEND_DIR = backend
FRONTEND_DIR = frontend

dev:
	@echo "Starting backend and frontend..."
	@trap 'kill 0' EXIT; \
		cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port 8000 & \
		cd $(FRONTEND_DIR) && npm run dev & \
		wait

dev-backend:
	@echo "Starting backend..."
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	@echo "Starting frontend..."
	cd $(FRONTEND_DIR) && npm run dev

build:
	cd $(FRONTEND_DIR) && npm run build

install:
	cd $(BACKEND_DIR) && uv sync
	cd $(FRONTEND_DIR) && npm install

clean:
	rm -rf $(FRONTEND_DIR)/dist
	rm -rf $(FRONTEND_DIR)/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
