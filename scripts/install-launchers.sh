#!/usr/bin/env bash

set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
runner="$repo_root/scripts/ynn-run"
bin_dir="$HOME/.local/bin"

if [[ ! -x "$runner" ]]; then
    echo "install-launchers.sh: expected executable runner at $runner" >&2
    exit 1
fi

mkdir -p "$bin_dir"

install_launcher() {
    local name=$1
    local target="$bin_dir/$name"

    cat > "$target" <<EOF
#!/usr/bin/env sh
exec "$runner" "$name" "\$@"
EOF
    chmod +x "$target"
    echo "Installed $target"
}

install_launcher ynn
install_launcher ynn-note
install_launcher ynn-notion
install_launcher ynn-prompt

case ":$PATH:" in
    *":$bin_dir:"*)
        ;;
    *)
        echo
        echo "Note: $bin_dir is not currently in PATH."
        echo "Add it to your shell profile to run ynn commands from any terminal directory."
        ;;
esac
