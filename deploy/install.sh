#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
CURRENT_USER="$(whoami)"

# 检查 venv 是否存在
if [ ! -f "$VENV_PYTHON" ]; then
    echo "错误：未找到 $VENV_PYTHON，请先运行 python -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# 确保 logs 目录存在
mkdir -p "$PROJECT_ROOT/logs"

OS="$(uname -s)"

if [ "$OS" = "Darwin" ]; then
    echo "[install] 检测到 macOS，安装 launchd daemon..."
    PLIST_DST="$HOME/Library/LaunchAgents/com.openmoss.server.plist"

    sed \
        -e "s|PROJECT_ROOT|$PROJECT_ROOT|g" \
        -e "s|VENV_PYTHON|$VENV_PYTHON|g" \
        "$PROJECT_ROOT/deploy/launchd.plist.template" > "$PLIST_DST"

    launchctl unload "$PLIST_DST" 2>/dev/null || true
    launchctl load -w "$PLIST_DST"

    echo "✅ launchd daemon 已安装并启动"
    echo "   配置文件: $PLIST_DST"
    echo "   日志目录: $PROJECT_ROOT/logs/"
    echo "   停止: make uninstall 或 launchctl unload $PLIST_DST"

elif [ "$OS" = "Linux" ]; then
    echo "[install] 检测到 Linux，安装 systemd service..."
    SERVICE_DST="/etc/systemd/system/openmoss.service"

    sed \
        -e "s|PROJECT_ROOT|$PROJECT_ROOT|g" \
        -e "s|VENV_PYTHON|$VENV_PYTHON|g" \
        -e "s|CURRENT_USER|$CURRENT_USER|g" \
        "$PROJECT_ROOT/deploy/systemd.service.template" > /tmp/openmoss.service

    sudo mv /tmp/openmoss.service "$SERVICE_DST"
    sudo systemctl daemon-reload
    sudo systemctl enable openmoss
    sudo systemctl start openmoss

    echo "✅ systemd service 已安装并启动"
    echo "   配置文件: $SERVICE_DST"
    echo "   查看状态: sudo systemctl status openmoss"
    echo "   停止: make uninstall"

else
    echo "⚠️  不支持的平台 ($OS)，请使用 supervisord 方式：make start"
    echo "   或使用 Docker：make docker-up"
    exit 1
fi
