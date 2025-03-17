#!/usr/bin/env bash
#   Use this script to test if a given TCP host:port are available
#   with an optional timeout, and then execute a command.
#
#   https://github.com/vishnubob/wait-for-it
#
#   Licensed under the MIT License.
#
# Usage:
#   wait-for-it.sh host:port [-t timeout] [-- command args]
#
# Examples:
#   wait-for-it.sh postgres:5432 -t 30 -- echo "Postgres is up"
#

set -e

TIMEOUT=15
STRICT=0
QUIET=0

# Print error messages to stderr
echoerr() { if [ "$QUIET" -ne 1 ]; then echo "$@" 1>&2; fi; }

usage() {
  echoerr "Usage: $0 host:port [-t timeout] [-- command args]"
  exit 1
}

# If no arguments, print usage and exit
if [ $# -lt 1 ]; then
  usage
fi

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    *:* )
      HOST=$(echo "$1" | cut -d':' -f1)
      PORT=$(echo "$1" | cut -d':' -f2)
      shift 1
      ;;
    -t|--timeout)
      TIMEOUT="$2"
      if [ -z "$TIMEOUT" ]; then break; fi
      shift 2
      ;;
    --strict)
      STRICT=1
      shift 1
      ;;
    --quiet)
      QUIET=1
      shift 1
      ;;
    --)
      shift
      break
      ;;
    *)
      echoerr "Unknown argument: $1"
      usage
      ;;
  esac
done

if [ -z "$HOST" ] || [ -z "$PORT" ]; then
  usage
fi

START_TS=$(date +%s)
END_TS=$((START_TS + TIMEOUT))

echoerr "Waiting for $HOST:$PORT (timeout: ${TIMEOUT}s)..."

# Wait for the TCP connection to succeed
while true; do
  if nc -z "$HOST" "$PORT" >/dev/null 2>&1; then
    echoerr "$HOST:$PORT is available"
    break
  fi
  NOW=$(date +%s)
  if [ $NOW -ge $END_TS ]; then
    echoerr "Timeout occurred after waiting ${TIMEOUT} seconds for $HOST:$PORT"
    if [ "$STRICT" -eq 1 ]; then
      exit 1
    fi
    break
  fi
  sleep 1
done

# Execute additional command if provided
if [ $# -gt 0 ]; then
  exec "$@"
fi
