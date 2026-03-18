#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OS="$(uname -s)"

if [ "$OS" = "Darwin" ]; then
    PLIST="$HOME/Library/LaunchAgents/com.openmoss.server.plist"
    if [ -f "$PLIST" ]; then
        launchctl unload "$PLIST" 2>/dev/null || true
        rm -f "$PLIST"
        echo "✅ launchd daemon 已卸载"
    else
        echo "未找到 launchd plist，可能未安装"
    fi

elif [ "$OS" = "Linux" ]; then
    SERVICE="/etc/systemd/system/openmoss.service"
    if [ -f "$SERVICE" ]; then
        sudo systemctl stop openmoss 2>/dev/null || true
        sudo systemctl disable openmoss 2>/dev/null || true
        sudo rm -f "$SERVICE"
        sudo systemctl daemon-reload
        echo "✅ systemd service 已卸载"
    else
        echo "未找到 systemd service，可能未安装"
    fi

else
    echo "不支持的平台 ($OS)"
fi
