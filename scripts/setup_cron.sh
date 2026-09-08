#!/bin/bash
# YT-Flow Cron Scheduler
# Sets up automated video processing and release
# Run once: bash scripts/setup_cron.sh

PROJECT_DIR="$HOME/Documents/YT-Flow"
LOG_DIR="$PROJECT_DIR/logs"
CRON_LOG="$LOG_DIR/cron_execution.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Cron schedule (edit these as needed)
# Format: minute hour day month weekday command

CRON_ENTRIES=$(cat <<'EOF'
# YT-Flow: Check release queue every hour
0 * * * * cd $HOME/Documents/YT-Flow && python3 scripts/schedule_release.py cron >> $HOME/Documents/YT-Flow/logs/cron_execution.log 2>&1

# YT-Flow: Process pending videos every 30 minutes
*/30 * * * * cd $HOME/Documents/YT-Flow && python3 scripts/process_video.py --input videos/raw/ --extend-to 22 >> $HOME/Documents/YT-Flow/logs/cron_execution.log 2>&1

# YT-Flow: Daily pipeline log update at midnight
0 0 * * * cd $HOME/Documents/YT-Flow && echo "[$(date)] Pipeline check" >> $HOME/Documents/YT-Flow/logs/cron_execution.log 2>&1
EOF
)

echo "Setting up YT-Flow cron jobs..."
echo "$CRON_ENTRIES"

# Install cron jobs
(crontab -l 2>/dev/null; echo "$CRON_ENTRIES") | sort -u | crontab -

echo "✅ Cron jobs installed. Run 'crontab -l' to verify."
