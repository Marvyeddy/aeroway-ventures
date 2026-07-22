#!/bin/bash

set -ex

uv run alembic upgrade head

exec uv run fastapi run main.py --port 80 --host 0.0.0.0