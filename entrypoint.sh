#!/bin/sh
set -e

python -m bot.recreate_database
exec python -m bot