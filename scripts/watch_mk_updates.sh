#!/usr/bin/env bash
set -Eeuo pipefail
cd "$HOME/mk"

echo "Watching project changes. Press Ctrl+C to stop."
echo

while true; do
  clear
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo
  echo "=== git status ==="
  git status --short || true

  echo
  echo "=== docker ps ==="
  sudo docker compose ps || true

  echo
  echo "=== latest changed frontend/backend files ==="
  find backend frontend -type f \
    \( -name "*.py" -o -name "*.tsx" -o -name "*.ts" -o -name "*.sql" -o -name "*.css" \) \
    -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort -r | head -n 30

  echo
  echo "=== timetable route ==="
  curl -fsSI http://localhost:3100/timetable 2>/dev/null | head -n 1 || echo "frontend timetable not reachable"

  echo
  echo "=== backend timetable summary ==="
  curl -fsS http://localhost:8100/api/v1/school-timetable/summary 2>/dev/null || echo "backend timetable not reachable"

  sleep 10
done
