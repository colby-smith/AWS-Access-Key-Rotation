#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SRC_DIR="$PROJECT_ROOT/src"
LAMBDA_FILE="$SRC_DIR/lambda_function.py"
ZIP_FILE="$SRC_DIR/lambda_function.zip"

if [ ! -f "$LAMBDA_FILE" ]; then
  echo "Error: could not find $LAMBDA_FILE"
  exit 1
fi

rm -f "$ZIP_FILE"

cd "$SRC_DIR"
zip -r "lambda_function.zip" "lambda_function.py"

echo "Created $ZIP_FILE"