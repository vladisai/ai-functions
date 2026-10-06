#!/usr/bin/env bash
# Start QuickLearn. The reader folder is kept across restarts; Reset in the app empties it.
#
#   ./run.sh [PORT]                               the default reader on port 8889
#   QUICKLEARN_READER=physics-undergrad ./run.sh  a demo reader from demo_readers/
#   QUICKLEARN_CONTENT=~/class-content ./run.sh   another content folder
set -euo pipefail
cd "$(dirname "$0")"

export AWS_STS_REGIONAL_ENDPOINTS=regional
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-west-2}"

PORT="${1:-8889}"
echo "Starting QuickLearn on port $PORT, reader ${QUICKLEARN_READER:-default}..."
exec uv run python -m quicklearn.app --port "$PORT"
