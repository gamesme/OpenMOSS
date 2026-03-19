# OpenMOSS — 统一操作入口
# 用法: make <target>

PYTHON   ?= .venv/bin/python
CONF     := deploy/supervisord.conf
SOCK     := supervisord.sock

.PHONY: help setup start stop restart status logs install uninstall \
        docker-up docker-down docker-logs docker-build clean

help:   ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── 环境准备 ──────────────────────────────────────────────

setup:  ## 创建 venv 并安装依赖
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@[ -f config.yaml ] || cp config.example.yaml config.yaml
	@mkdir -p logs data
	@echo "✅ 环境准备完成，请编辑 config.yaml 后运行 make start"

# ── supervisord 方式（跨平台，推荐日常开发）────────────────

start:  ## 启动服务（supervisord）
	@if [ -f $(SOCK) ]; then echo "服务已在运行，请用 make restart"; else \
	  mkdir -p logs && .venv/bin/supervisord -c $(CONF) && sleep 1 && $(MAKE) status; \
	fi

stop:   ## 停止服务（supervisord）
	@if [ -f $(SOCK) ]; then \
	  .venv/bin/supervisorctl -c $(CONF) shutdown; true; \
	else \
	  echo "服务未运行"; \
	fi

restart: ## 重启 OpenMOSS 进程（不重启 supervisord）
	.venv/bin/supervisorctl -c $(CONF) restart openmoss

status: ## 查看服务状态
	.venv/bin/supervisorctl -c $(CONF) status

logs:   ## 实时查看日志（Ctrl+C 退出）
	tail -f logs/stdout.log logs/stderr.log

# ── 系统级 daemon（开机自启，需要 install 一次）────────────

install: ## 安装为系统 daemon（macOS: launchd / Linux: systemd）
	bash deploy/install.sh

uninstall: ## 卸载系统 daemon
	bash deploy/uninstall.sh

# ── Docker Compose 方式（完整隔离，适合服务器）────────────

docker-build: ## 构建 Docker 镜像
	docker compose build

docker-up: ## 后台启动 Docker 服务
	@[ -f config.yaml ] || cp config.example.yaml config.yaml
	@mkdir -p logs data
	docker compose up -d
	@echo "✅ 服务已启动: http://localhost:6565"

docker-down: ## 停止并移除 Docker 容器
	docker compose down

docker-logs: ## 实时查看 Docker 日志
	docker compose logs -f

# ── 清理 ─────────────────────────────────────────────────

clean:  ## 清理运行时产物（不删除数据）
	rm -f supervisord.pid supervisord.sock
	rm -f logs/supervisord.log
	@echo "清理完成（data/ 和 logs/*.log 保留）"
