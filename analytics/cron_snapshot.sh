#!/usr/bin/env bash
# Wrapper de cron: roda o snapshot diario e loga resultado.
cd "$(dirname "$0")/.."
LOG="analytics/data/cron.log"
mkdir -p analytics/data
echo "----- $(date -u +%Y-%m-%dT%H:%M:%SZ) -----" >> "$LOG"
.venv/bin/python analytics/snapshot.py >> "$LOG" 2>&1
echo "exit=$? " >> "$LOG"
