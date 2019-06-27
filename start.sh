#!/bin/sh

set -e

echo "Installing dependecies"
fridge -i

echo "All ok running cron in foreground"
crond -f -d 8