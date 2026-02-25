#!/bin/bash
# GhostPen - Stop Everything
echo "Stopping GhostPen..."
pkill -f "python server.py" 2>/dev/null
pkill -f "next-server" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
rm -f /home/alexandratitus767/gptoss-alexandra-project/ghostpen/.next/dev/lock 2>/dev/null
echo "Done. All GhostPen processes stopped."
