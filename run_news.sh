#!/bin/bash
# run_news.sh — wrapper script for news_collector.py
# Usage: ./run_news.sh [--open]
# Cron example: 0 7 * * * /path/to/news_collector/run_news.sh >> /path/to/news_collector/cron.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
LOG_DIR="$SCRIPT_DIR/logs"
REPORT_DIR="$SCRIPT_DIR/reports"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/run_$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] Starting news collection..."

# Activate virtualenv if present
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Check feedparser is installed, install if missing
if ! $PYTHON -c "import feedparser" 2>/dev/null; then
    echo "Installing feedparser..."
    $PYTHON -m pip install feedparser --quiet
fi

# Run collector
$PYTHON "$SCRIPT_DIR/news_collector.py" 2>&1 | tee "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Success. Report: $REPORT_DIR/latest.html"

    # --open flag: open in default browser
    if [[ "${1:-}" == "--open" ]]; then
        if command -v open &>/dev/null; then
            open "$REPORT_DIR/latest.html"
        elif command -v xdg-open &>/dev/null; then
            xdg-open "$REPORT_DIR/latest.html"
        fi
    fi
else
    echo "[$TIMESTAMP] ERROR: collector exited with code $EXIT_CODE" >&2
fi

# Keep only last 30 log files
ls -t "$LOG_DIR"/run_*.log 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

exit $EXIT_CODE
