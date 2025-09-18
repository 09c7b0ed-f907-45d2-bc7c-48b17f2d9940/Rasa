#!/bin/bash

# Usage:
#   ./layer_rasa_projects.sh [--dry-run[=stdout|files]] [--dump-dir <dir>] /path/to/project1 [/path/to/project2 ...]
# Layers Rasa projects exactly in the order provided (first is the base layer). When --dry-run is supplied,
# it will dump the merged domain and NLU without running 'rasa train'. No hardcoded knowledge of core/fallback.

set -euo pipefail

# Defaults
DRY_RUN_MODE=""
DUMP_DIR="build/overlay-dump"

# Parse options
while [[ "$#" -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN_MODE="files"; shift ;;
    --dry-run=stdout)
      DRY_RUN_MODE="stdout"; shift ;;
    --dry-run=files)
      DRY_RUN_MODE="files"; shift ;;
    --dump-dir)
      DUMP_DIR="$2"; shift 2 ;;
    --dump-dir=*)
      DUMP_DIR="${1#*=}"; shift ;;
    --)
      shift; break ;;
    *)
      echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 [--dry-run[=stdout|files]] [--dump-dir <dir>] <project_path_1> [project_path_2 ...]"
  exit 1
fi

# Consume ordered project list
PROJECTS=("$@")

# Use first as base, rest as overlays
BASE_PATH="${PROJECTS[0]}"
OVERLAY_PATHS=("${PROJECTS[@]:1}")

BASE_DOMAIN="$BASE_PATH/domain"
BASE_NLU="$BASE_PATH/nlu"
BASE_STORIES="$BASE_PATH/data"
BASE_CONFIG="$BASE_PATH/config.yml"

# Initialize overlay paths
OVERLAY_DOMAIN_ARR=()
OVERLAY_NLU_ARR=()
OVERLAY_STORIES_ARR=()

for overlay_path in "${OVERLAY_PATHS[@]}"; do
  OVERLAY_DOMAIN_ARR+=("$overlay_path/domain")
  OVERLAY_NLU_ARR+=("$overlay_path/data/nlu")
  OVERLAY_STORIES_ARR+=("$overlay_path/data")
done

# Join overlays as comma-separated lists
OVERLAY_DOMAIN_STR=$(IFS=,; echo "${OVERLAY_DOMAIN_ARR[*]}")
OVERLAY_NLU_STR=$(IFS=,; echo "${OVERLAY_NLU_ARR[*]}")
OVERLAY_STORIES_STR=$(IFS=,; echo "${OVERLAY_STORIES_ARR[*]}")

# Export environment variables for OverlayImporter (env takes precedence over config)
export OVERLAY_BASE_DOMAIN="$BASE_DOMAIN"
export OVERLAY_DOMAIN="$OVERLAY_DOMAIN_STR"
export OVERLAY_NLU="$OVERLAY_NLU_STR"
export OVERLAY_STORIES="$OVERLAY_STORIES_STR"

# Ensure Python can import our components (use repo root regardless of environment)
export PYTHONPATH="${PYTHONPATH:-$PWD}"

# Dry-run path: dump merged Domain and NLU using OverlayImporter and exit
if [[ -n "$DRY_RUN_MODE" ]]; then
  if [[ "$DRY_RUN_MODE" == "stdout" ]]; then
    export OVERLAY_DUMP_DOMAIN=stdout
    export OVERLAY_DUMP_NLU=stdout
  else
    mkdir -p "$DUMP_DIR"
    export OVERLAY_DUMP_DOMAIN="$DUMP_DIR/merged-domain.yml"
    export OVERLAY_DUMP_NLU="$DUMP_DIR/merged-nlu.yml"
    echo "Dry run: writing merged files to $DUMP_DIR" >&2
  fi

  # Call the importer directly to perform merges once
  python - <<'PY' "$BASE_DOMAIN" "${OVERLAY_DOMAIN_ARR[@]}"
import os, sys
from src.components.layered_importer import OverlayImporter

base_domain = [sys.argv[1]]
overlay_domain = sys.argv[2:]
overlay_nlu = os.environ.get('OVERLAY_NLU')
imp = OverlayImporter(base_domain=base_domain, overlay_domain=overlay_domain, overlay_nlu=overlay_nlu)

# Trigger merges; dumps are controlled by env vars OVERLAY_DUMP_DOMAIN / OVERLAY_DUMP_NLU
imp.get_domain()
imp.get_nlu_data()
PY
  exit 0
fi

# Run Rasa train
rasa train -d "$BASE_DOMAIN" --config "$BASE_CONFIG" --data "$BASE_STORIES"
