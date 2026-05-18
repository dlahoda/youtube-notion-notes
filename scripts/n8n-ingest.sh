#!/usr/bin/env sh

set -u

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
stdout_file=$(mktemp "${TMPDIR:-/tmp}/n8n-ingest-stdout.XXXXXX") || exit 1

cleanup() {
    rm -f "$stdout_file"
}
trap cleanup EXIT HUP INT TERM

cd "$repo_root" || exit 1

python ./ingest.py --input-json-file - --output json > "$stdout_file"
ingest_status=$?

if [ ! -s "$stdout_file" ]; then
    echo "n8n-ingest.sh: ./ingest.py produced no stdout JSON." >&2
    if [ "$ingest_status" -ne 0 ]; then
        exit "$ingest_status"
    fi
    exit 1
fi

if ! python -m json.tool "$stdout_file" > /dev/null; then
    echo "n8n-ingest.sh: ./ingest.py stdout was not valid JSON." >&2
    if [ "$ingest_status" -ne 0 ]; then
        exit "$ingest_status"
    fi
    exit 1
fi

cat "$stdout_file"
exit 0
