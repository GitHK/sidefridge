#!/bin/sh

set -e

echo "[Boot script] Installing dependecies"
fridge -i

echo "[Boot script] All ok running cron in foreground"
crond -f -d 8