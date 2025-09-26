#!/usr/bin/env bash

# Usage:
#   ./scripts/layer_rasa_lang.sh [--dry-run[=stdout|files]] [--dump-dir <dir>] [--no-us-fallback] <lang_spec>
#
# Builds layer paths based on a language[/REGION] spec, mirroring docker-build.yml logic:
#   LAYERS=("src/core" "src/locales/en/US" ["src/locales/$LANG"] ["src/locales/$LANG/$REGION"])
# Then forwards to scripts/layer_rasa_projects.sh with the computed layer list.

set -euo pipefail

DRY=""
DUMP_DIR=""
NO_US_FALLBACK="false"
ARGS_TO_FORWARD=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run|--dry-run=stdout|--dry-run=files)
      DRY="$1"; shift ;;
    --dump-dir)
      DUMP_DIR="$2"; ARGS_TO_FORWARD+=("--dump-dir" "$2"); shift 2 ;;
    --dump-dir=*)
      DUMP_DIR="${1#*=}"; ARGS_TO_FORWARD+=("$1"); shift ;;
    --no-us-fallback)
      NO_US_FALLBACK="true"; shift ;;
    --)
      shift; break ;;
    --*)
      # forward unknown flags
      ARGS_TO_FORWARD+=("$1"); shift ;;
    *)
      break ;;
  esac
done

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [--dry-run[=stdout|files]] [--dump-dir <dir>] [--no-us-fallback] <lang_spec>" >&2
  exit 2
fi

LANG_SPEC="$1"

# Parse lang and optional region
LANG_CODE="$LANG_SPEC"
REGION=""
if [[ "$LANG_SPEC" == */* ]]; then
  REGION="${LANG_SPEC#*/}"
  LANG_CODE="${LANG_SPEC%%/*}"
fi

# Canonicalize: language (lowercase), region (uppercase unless numeric or script Case)
LANG_CODE_CANON="${LANG_CODE,,}"
REGION_CANON=""
if [[ -n "$REGION" ]]; then
  if [[ "$REGION" =~ ^[0-9]+$ ]]; then
    REGION_CANON="$REGION"
  elif [[ ${#REGION} -eq 4 && ${REGION:0:1} =~ [A-Z] && ${REGION:1} =~ [a-z][a-z][a-z] ]]; then
    REGION_CANON="$REGION"  # script code like Hans/Hant
  else
    REGION_CANON="${REGION^^}"
  fi
fi

# Build layer list similar to docker-build.yml
LAYERS=("src/core")
if [[ "$NO_US_FALLBACK" != "true" ]]; then
  LAYERS+=("src/locales/en/US")
fi
if [[ "$LANG_CODE_CANON" != "en" ]]; then
  LAYERS+=("src/locales/$LANG_CODE_CANON")
fi
if [[ -n "$REGION_CANON" ]]; then
  LAYERS+=("src/locales/$LANG_CODE_CANON/$REGION_CANON")
fi

# Keep only existing directories
EXISTING=()
for p in "${LAYERS[@]}"; do
  if [[ -d "$p" ]]; then EXISTING+=("$p"); fi
done

if [[ ${#EXISTING[@]} -eq 0 ]]; then
  echo "No valid layer directories found for spec '$LANG_SPEC' (checked: ${LAYERS[*]})." >&2
  exit 3
fi

echo "Using layers: ${EXISTING[*]}"

# Forward to project-based script
CMD=("bash" "$(dirname "$0")/layer_rasa_projects.sh")
if [[ -n "$DRY" ]]; then CMD+=("$DRY"); fi
CMD+=("${ARGS_TO_FORWARD[@]}")
CMD+=("${EXISTING[@]}")

"${CMD[@]}"
