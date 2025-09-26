#!/bin/bash

# Usage:
#   ./layer_rasa_projects.sh [--dry-run[=stdout|files]] [--dump-dir <dir>] /path/to/project1 [/path/to/project2 ...]
# Layers Rasa projects in the order provided (first is the base layer). When --dry-run is supplied,
# it will dump the merged domain and NLU without running 'rasa train'.

set -euo pipefail

DRY_RUN_MODE=""
DUMP_DIR="build/overlay-dump"
WRITE_OVERLAY_INFO="false"

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
    --write-overlay-info)
      WRITE_OVERLAY_INFO="true"; shift ;;
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

PROJECTS=("$@")

BASE_PATH="${PROJECTS[0]}"
OVERLAY_PATHS=("${PROJECTS[@]:1}")

BASE_DOMAIN="$BASE_PATH/domain"
# Determine config/endpoints/credentials using layered precedence (last project wins)
SELECTED_CONFIG=""
SELECTED_ENDPOINTS=""
SELECTED_CREDENTIALS=""

# Scan from highest precedence (last) to lowest (first)
for (( idx=${#PROJECTS[@]}-1 ; idx>=0 ; idx-- )); do
  p="${PROJECTS[$idx]}"
  [[ -z "$SELECTED_CONFIG" && -f "$p/config.yml" ]] && SELECTED_CONFIG="$p/config.yml"
  [[ -z "$SELECTED_ENDPOINTS" && -f "$p/endpoints.yml" ]] && SELECTED_ENDPOINTS="$p/endpoints.yml"
  [[ -z "$SELECTED_CREDENTIALS" && -f "$p/credentials.yml" ]] && SELECTED_CREDENTIALS="$p/credentials.yml"
done

# Fallback for config if nothing found in layers
if [[ -z "$SELECTED_CONFIG" && -f "src/core/config.yml" ]]; then
  SELECTED_CONFIG="src/core/config.yml"
fi

BASE_STORIES="$BASE_PATH/data"

OVERLAY_DOMAIN_ARR=()
OVERLAY_NLU_ARR=()
OVERLAY_STORIES_ARR=()

# Base NLU candidates (derived similarly to importer)
BASE_NLU_ARR=()
[[ -d "$BASE_PATH/data/nlu" ]] && BASE_NLU_ARR+=("$BASE_PATH/data/nlu")
[[ -d "$BASE_PATH/nlu" ]] && BASE_NLU_ARR+=("$BASE_PATH/nlu")

for overlay_path in "${OVERLAY_PATHS[@]}"; do
  [ -d "$overlay_path/domain" ] && OVERLAY_DOMAIN_ARR+=("$overlay_path/domain")
  [ -d "$overlay_path/data/nlu" ] && OVERLAY_NLU_ARR+=("$overlay_path/data/nlu")
  [ -d "$overlay_path/data" ] && OVERLAY_STORIES_ARR+=("$overlay_path/data")
done

OVERLAY_DOMAIN_STR=$(IFS=,; echo "${OVERLAY_DOMAIN_ARR[*]}")
OVERLAY_NLU_STR=$(IFS=,; echo "${OVERLAY_NLU_ARR[*]}")
OVERLAY_STORIES_STR=$(IFS=,; echo "${OVERLAY_STORIES_ARR[*]}")
BASE_NLU_STR=$(IFS=,; echo "${BASE_NLU_ARR[*]}")

export OVERLAY_BASE_DOMAIN="$BASE_DOMAIN"
export OVERLAY_DOMAIN="$OVERLAY_DOMAIN_STR"
export OVERLAY_NLU="$OVERLAY_NLU_STR"
export OVERLAY_STORIES="$OVERLAY_STORIES_STR"

export PYTHONPATH="${PYTHONPATH:-$PWD}"

# Optionally persist overlay info; otherwise print on dry-run only
if [[ "$WRITE_OVERLAY_INFO" == "true" ]]; then
  mkdir -p build
  {
    echo "BASE_DOMAIN=$BASE_DOMAIN"
    echo "OVERLAY_DOMAIN=$OVERLAY_DOMAIN_STR"
    echo "OVERLAY_NLU=$OVERLAY_NLU_STR"
    echo "BASE_NLU=$BASE_NLU_STR"
    echo "OVERLAY_STORIES=$OVERLAY_STORIES_STR"
    echo "CONFIG=$SELECTED_CONFIG"
    echo "ENDPOINTS=$SELECTED_ENDPOINTS"
    echo "CREDENTIALS=$SELECTED_CREDENTIALS"
    echo -n "PROJECTS="; printf '%s ' "${PROJECTS[@]}"; echo
  } > build/overlay-info.txt
fi

if [[ -n "$DRY_RUN_MODE" ]]; then
  if [[ "$DRY_RUN_MODE" == "stdout" ]]; then
    export OVERLAY_DUMP_DOMAIN=stdout
    export OVERLAY_DUMP_NLU=stdout
    # Show overlay info inline during dry run
    echo "--- Overlay info (dry run) ---"
    echo "BASE_DOMAIN=$BASE_DOMAIN"
    echo "BASE_NLU=$BASE_NLU_STR"
    echo "OVERLAY_DOMAIN=$OVERLAY_DOMAIN_STR"
    echo "OVERLAY_NLU=$OVERLAY_NLU_STR"
    echo "OVERLAY_STORIES=$OVERLAY_STORIES_STR"
    echo "CONFIG=$SELECTED_CONFIG"
    echo "ENDPOINTS=$SELECTED_ENDPOINTS"
    echo "CREDENTIALS=$SELECTED_CREDENTIALS"
    echo -n "PROJECTS="; printf '%s ' "${PROJECTS[@]}"; echo
    echo "------------------------------"
  else
    mkdir -p "$DUMP_DIR"
    export OVERLAY_DUMP_DOMAIN="$DUMP_DIR/merged-domain.yml"
    export OVERLAY_DUMP_NLU="$DUMP_DIR/merged-nlu.yml"
    echo "Dry run: writing merged files to $DUMP_DIR" >&2
    # Also print overlay info for visibility in files mode
    echo "--- Overlay info (dry run) ---"
    echo "BASE_DOMAIN=$BASE_DOMAIN"
    echo "BASE_NLU=$BASE_NLU_STR"
    echo "OVERLAY_DOMAIN=$OVERLAY_DOMAIN_STR"
    echo "OVERLAY_NLU=$OVERLAY_NLU_STR"
    echo "OVERLAY_STORIES=$OVERLAY_STORIES_STR"
    echo "CONFIG=$SELECTED_CONFIG"
    echo "ENDPOINTS=$SELECTED_ENDPOINTS"
    echo "CREDENTIALS=$SELECTED_CREDENTIALS"
    echo -n "PROJECTS="; printf '%s ' "${PROJECTS[@]}"; echo
    echo "------------------------------"
  fi

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

python - <<'PY'
import sys
print('sys.path=', sys.path)
try:
  import src.components.layered_importer as li
  from src.components.layered_importer import OverlayImporter
  print('OverlayImporter import OK:', li.__file__)
except Exception as e:
  print('Failed to import OverlayImporter:', e)
  raise
try:
  import src.components.entity_consolidator as ec
  print('EntityConsolidator import OK:', ec.__file__)
except Exception as e:
  print('Failed to import EntityConsolidator:', e)
  raise
PY

# Use the selected config if available
CONFIG_TO_USE="$SELECTED_CONFIG"
if [[ -z "$CONFIG_TO_USE" ]]; then
  CONFIG_TO_USE="src/core/config.yml"
fi

echo "Training with: domain=$BASE_DOMAIN config=$CONFIG_TO_USE data=$BASE_STORIES ${OVERLAY_STORIES_ARR[*]}"
# Attempt to build a merged layered config (if overlay configs present) using the importer
MERGED_CONFIG_PATH="build/merged-config.yml"
python - <<'PY'
import os, yaml, pathlib
from src.components.layered_importer import OverlayImporter

base_domain = [os.environ.get('OVERLAY_BASE_DOMAIN','')] if os.environ.get('OVERLAY_BASE_DOMAIN') else []
overlay_domain_raw = os.environ.get('OVERLAY_DOMAIN','').strip()
overlay_domain = [p for p in overlay_domain_raw.split(',') if p] if overlay_domain_raw else []
imp = OverlayImporter(base_domain=base_domain, overlay_domain=overlay_domain)
cfg = imp.get_config()
if cfg:
  pathlib.Path('build').mkdir(exist_ok=True)
  out = pathlib.Path('build/merged-config.yml')
  with out.open('w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
  print(f"Layered config merged -> {out}")
else:
  print("No layered config produced (falling back to selected file).")
PY

if [[ -f "$MERGED_CONFIG_PATH" ]]; then
  CONFIG_TO_USE="$MERGED_CONFIG_PATH"
  echo "Using merged layered config: $CONFIG_TO_USE"
fi

rasa train -d "$BASE_DOMAIN" --config "$CONFIG_TO_USE" --data "$BASE_STORIES" ${OVERLAY_STORIES_ARR[@]+"${OVERLAY_STORIES_ARR[@]}"}

if [[ -n "$SELECTED_ENDPOINTS" ]]; then
  echo "Note: At runtime, pass --endpoints $SELECTED_ENDPOINTS to rasa shell/run to enable custom actions."
fi
