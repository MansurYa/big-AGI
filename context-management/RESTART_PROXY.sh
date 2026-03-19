#!/bin/bash
# Скрипт для перезапуска прокси с очисткой кэша

echo "🧹 Очистка Python кэша..."
find src -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find src -name "*.pyc" -delete 2>/dev/null
echo "✅ Кэш очищен"

echo ""
echo "🚀 Запуск прокси сервера..."
echo "Нажми Ctrl+C чтобы остановить"
echo ""

export ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
export ANTHROPIC_BASE_URL="https://api.kiro.cheap"
PYTHONPATH=. python src/proxy/server.py
