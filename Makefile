.PHONY: help install start backend frontend format lint clean

.DEFAULT_GOAL := help
help:
	@echo "================================================="
	@echo "          🤖 FPT HR Chatbot - Makefile         "
	@echo "================================================="
	@echo "Các lệnh (commands) có sẵn:"
	@echo ""
	@echo "Cài đặt & Khởi tạo:"
	@echo "  make setup    : Cài đặt thư viện cho cả Backend (uv) và Frontend (npm)"
	@echo ""
	@echo "Chạy ứng dụng:"
	@echo "  make start      : Chạy CÙNG LÚC cả Backend và Frontend"
	@echo "  make backend    : Chỉ khởi chạy Backend (FastAPI)"
	@echo "  make frontend   : Chỉ khởi chạy Frontend (React/Vite)"
	@echo ""
	@echo "Tiện ích:"
	@echo "  make clean      : Xóa các file rác, cache, môi trường ảo (.venv, node_modules)"
	@echo "================================================="

setup:
	@echo "Đang cài đặt Backend Dependencies (bằng uv)..."
	cd backend && uv sync
	@echo "Đang cài đặt Frontend Dependencies (bằng npm)..."
	cd frontend && npm install
	@echo "Cài đặt hoàn tất!"

start:
	@echo "(Backend + Frontend)..."
	@echo "Nhấn Ctrl+C để dừng cả hai."
	make backend & make frontend & wait

backend:
	@echo " Đang chạy FastAPI Backend tại http://localhost:8000"
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo " Đang chạy React/Vite Frontend..."
	cd frontend && npm run dev

clean:
	@echo " Đang tiến hành dọn dẹp..."
	rm -rf backend/.venv
	rm -rf backend/.ruff_cache
	rm -rf frontend/node_modules
	rm -rf frontend/dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Dọn dẹp hoàn tất!"
