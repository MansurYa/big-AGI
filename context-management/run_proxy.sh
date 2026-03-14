#!/bin/bash
# Convenience script to run the proxy server

cd "$(dirname "$0")"
source .venv/bin/activate
PYTHONPATH=. python src/proxy/server.py
