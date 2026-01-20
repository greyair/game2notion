.PHONY: help install dev test lint format clean

help:
	@echo "Game2Notion 开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make install     - 安装项目依赖"
	@echo "  make dev         - 安装开发依赖"
	@echo "  make test        - 运行测试"
	@echo "  make lint        - 运行代码检查 (flake8 + mypy)"
	@echo "  make format      - 格式化代码 (black)"
	@echo "  make clean       - 清理构建文件"
	@echo "  make check       - 运行所有检查 (lint + test)"
	@echo "  make run         - 运行游戏列表同步"
	@echo "  make run-daily   - 运行每日记录同步"

install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src

lint:
	flake8 src/ tests/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/ docs/

check: lint test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name 'build' -exec rm -rf {} +
	find . -type d -name 'dist' -exec rm -rf {} +

run:
	python -m src.notion_game_list

run-daily:
	python -m src.daily_game_records

run-debug:
	python -m src.notion_game_list --debug

.DEFAULT_GOAL := help
