#!/usr/bin/env bash
# scripts/run_local_agent.sh — Sterilized thin invoker for .omarchy/ kernel & batch scheduler.
# Rejects ad-hoc strings; accepts only --batch/--queue or verified .json packet paths.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KERNEL="${REPO_ROOT}/.omarchy/omarchy.py"
BATCH_RUNNER="${REPO_ROOT}/.omarchy/batch_runner.py"
PACKETS_DIR="${REPO_ROOT}/.omarchy/packets"

usage() {
  cat >&2 <<EOF
Usage:
  Single Packet: $(basename "$0") <packet.json> [--keep-warm] [--dry-run]
  Batch Queue:   $(basename "$0") --batch [--strict-fifo] [--dry-run] [packet1.json ...]
                 $(basename "$0") --queue ...   (alias for --batch)

Examples:
  $(basename "$0") _sample_packet.json --dry-run
  $(basename "$0") --batch --dry-run
  $(basename "$0") --batch --dry-run pkt-01-impl.json pkt-02-audit.json pkt-03-optimize.json
EOF
  exit 64
}

if [[ ! -f "${KERNEL}" ]]; then
  echo "[ERROR] Missing kernel: ${KERNEL}" >&2
  exit 1
fi
if [[ ! -f "${BATCH_RUNNER}" ]]; then
  echo "[ERROR] Missing batch runner: ${BATCH_RUNNER}" >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  usage
fi

# Mode 1: Serialized Model-Family Batch Mode (causal waves + finally eviction)
if [[ "$1" == "--batch" || "$1" == "--queue" ]]; then
  shift
  NORMALIZED_ARGS=()
  for arg in "$@"; do
    if [[ "${arg}" == --* ]]; then
      NORMALIZED_ARGS+=("${arg}")
    elif [[ "${arg}" == *.json ]] && [[ ! "${arg}" =~ [[:space:]] ]]; then
      if [[ -f "${PACKETS_DIR}/${arg}" ]]; then
        NORMALIZED_ARGS+=("${PACKETS_DIR}/${arg}")
      elif [[ -f "${arg}" ]]; then
        NORMALIZED_ARGS+=("$(cd "$(dirname "${arg}")" && pwd)/$(basename "${arg}")")
      elif [[ -f "${REPO_ROOT}/${arg}" ]]; then
        NORMALIZED_ARGS+=("${REPO_ROOT}/${arg}")
      else
        echo "[ERROR] Packet file not found: ${arg}" >&2
        exit 66
      fi
    else
      echo "[ERROR] Ad-hoc strings are forbidden in batch mode: '${arg}'" >&2
      usage
    fi
  done
  exec python3 "${BATCH_RUNNER}" "${NORMALIZED_ARGS[@]}"
fi

# Mode 2: Single Sterilized Packet Mode
RAW_PACKET="$1"
shift

if [[ "${RAW_PACKET}" != *.json ]] || [[ "${RAW_PACKET}" =~ [[:space:]] ]]; then
  echo "[ERROR] Ad-hoc strings are forbidden. Provide a valid .json packet file or --batch." >&2
  usage
fi

if [[ -f "${PACKETS_DIR}/${RAW_PACKET}" ]]; then
  PACKET_PATH="${PACKETS_DIR}/${RAW_PACKET}"
elif [[ -f "${RAW_PACKET}" ]]; then
  PACKET_PATH="$(cd "$(dirname "${RAW_PACKET}")" && pwd)/$(basename "${RAW_PACKET}")"
elif [[ -f "${REPO_ROOT}/${RAW_PACKET}" ]]; then
  PACKET_PATH="${REPO_ROOT}/${RAW_PACKET}"
else
  echo "[ERROR] Packet not found: ${RAW_PACKET}" >&2
  exit 66
fi

exec python3 "${KERNEL}" --packet "${PACKET_PATH}" "$@"
