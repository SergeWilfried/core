#!/bin/bash

SCRIPTS_DIR=$(dirname $(readlink -e "$0"))
ROOT_DIR=$(dirname "$SCRIPTS_DIR")

uv run ruff format --check "$ROOT_DIR"
