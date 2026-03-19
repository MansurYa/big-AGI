#!/bin/bash
# Обычный запуск прокси (без очистки кэша)

echo "🚀 Запуск прокси сервера..."
echo "Нажми Ctrl+C чтобы остановить"
echo ""

export ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
export ANTHROPIC_BASE_URL="https://api.kiro.cheap"
PYTHONPATH=. python src/proxy/server.py
